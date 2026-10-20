# =============================================================
#  1. PROVIDER
# =============================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.61.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
    region = var.aws_region
}

# =============================================================
# 2. S3 BUCKET
# =============================================================
resource "aws_s3_bucket" "project_bucket" {
 bucket        = var.s3_bucket_name
  force_destroy = true

  tags = {
    Name = var.s3_bucket_name
  }
}

# =============================================================
# 2. S3 VERSIONING
# =============================================================

resource "aws_s3_bucket_versioning" "my_bucket" {
  bucket = aws_s3_bucket.my_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# =============================================================
# 3. BLOCK PUBLIC ACCESS
# =============================================================
# Block public access for each bucket

resource "aws_s3_bucket_public_access_block" "s3_block" {
  for_each                = aws_s3_bucket.airflow_buckets
  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# =============================================================
# 4. S3 LAMBDA IAM POLICY
# =============================================================

resource "aws_iam_s3_lambda_policy" "s3_role" {
  name = "${var.project_name}-snowflake-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          AWS = var.storage_aws_iam_user_arn
        }

        Action = "sts:AssumeRole"

        Condition = {
          StringEquals = {
            "sts:ExternalId" = var.storage_aws_external_id
          }
        }
      }
    ]
  })

  tags = {
    Name      = "${var.project_name}-snowflake-role"
  }
}


# =============================================================
# 5. SNOWFLAKE → S3 IAM POLICY
# =============================================================


# EC2 Instance Profile to attach the IAM role to the instance
resource "aws_iam_instance_profile" "ec2_s3_profile" {
  name = "airflow-ec2-s3-instance-profile"
  role = aws_iam_role.ec2_s3_role.name
}

# =============================================================
# 6. ATTACH SNOWFLAKE → S3 POLICY
# =============================================================
resource "aws_iam_role_policy_attachment" "snowflake_s3_policy" {
  role       = aws_iam_role.snowflake_role.name
  policy_arn = aws_iam_policy.snowflake_s3_policy.arn
}



