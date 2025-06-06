#!/bin/bash
# Script to deploy the FastAPI Bootstrap infrastructure

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Usage help function
function usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -e, --environment    Target environment (dev, test, prod)"
  echo "  -a, --account-id     AWS Account ID"
  echo "  -r, --region         AWS Region (default: us-east-1)"
  echo "  -d, --domain         Domain name for SSL certificate (optional)"
  echo "  -h, --help           Display this help message"
  exit 1
}

# Default values
ENVIRONMENT="dev"
AWS_ACCOUNT_ID=""
AWS_REGION="us-east-1"
DOMAIN_NAME=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -e|--environment)
      ENVIRONMENT="$2"
      shift
      shift
      ;;
    -a|--account-id)
      AWS_ACCOUNT_ID="$2"
      shift
      shift
      ;;
    -r|--region)
      AWS_REGION="$2"
      shift
      shift
      ;;
    -d|--domain)
      DOMAIN_NAME="$2"
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

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod)$ ]]; then
  echo "Error: Environment must be one of: dev, test, prod"
  exit 1
fi

# Validate AWS Account ID
if [[ -z "$AWS_ACCOUNT_ID" ]]; then
  echo "Error: AWS Account ID is required"
  echo "Please provide your AWS Account ID using the -a or --account-id option"
  exit 1
fi

echo "Deploying FastAPI Bootstrap to $ENVIRONMENT environment"

# Generate Lambda function zip files
echo "Generating Lambda function zip files..."
"$SCRIPT_DIR/generate-lambda-functions.sh"

# Create KMS key if it doesn't exist
echo "Creating or retrieving KMS key..."
KMS_KEY_ID=$(aws kms describe-key --key-id alias/fastapi-bootstrap-${ENVIRONMENT} --query 'KeyMetadata.KeyId' --output text 2>/dev/null || echo "")

if [[ -z "$KMS_KEY_ID" ]]; then
  echo "Creating new KMS key for $ENVIRONMENT environment..."
  KMS_KEY_ID=$(aws kms create-key --description "FastAPI Bootstrap ${ENVIRONMENT} encryption key" --query 'KeyMetadata.KeyId' --output text)
  aws kms create-alias --alias-name alias/fastapi-bootstrap-${ENVIRONMENT} --target-key-id $KMS_KEY_ID
  echo "Created KMS key: $KMS_KEY_ID"
else
  echo "Using existing KMS key: $KMS_KEY_ID"
fi

KMS_KEY_ARN="arn:aws:kms:${AWS_REGION}:${AWS_ACCOUNT_ID}:key/${KMS_KEY_ID}"

# Create or retrieve SSL certificate
CERTIFICATE_ARN=""
if [[ -n "$DOMAIN_NAME" ]]; then
  echo "Creating or retrieving SSL certificate for $DOMAIN_NAME..."
  CERTIFICATE_ARN=$(aws acm list-certificates --query "CertificateSummaryList[?DomainName=='$DOMAIN_NAME'].CertificateArn" --output text)
  
  if [[ -z "$CERTIFICATE_ARN" ]]; then
    echo "Creating new SSL certificate for $DOMAIN_NAME..."
    CERTIFICATE_ARN=$(aws acm request-certificate --domain-name $DOMAIN_NAME --validation-method DNS --query 'CertificateArn' --output text)
    echo "Created certificate: $CERTIFICATE_ARN"
    echo "IMPORTANT: You must validate the certificate by adding the required DNS records."
    echo "Check the AWS console for validation details."
  else
    echo "Using existing certificate: $CERTIFICATE_ARN"
  fi
