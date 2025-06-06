#!/bin/bash
# Initialize AWS resources in LocalStack

# Create S3 bucket for Terraform state
echo "Creating S3 bucket for Terraform state..."
awslocal s3 mb s3://terraform-state

# Create DynamoDB table for Terraform state locking
echo "Creating DynamoDB table for Terraform state locking..."
awslocal dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Create KMS key for encryption
echo "Creating KMS key..."
KMS_KEY_ID=$(awslocal kms create-key --description "FastAPI Bootstrap encryption key" --query 'KeyMetadata.KeyId' --output text)
awslocal kms create-alias --alias-name alias/fastapi-bootstrap-dev --target-key-id $KMS_KEY_ID

# Create SSM parameters
echo "Creating SSM parameters..."
awslocal ssm put-parameter \
  --name "/fastapi-bootstrap/dev/database/url" \
  --value "postgresql://postgres:postgres@db:5432/app" \
  --type SecureString \
  --overwrite

awslocal ssm put-parameter \
  --name "/fastapi-bootstrap/dev/api/secret_key" \
  --value "local-development-secret-key" \
  --type SecureString \
  --overwrite

echo "LocalStack initialization complete!"