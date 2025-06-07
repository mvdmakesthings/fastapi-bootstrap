# Deployment Guide

This comprehensive guide provides detailed instructions for deploying the FastAPI Bootstrap application to AWS, designed for Solutions Architects, DevOps Engineers, and Software Engineers responsible for infrastructure management and application deployment.

## Overview

The FastAPI Bootstrap project uses a fully automated deployment pipeline that leverages:

- **Terraform** for infrastructure provisioning
- **AWS CodeDeploy** for blue/green deployments
- **GitHub Actions** for CI/CD pipeline (optional)
- **Docker** for containerization

This guide covers both the initial setup process and ongoing deployments.

## Prerequisites

Before deploying, ensure you have the following:

- **AWS CLI** installed and configured with appropriate permissions
- **Terraform CLI** installed (version 1.0.0 or later)
- **Docker** installed and configured
- **Git** repository cloned locally
- **AWS Account** with appropriate permissions:
  - IAM role creation
  - ECS/ECR access
  - S3 bucket creation
  - DynamoDB table creation
  - KMS key management
  - CloudWatch access
  - CodeDeploy deployment

## Initial Setup

### Interactive Setup (Recommended)

For a guided setup experience, run the interactive initialization script:

```bash
./scripts/init.sh
```

The `init.sh` script provides a step-by-step interactive setup process:

1. **Checks dependencies**: Verifies that all required tools are installed
2. **Validates AWS credentials**: Ensures you have valid AWS credentials configured
3. **Collects configuration information**:
   - Organization name (for resource naming)
   - AWS region
   - Environment (dev/test/prod)
   - Domain name (optional, for SSL certificate)
4. **Sets up Terraform backend**:
   - Creates S3 bucket for state storage
   - Creates DynamoDB table for state locking
5. **Deploys infrastructure**: Provisions all required AWS resources
6. **Configures GitHub Actions** (optional): Sets up repository secrets for CI/CD

Here's a snippet of the interactive script showing the configuration process:

```bash
# Check for required tools
echo "Checking for required tools..."
for tool in aws terraform docker jq curl; do
  if ! command -v $tool &> /dev/null; then
    echo "Error: $tool is not installed. Please install it and try again."
    exit 1
  fi
done

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
  echo "Error: AWS credentials not configured or invalid."
  echo "Please run 'aws configure' to set up your AWS credentials."
  exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get organization name
read -p "Enter your organization name (used for S3 bucket naming): " ORG_NAME
while [[ -z "$ORG_NAME" ]]; do
  echo "Organization name cannot be empty."
  read -p "Enter your organization name: " ORG_NAME
done
ORG_NAME=$(echo "$ORG_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

# Get AWS region
DEFAULT_REGION="us-east-1"
read -p "Enter AWS region [$DEFAULT_REGION]: " AWS_REGION
AWS_REGION=${AWS_REGION:-$DEFAULT_REGION}

# Get environment
DEFAULT_ENV="dev"
read -p "Enter deployment environment (dev/test/prod) [$DEFAULT_ENV]: " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-$DEFAULT_ENV}
```

### Manual Setup (Alternative)

If you prefer to set up manually or need to customize the process, follow these steps:

#### a. Set up the Terraform backend

```bash
./scripts/setup-terraform-backend.sh --org-name YOUR-ORGANIZATION-NAME --region us-east-1
```

This script:
- Creates an S3 bucket for Terraform state storage with versioning enabled
- Creates a DynamoDB table for state locking
- Updates the Terraform backend configuration in `terraform/main.tf`

#### b. Deploy the infrastructure

```bash
./scripts/deploy.sh --environment dev --account-id YOUR_AWS_ACCOUNT_ID --region us-east-1 --domain example.com
```

The `deploy.sh` script handles the entire deployment process with the following parameters:

- `--environment` or `-e`: Target environment (dev, test, prod)
- `--account-id` or `-a`: AWS Account ID
- `--region` or `-r`: AWS Region (default: us-east-1)
- `--domain` or `-d`: Domain name for SSL certificate (optional)
- `--help` or `-h`: Display help message

Here's a snippet showing how the script works:

```bash
#!/bin/bash
# Script to deploy the FastAPI Bootstrap infrastructure

set -e

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
    # ... other parameters ...
  esac
done

# Main deployment steps
echo "Deploying to $ENVIRONMENT environment in $AWS_REGION..."

# 1. Generate Lambda functions for deployment hooks
# 2. Create/validate KMS key for encryption
# 3. Create/validate SSL certificate
# 4. Update terraform.tfvars with actual ARNs
# 5. Apply Terraform configuration
# 6. Update AppSpec files for CodeDeploy
```

The script performs the following steps:

1. **Validates inputs and requirements**
2. **Generates Lambda functions** for deployment hooks
3. **Creates or uses existing KMS key** for encryption
4. **Creates or validates SSL certificate** (if domain is provided)
5. **Updates Terraform variables** with actual ARNs
6. **Applies Terraform configuration**
7. **Updates AppSpec files** for CodeDeploy

## Helper Scripts

The FastAPI Bootstrap project includes several helper scripts to simplify common tasks. These scripts are located in the `scripts/` directory:

### Deployment Scripts

#### 1. `deploy.sh`

Handles the entire deployment process:

```bash
# Deploy to development environment
./scripts/deploy.sh --environment dev --account-id 123456789012 --region us-east-1

# Deploy to production with custom domain
./scripts/deploy.sh --environment prod --account-id 123456789012 --region us-east-1 --domain api.example.com
```

