# Deployment Scripts

This directory contains scripts for deploying and managing the FastAPI Bootstrap infrastructure.

## Scripts

### deploy.sh

Deploys the FastAPI Bootstrap infrastructure to AWS.

```bash
./deploy.sh --environment dev --account-id YOUR_AWS_ACCOUNT_ID --region us-east-1 --domain example.com
```

Options:
- `-e, --environment`: Target environment (dev, test, prod)
- `-a, --account-id`: AWS Account ID
- `-r, --region`: AWS Region (default: us-east-1)
- `-d, --domain`: Domain name for SSL certificate (optional)

### setup-terraform-backend.sh

Sets up the Terraform backend resources (S3 bucket and DynamoDB table).

```bash
./setup-terraform-backend.sh --org-name YOUR-ORGANIZATION-NAME
```

Options:
- `-o, --org-name`: Organization name (used in S3 bucket name)
- `-r, --region`: AWS Region (default: us-east-1)

### update-appspec.sh

Updates appspec files with Lambda ARNs from Terraform outputs.

```bash
./update-appspec.sh --environment dev
```

Options:
- `-e, --environment`: Target environment (dev, test, prod)

### generate-lambda-functions.sh

Generates Lambda function zip files for deployment hooks.

```bash
./generate-lambda-functions.sh
```

This script creates Python zip files for the following Lambda functions:
- validate_before_install (lambda_handler.py)
- validate_deployment (lambda_handler.py)
- validate_test_traffic (lambda_handler.py)
- run_migrations (migrations_handler.py)
- validate_production (lambda_handler.py)