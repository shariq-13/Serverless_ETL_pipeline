import csv
import io
import json
import os
from urllib.parse import unquote_plus

import boto3
import pandas as pd
import snowflake.connector
from snowflake.connector.errors import ProgrammingError
from snowflake.connector.pandas_tools import write_pandas

s3_client = boto3.client("s3")


# ---------------------------------------------------------
# SNOWFLAKE CONFIGURATION (Schema hardcoded to 'GOLD')
# ---------------------------------------------------------
def get_sf_config():
    return {
        "user": os.environ.get("SF_USER"),
        "password": os.environ.get("SF_PASSWORD"),
        "account": os.environ.get("SF_ACCOUNT"),
        "warehouse": os.environ.get("SF_WAREHOUSE"),
        "database": os.environ.get("SF_DATABASE"),
        "schema": "GOLD",  # Hardcoded automatically
        "role": os.environ.get("SF_ROLE", "SYSADMIN"),
    }


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def extract_bucket_and_key(event):
    """Return (bucket, key) from S3 notifications, EventBridge, or flat Step Functions/EventBridge input."""
    if not isinstance(event, dict):
        raise KeyError("event is not a JSON object")

    for wrapper in ("Payload", "input"):
        if isinstance(event.get(wrapper), dict):
            event = event[wrapper]

    if "Records" in event:
        s3 = event["Records"][0]["s3"]
        return s3["bucket"]["name"], unquote_plus(s3["object"]["key"])

    if "detail" in event:
        event = event["detail"]

    if isinstance(event.get("bucket"), dict):
        return event["bucket"]["name"], unquote_plus(event["object"]["key"])

    if "bucket" in event and "key" in event:
        return event["bucket"], unquote_plus(event["key"])

    raise KeyError(f"Could not locate bucket and key in event structure: {event}")


def decode_csv_bytes(raw):
    """UTF-8 (BOM-safe) first, then Latin-1 as a fallback."""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def ensure_schema_exists(conn, database_name, schema_name):
    """Automatically creates the schema if it doesn't exist."""
    cur = conn.cursor()
    try:
        cur.execute(f"USE DATABASE {database_name}")
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        print(f"Ensured schema {database_name}.{schema_name} exists.")
    finally:
        cur.close()


def _delete_existing_gold(cursor, schema, table, source_file):
    """Remove rows from an earlier load of the same file to keep retries idempotent."""
    try:
        cursor.execute(
            f'DELETE FROM {schema}.{table} WHERE "SOURCE_FILE" = %s', (source_file,)
        )
    except ProgrammingError:
        pass  # Table does not exist yet; write_pandas will auto-create it


# ---------------------------------------------------------
# LAMBDA HANDLER (RAW -> SILVER -> GOLD -> SNOWFLAKE)
# ---------------------------------------------------------
def lambda_handler(event, context):
    print("Received event: ", json.dumps(event, default=str))

    try:
        bucket_name, file_key = extract_bucket_and_key(event)
        print(f"Processing bucket: {bucket_name}, file: {file_key}")

        # Validate path pattern (expects files in raw/)
        if not file_key.startswith("raw/") or not file_key.lower().endswith(".csv"):
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "File must be located in 'raw/' and have a '.csv' extension."})
            }

        # ---------------------------------------------------------
        # 1. READ RAW (BRONZE)
        # ---------------------------------------------------------
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        csv_content = decode_csv_bytes(response["Body"].read())
        
        df_raw = pd.read_csv(io.StringIO(csv_content), low_memory=False)
        df_raw = df_raw.dropna(how="all")
        df_raw.columns = [str(c).upper().replace(".", "_") for c in df_raw.columns]

        # ---------------------------------------------------------
        # 2. TRANSFORM & WRITE TO SILVER LAYER
        # ---------------------------------------------------------
        df_silver = df_raw.copy()

        if "ORDER_ID" in df_silver.columns:
            df_silver = df_silver[df_silver["ORDER_ID"].notna() & (df_silver["ORDER_ID"].astype(str).str.strip() != "")]
            df_silver = df_silver.drop_duplicates(subset=["ORDER_ID"])

        if "AMOUNT" in df_silver.columns:
            df_silver["AMOUNT"] = pd.to_numeric(df_silver["AMOUNT"], errors="coerce")
            df_silver = df_silver[df_silver["AMOUNT"] >= 0]

        base = file_key.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        silver_s3_key = f"silver/{base}.json"

        s3_client.put_object(
            Bucket=bucket_name,
            Key=silver_s3_key,
            Body=df_silver.to_json(orient="records", indent=2),
            ContentType="application/json"
        )
        print(f"Successfully wrote Silver data to s3://{bucket_name}/{silver_s3_key}")

        # ---------------------------------------------------------
        # 3. AGGREGATE & WRITE TO GOLD LAYER (S3)
        # ---------------------------------------------------------
        group_col = "CITY" if "CITY" in df_silver.columns else df_silver.columns[0]
        
        df_gold = df_silver.groupby(group_col).agg(
            TOTAL_ORDERS=("ORDER_ID", "count") if "ORDER_ID" in df_silver.columns else (group_col, "count"),
            TOTAL_SALES=("AMOUNT", "sum") if "AMOUNT" in df_silver.columns else (group_col, "count")
        ).reset_index()

        df_gold.rename(columns={group_col: "CATEGORY"}, inplace=True)
        df_gold["TOTAL_SALES"] = df_gold["TOTAL_SALES"].round(2)
        df_gold["SOURCE_FILE"] = file_key

        gold_s3_key = f"gold/{base}_sales.json"

        s3_client.put_object(
            Bucket=bucket_name,
            Key=gold_s3_key,
            Body=df_gold.to_json(orient="records", indent=2),
            ContentType="application/json"
        )
        print(f"Successfully wrote Gold data to s3://{bucket_name}/{gold_s3_key}")

        # ---------------------------------------------------------
        # 4. PICK UP GOLD FILE & INGEST INTO SNOWFLAKE
        # ---------------------------------------------------------
        sf_config = get_sf_config()
        conn = snowflake.connector.connect(**sf_config)
        
        try:
            database_name = sf_config["database"]
            schema_name = sf_config["schema"]
            
            ensure_schema_exists(conn, database_name, schema_name)
            cursor = conn.cursor()

            print(f"Ingesting Gold dataset into {schema_name}.SALES_GOLD_SUMMARY...")
            _delete_existing_gold(cursor, schema_name, "SALES_GOLD_SUMMARY", file_key)
            
            write_pandas(
                conn=conn, df=df_gold, table_name="SALES_GOLD_SUMMARY",
                database=database_name, schema=schema_name,
                auto_create_table=True, overwrite=False
            )
            cursor.close()

        finally:
            conn.close()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Pipeline execution successful: Raw -> Silver -> Gold (S3) -> Snowflake Gold Table!",
                "bucket": bucket_name,
                "silver_key": silver_s3_key,
                "gold_key": gold_s3_key,
                "gold_rows_ingested": len(df_gold),
            }),
        }

    except Exception as e:
        print(f"Error in Medallion pipeline execution: {e}")
        raise e