else
  echo "No domain provided. Using a self-signed certificate..."
  CERTIFICATE_ARN=$(aws acm list-certificates --query "CertificateSummaryList[?DomainName=='fastapi-bootstrap-${ENVIRONMENT}.local'].CertificateArn" --output text)
  
  if [[ -z "$CERTIFICATE_ARN" ]]; then
    # Create a self-signed certificate
    echo "Creating self-signed certificate..."
    CERTIFICATE_ARN=$(aws acm import-certificate --certificate fileb://<(openssl req -x509 -newkey rsa:2048 -nodes -keyout /dev/stdout -out /dev/stdout -days 365 -subj "/CN=fastapi-bootstrap-${ENVIRONMENT}.local" | tee >(cat 1>&2)) --query 'CertificateArn' --output text)
    echo "Created self-signed certificate: $CERTIFICATE_ARN"
  else
    echo "Using existing self-signed certificate: $CERTIFICATE_ARN"
  fi
fi

# Update terraform.tfvars with actual KMS key and certificate ARNs
echo "Updating terraform.tfvars with actual ARNs..."
sed -i '' "s|kms_key_id = \".*\"|kms_key_id = \"$KMS_KEY_ARN\"|" "$PROJECT_ROOT/terraform/environments/${ENVIRONMENT}/terraform.tfvars"
sed -i '' "s|certificate_arn = \".*\"|certificate_arn = \"$CERTIFICATE_ARN\"|" "$PROJECT_ROOT/terraform/environments/${ENVIRONMENT}/terraform.tfvars"

# Generate a random deployment ID for task definition
DEPLOYMENT_ID=$(date +%s)
echo "Generated deployment ID: $DEPLOYMENT_ID"

# Update AWS Account ID and deployment ID in task definition files
echo "Updating configuration files..."
find "$PROJECT_ROOT/.aws" -name "task-definition-*-${ENVIRONMENT}.json" -exec sed -i '' "s/ACCOUNT_ID/$AWS_ACCOUNT_ID/g" {} \;
find "$PROJECT_ROOT/.aws" -name "task-definition-*-${ENVIRONMENT}.json" -exec sed -i '' "s/DEPLOYMENT_ID_PLACEHOLDER/$DEPLOYMENT_ID/g" {} \;

# Update subnet and security group placeholders in appspec files
echo "Updating network configuration in appspec files..."
cd "$PROJECT_ROOT/terraform/environments/$ENVIRONMENT"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Get VPC information
echo "Retrieving VPC information..."
PRIVATE_SUBNETS=$(terraform output -json private_subnets | jq -r 'join("\",\"")')
SECURITY_GROUP=$(terraform output -raw ecs_security_group_id)

# Update appspec files with actual subnet and security group IDs
cd "$PROJECT_ROOT"
find .aws -name "appspec-*-${ENVIRONMENT}.yaml" -exec sed -i '' "s/<SUBNET_1>\",\"<SUBNET_2>/$PRIVATE_SUBNETS/g" {} \;
find .aws -name "appspec-*-${ENVIRONMENT}.yaml" -exec sed -i '' "s/<SECURITY_GROUP>/$SECURITY_GROUP/g" {} \;

# Return to Terraform directory
cd "$PROJECT_ROOT/terraform/environments/$ENVIRONMENT"

# Plan Terraform changes
echo "Planning Terraform changes..."
terraform plan -out=tfplan

# Apply Terraform changes
echo "Applying Terraform changes..."
terraform apply tfplan

# Extract required outputs
echo "Extracting deployment information..."
ECR_REPOSITORY_URL=$(terraform output -raw ecr_repository_url)
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
ALB_DNS_NAME=$(terraform output -raw alb_dns_name)

# Update appspec files with Lambda ARNs
echo "Updating appspec files with Lambda ARNs..."
"$SCRIPT_DIR/update-appspec.sh" -e ${ENVIRONMENT}

echo "Deployment completed successfully!"
echo "ECR Repository URL: $ECR_REPOSITORY_URL"
echo "ECS Cluster Name: $CLUSTER_NAME"
echo "ALB DNS Name: $ALB_DNS_NAME"
echo "API v1 URL: https://$ALB_DNS_NAME/api/v1"

# Instructions for first-time setup
echo ""
echo "For first-time setup, you need to:"
echo "1. Push an initial image to the ECR repository:"
echo "   aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URL"
echo "   docker build -t $ECR_REPOSITORY_URL:latest ."
echo "   docker push $ECR_REPOSITORY_URL:latest"
echo ""
echo "2. Set up GitHub repository secrets for CI/CD:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - AWS_REGION"
echo "   - AWS_ACCOUNT_ID"
