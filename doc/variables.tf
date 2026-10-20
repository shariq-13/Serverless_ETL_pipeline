
{ "bucket": { "name": "serverless-etl-s3" }, "object": { "key": "AdventureWorks_Customers.csv" } }

{
  "source": ["custom.etl.source"],
  "detail-type": ["ETLTriggerEvent"]
}
{
    "bucket": "serverless-etl-s3",
    "key": "raw/AdventureWorks_Customers.csv"
            
}
Invalid Action: The action logs:DescribeLogDeliveries does not exist. Learn more 
KeyError encountered: 'key'

KeyError encountered: 'key'
2026-10-20T13:05:39.264Z
[ERROR] ValueError: Missing expected key in payload: 'key'. Send 
{
    "bucket": "<bucket>",
    "key": "<file path>"

AWSLambdaRole
AWS managed
2 plicies atahed in step function


{
  "source": ["custom.etl.source"],
  "detail-type": ["ETLTriggerEvent"]
}


{
  "bucket": {
    "name": "serverless-etl-s3"
  },
  "object": {
    "key": "AdventureWorks_Customers.csv"
  }
}
{'bucket': {'name': 'serverless-etl-s3'}, 'object': {'key': 'AdventureWorks_Customers.csv'}}
{ "bucket": { "name": "serverless-etl-s3" }, "object": { "key": "AdventureWorks_Customers.csv" } }

{
  "bucket": "your-real-bucket-name",
  "key": "orders_data.csv"
}
# -------------------------------------------------------------
# 1. CONFIGURE AWS 
# -------------------------------------------------------------
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# -------------------------------------------------------------
# 2. S3 PROJECT NAME 
# -------------------------------------------------------------

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "serverless_etl_pipeline"
}

# -------------------------------------------------------------
# 3. S3 BUCKET NAME 
# -------------------------------------------------------------
variable "s3_bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
  default     = "serverless_etl_s3"
  
}

# -------------------------------------------------------------
# 4. S3 LAMBDA IAM POLICY
# -------------------------------------------------------------
variable "aws_iam_s3_lambda_policy" {
  description = "Role name"
  type        = string
  default     = "serverless_etl_s3_lambda_policy" 
}

# -------------------------------------------------------------
# 5. EVENTBRIDGE NAME
# -------------------------------------------------------------
variable "aws_eventbridge" {
  description = "Role name"
  type        = string
  default     = "serverless_etl_eventbridge" 
}

# -------------------------------------------------------------
# 6. STEP FUNCTION NAME
# -------------------------------------------------------------
variable "aws_stepfunction" {
  description = "Role name"
  type        = string
  default     = "serverless_etl_stepfunction" 
}

# -------------------------------------------------------------
# 7. LAMBDA IAM ROLE
# -------------------------------------------------------------
variable "aws_iam_role_lambda" {
  description = "Role name"
  type        = string
  default     = "serverless_etl_lambda_role" 
}

# -------------------------------------------------------------
# 8. SQS NAME
# -------------------------------------------------------------
variable "aws_sqs" {
  description = "Role name"
  type        = string
  default     = "serverless_etl_sqs" 
}

# -------------------------------------------------------------
# 9. SNS NAME
# -------------------------------------------------------------
variable "aws_sns" {
  description = "Role name"
  type        = string
  default     = "serverless_etl_sns" 
}



