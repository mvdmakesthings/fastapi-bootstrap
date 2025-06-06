# Deployment Guide

This guide provides detailed instructions for deploying the FastAPI Bootstrap application to AWS.

## Prerequisites

Before deploying, ensure you have the following:

- AWS CLI installed and configured with appropriate permissions
- Terraform CLI installed (version 1.0.0 or later)
- Docker installed
- Git repository cloned locally

## Initial Setup

### 1. Initialize the Project

Run the interactive setup script to configure your environment:

```bash
./scripts/init.sh
```

This script will:
- Check for required dependencies
- Validate AWS credentials
- Set up the Terraform backend (S3 bucket and DynamoDB table)
- Create a KMS key for encryption
- Create or use an existing SSL certificate
- Deploy the infrastructure

### 2. Manual Setup (Alternative)

If you prefer to set up manually, follow these steps:

#### a. Set up the Terraform backend

```bash
./scripts/setup-terraform-backend.sh --org-name YOUR-ORGANIZATION-NAME
```

#### b. Deploy the infrastructure

```bash
./scripts/deploy.sh --environment dev --account-id YOUR_AWS_ACCOUNT_ID --region us-east-1 --domain example.com
```

## Deployment Options

### Standard Deployment

The standard deployment uses an Application Load Balancer (ALB) to route traffic to ECS Fargate containers:

1. Edit the environment-specific variables in `terraform/environments/<env>/terraform.tfvars`
2. Run the deployment script:

```bash
./scripts/deploy.sh --environment dev --account-id YOUR_AWS_ACCOUNT_ID
```

### API Gateway Deployment

To use API Gateway instead of direct ALB access:

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