Key features:
- Generates Lambda functions for deployment hooks
- Creates or validates KMS key for encryption
- Sets up SSL certificate (if domain is provided)
- Updates Terraform variables with actual ARNs
- Applies Terraform configuration
- Updates AppSpec files for CodeDeploy

#### 2. `setup-terraform-backend.sh`

Creates the S3 bucket and DynamoDB table for Terraform state management:

```bash
./scripts/setup-terraform-backend.sh --org-name your-organization --region us-east-1
```

Key features:
- Creates S3 bucket with versioning enabled
- Creates DynamoDB table for state locking
- Updates Terraform backend configuration

#### 3. `generate-lambda-functions.sh`

Creates Lambda function zip packages for deployment hooks:

```bash
./scripts/generate-lambda-functions.sh
```

Key features:
- Generates Python scripts for each deployment hook
- Packages scripts into zip files
- Places zip files in the correct location for Terraform

#### 4. `update-appspec.sh`

Updates the AppSpec files with current ARNs and settings:

```bash
./scripts/update-appspec.sh --environment dev --account-id 123456789012 --region us-east-1
```

Key features:
- Updates task definition ARN
- Updates subnet and security group IDs
- Updates Lambda function ARNs for hooks

### Continuous Deployment with GitHub Actions

For automated deployments, the project includes GitHub Actions workflows in `.github/workflows/`:

1. **CI/CD Pipeline** (`.github/workflows/deploy.yml`):
   - Triggered on push to main (production) or develop (development) branches
   - Runs tests, builds Docker image, and deploys to the appropriate environment

2. **Pull Request Validation** (`.github/workflows/pr.yml`):
   - Triggered on pull requests
   - Runs tests and validates code quality
   - Does not deploy to any environment

To set up GitHub Actions:

1. Add the following secrets to your GitHub repository:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `AWS_ACCOUNT_ID`

2. Push to the appropriate branch to trigger deployment:
   - `develop` branch → development environment
   - `main` branch → production environment

1. Edit the environment-specific variables in `terraform/environments/<env>/terraform.tfvars`:

```hcl
api_gateway_enabled = true
custom_domain_name = "api.example.com"  # Optional
```

2. Run the deployment script as usual

### Database Deployment

To include a managed RDS database:

1. Edit the environment-specific variables in `terraform/environments/<env>/terraform.tfvars`:

```hcl
db_enabled = true
db_instance_class = "db.t3.micro"
db_allocated_storage = 20
db_engine = "postgres"
db_engine_version = "13.7"
db_name = "app"
db_username = "postgres"
db_password = "your-secure-password"
```

2. Run the deployment script as usual

## CI/CD Pipeline

### GitHub Actions Setup

1. Add the following secrets to your GitHub repository:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `AWS_ACCOUNT_ID`

2. Push to the appropriate branch:
   - `develop` branch deploys to the `dev` environment
   - `main` branch deploys to the `prod` environment

### Manual Deployment Trigger

You can manually trigger a deployment to any environment:

1. Go to the "Actions" tab in your GitHub repository
2. Select the "Deploy FastAPI to AWS Fargate" workflow
3. Click "Run workflow"
4. Select the branch and environment
5. Click "Run workflow"

## Post-Deployment Steps

### 1. Verify Deployment

Check that the application is running:

```bash
curl https://<alb_dns_name>/api/v1
```

### 2. Monitor the Application

1. Access the CloudWatch dashboard:
   - Go to the AWS Console
   - Navigate to CloudWatch > Dashboards
   - Select the dashboard named `fastapi-bootstrap-<environment>`

2. Check the logs:
   - Go to CloudWatch > Log Groups
   - Select `/ecs/fastapi-bootstrap-<environment>`

### 3. Run Database Migrations

If using a database, run migrations:

```bash
# Set environment variables
export DB_URL=$(aws ssm get-parameter --name "/fastapi-bootstrap/dev/database/url" --with-decryption --query "Parameter.Value" --output text)

# Run migrations
poetry run alembic upgrade head
```

## Environment-Specific Configurations

### Development Environment

```hcl
environment = "dev"
task_cpu = 256
task_memory = 512
min_capacity = 1
max_capacity = 1
db_instance_class = "db.t3.micro"
db_multi_az = false
```

### Production Environment

```hcl
environment = "prod"
task_cpu = 1024
task_memory = 2048
min_capacity = 2
max_capacity = 10
db_instance_class = "db.t3.medium"
db_multi_az = true
db_deletion_protection = true
```

## Troubleshooting

### Common Issues

1. **Deployment Failure**:
   - Check CloudWatch Logs for ECS service
   - Verify task definition is correct
   - Check CodeDeploy events

2. **Database Connection Issues**:
   - Verify security group rules
   - Check database credentials in SSM Parameter Store
   - Ensure ECS task has proper IAM permissions

3. **SSL Certificate Validation**:
   - Ensure DNS records are properly configured for domain validation
   - Wait for certificate validation to complete (can take up to 30 minutes)

### Rollback Procedure

If you need to rollback to a previous version:

1. Find the previous task definition revision:
   ```bash
   aws ecs list-task-definitions --family-prefix fastapi-bootstrap-v1-dev
   ```

2. Update the service to use the previous task definition:
   ```bash
   aws ecs update-service --cluster fastapi-bootstrap-dev --service fastapi-bootstrap-v1-dev --task-definition fastapi-bootstrap-v1-dev:X
   ```

## Cleanup

To destroy the infrastructure when no longer needed:

```bash
cd terraform/environments/<environment>
terraform destroy
```

**Warning**: This will delete all resources including databases. Make sure to backup any important data before proceeding.