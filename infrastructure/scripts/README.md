# Deployment and Utility Scripts

This directory contains scripts for deploying, managing, and maintaining the FastAPI Bootstrap infrastructure. These scripts are designed to automate common tasks and provide a consistent approach to infrastructure management.

## Available Scripts

### init.sh

The main interactive setup script that guides you through the initial project setup:

```bash
./init.sh
```

This script:
- Checks for required dependencies (AWS CLI, Terraform, Docker, etc.)
- Validates AWS credentials
- Collects configuration information (organization name, region, environment)
- Sets up the Terraform backend (S3 bucket and DynamoDB table)
- Deploys the infrastructure
- Configures GitHub Actions (optional)

### deploy.sh

Deploys the FastAPI Bootstrap infrastructure to AWS:

```bash
./deploy.sh --environment dev --account-id 123456789012 --region us-east-1 --domain api.example.com
```

**Options:**
- `-e, --environment`: Target environment (dev, test, prod)
- `-a, --account-id`: AWS Account ID
- `-r, --region`: AWS Region (default: us-east-1)
- `-d, --domain`: Domain name for SSL certificate (optional)
- `-h, --help`: Display help message

**Implementation Details:**
- Generates Lambda functions for deployment hooks
- Creates or validates KMS key for encryption
- Creates or validates SSL certificate (if domain provided)
- Updates terraform.tfvars with actual ARNs
- Applies Terraform configuration
- Updates AppSpec files for CodeDeploy

### setup-terraform-backend.sh

Sets up the Terraform backend resources (S3 bucket and DynamoDB table):

```bash
./setup-terraform-backend.sh --org-name acme-corp --region us-east-1
```

**Options:**
- `-o, --org-name`: Organization name (used in S3 bucket name)
- `-r, --region`: AWS Region (default: us-east-1)
- `-h, --help`: Display help message

**Implementation Details:**
- Creates S3 bucket with versioning enabled
- Creates DynamoDB table for state locking
- Updates backend configuration in terraform/main.tf

### update-appspec.sh

Updates AppSpec files with current ARNs and settings:

```bash
./update-appspec.sh --environment dev --account-id 123456789012 --region us-east-1
```

**Options:**
- `-e, --environment`: Target environment (dev, test, prod)
- `-a, --account-id`: AWS Account ID (default: from AWS CLI)
- `-r, --region`: AWS Region (default: us-east-1)
- `-h, --help`: Display help message

**Implementation Details:**
- Reads Terraform outputs for the specified environment
- Updates task definition ARN in AppSpec files
- Updates subnet and security group IDs
- Updates Lambda function ARNs for deployment hooks

### generate-lambda-functions.sh

Generates Lambda function zip files for deployment hooks:

```bash
./generate-lambda-functions.sh
```

**Implementation Details:**
- Creates Python scripts for each deployment hook:
  - `validate-before-install.py`: Validates prerequisites before deployment
  - `validate-deployment.py`: Validates deployment success
  - `validate-test-traffic.py`: Tests the application with synthetic traffic
  - `run-migrations.py`: Executes database migrations
  - `validate-production.py`: Final validation after production traffic is routed
- Packages scripts into zip files
- Places zip files in terraform/modules/lambda/lambda_functions/

## Usage in CI/CD Pipelines

These scripts are designed to be used in CI/CD pipelines, particularly with GitHub Actions:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Deploy infrastructure
        run: |
          ./scripts/deploy.sh --environment dev --account-id ${{ secrets.AWS_ACCOUNT_ID }}
```

## Best Practices

1. **Review Changes**: Always review the changes proposed by Terraform before applying
2. **Use Version Control**: Keep your Terraform state in version-controlled S3 bucket
3. **Test in Dev First**: Always deploy to dev environment before production
4. **Monitor Deployments**: Check CloudWatch Logs after deployment for any issues
5. **Use Meaningful Commit Messages**: Helps with tracking changes through CI/CD

## Troubleshooting

If you encounter issues with the deployment scripts:

1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify Terraform installation: `terraform version`
3. Ensure script permissions: `chmod +x scripts/*.sh`
4. Check CloudWatch Logs for Lambda function errors
5. Review Terraform state: `terraform state list`

This script creates Python zip files for the following Lambda functions:
- validate_before_install (lambda_handler.py)
- validate_deployment (lambda_handler.py)
- validate_test_traffic (lambda_handler.py)
- run_migrations (migrations_handler.py)
- validate_production (lambda_handler.py)