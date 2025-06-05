#!/bin/bash
# Script to deploy the FastAPI Bootstrap infrastructure

set -e

# Usage help function
function usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -e, --environment    Target environment (dev, test, prod)"
  echo "  -h, --help           Display this help message"
  exit 1
}

# Default values
ENVIRONMENT="dev"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -e|--environment)
      ENVIRONMENT="$2"
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

echo "Deploying FastAPI Bootstrap to $ENVIRONMENT environment"

# Initialize Terraform
echo "Initializing Terraform..."
cd terraform/environments/$ENVIRONMENT
terraform init

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

echo "Deployment completed successfully!"
echo "ECR Repository URL: $ECR_REPOSITORY_URL"
echo "ECS Cluster Name: $CLUSTER_NAME"
echo "ALB DNS Name: $ALB_DNS_NAME"
echo "API v1 URL: https://$ALB_DNS_NAME/api/v1"
echo "API v2 URL: https://$ALB_DNS_NAME/api/v2"

# Instructions for first-time setup
echo ""
echo "For first-time setup, you need to:"
echo "1. Push an initial image to the ECR repository:"
echo "   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPOSITORY_URL"
echo "   docker build -t $ECR_REPOSITORY_URL:latest ."
echo "   docker push $ECR_REPOSITORY_URL:latest"
echo ""
echo "2. Set up GitHub repository secrets for CI/CD:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - AWS_REGION"
echo ""
echo "3. Update the AWS account ID in the task definition files:"
echo "   find .aws -name 'task-definition-*.json' -exec sed -i '' 's/ACCOUNT_ID/YOUR_AWS_ACCOUNT_ID/g' {} \;"
echo "   find .aws -name 'appspec-*.yaml' -exec sed -i '' 's/ACCOUNT_ID/YOUR_AWS_ACCOUNT_ID/g' {} \;"
