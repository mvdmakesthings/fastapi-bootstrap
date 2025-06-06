#!/bin/bash
# Script to set up Terraform backend resources (S3 bucket and DynamoDB table)

set -e

# Usage help function
function usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -o, --org-name       Organization name (used in S3 bucket name)"
  echo "  -r, --region         AWS Region (default: us-east-1)"
  echo "  -h, --help           Display this help message"
  exit 1
}

# Default values
AWS_REGION="us-east-1"
ORG_NAME=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -o|--org-name)
      ORG_NAME="$2"
      shift
      shift
      ;;
    -r|--region)
      AWS_REGION="$2"
      shift
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

# Validate organization name
if [[ -z "$ORG_NAME" ]]; then
  echo "Error: Organization name is required"
  echo "Please provide your organization name using the -o or --org-name option"
  exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [[ -z "$AWS_ACCOUNT_ID" ]]; then
  echo "Error: Failed to get AWS account ID"
  echo "Please ensure you have AWS CLI configured correctly"
  exit 1
fi

# Create S3 bucket for Terraform state
BUCKET_NAME="${ORG_NAME}-terraform-state-${AWS_ACCOUNT_ID}"
echo "Creating S3 bucket: $BUCKET_NAME"
aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION

# Enable versioning on the bucket
echo "Enabling versioning on the bucket"
aws s3api put-bucket-versioning --bucket $BUCKET_NAME --versioning-configuration Status=Enabled

# Enable encryption on the bucket
echo "Enabling encryption on the bucket"
aws s3api put-bucket-encryption --bucket $BUCKET_NAME --server-side-encryption-configuration '{
  "Rules": [
    {
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }
  ]
}'

# Create DynamoDB table for state locking
TABLE_NAME="terraform-locks"
echo "Creating DynamoDB table: $TABLE_NAME"
aws dynamodb create-table \
  --table-name $TABLE_NAME \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION

# Update Terraform backend configuration
echo "Updating Terraform backend configuration"
sed -i '' "s/bucket         = \".*\"/bucket         = \"$BUCKET_NAME\"/" terraform/main.tf
sed -i '' "s/region         = \".*\"/region         = \"$AWS_REGION\"/" terraform/main.tf

echo "Terraform backend setup completed successfully"
echo "S3 Bucket: $BUCKET_NAME"
echo "DynamoDB Table: $TABLE_NAME"
echo "AWS Region: $AWS_REGION"