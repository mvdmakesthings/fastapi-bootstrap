# AWS CDK Infrastructure

This document describes the AWS CDK infrastructure used in the FastAPI Bootstrap project.

## Overview

The FastAPI Bootstrap project uses AWS CDK (Cloud Development Kit) to define and deploy AWS infrastructure as code. The infrastructure is organized into several stacks:

1. **API Stack** - Contains the API infrastructure including ECS Fargate service, load balancer, and VPC
2. **Database Stack** - Contains the RDS PostgreSQL database
3. **Monitoring Stack** - Contains CloudWatch dashboards and alarms

## Prerequisites

Before deploying the infrastructure, you need to:

1. Install the AWS CDK CLI:
   ```
   npm install -g aws-cdk
   ```

2. Initialize the project with required AWS resources:
   ```
   fastapi-bootstrap init project --org-name <your-org-name> --aws-profile <your-aws-profile> --aws-region <your-aws-region> --environment <dev|test|prod>
   ```

3. Bootstrap the AWS CDK environment:
   ```
   fastapi-bootstrap infra bootstrap --aws-profile <your-aws-profile> --aws-region <your-aws-region>
   ```

## Infrastructure Stacks

### API Stack (`api_stack.py`)

The API Stack creates the following resources:

- **VPC** - A Virtual Private Cloud with public and private subnets
- **ECS Cluster** - An Amazon ECS cluster for running the API containers
- **ECS Fargate Service** - A Fargate service for running the API containers
- **Application Load Balancer** - A load balancer for distributing traffic to the API containers
- **Security Groups** - Security groups for controlling inbound and outbound traffic
- **IAM Roles** - IAM roles for the ECS task execution and ECS tasks
- **ECR Repository** - A container registry for storing API container images

The API Stack also exports the VPC to be used by other stacks.

### Database Stack (`database_stack.py`)

The Database Stack creates the following resources:

- **RDS Instance** - A PostgreSQL database instance
- **Database Security Group** - A security group for controlling access to the database
- **Database Subnet Group** - A subnet group for the database instance
- **Database Parameter Group** - A parameter group for configuring the database
- **Secret** - A Secrets Manager secret for storing database credentials

The Database Stack depends on the VPC created in the API Stack.

### Monitoring Stack (`monitoring_stack.py`)

The Monitoring Stack creates the following resources:

- **CloudWatch Dashboard** - A dashboard for monitoring the API and database
- **CloudWatch Alarms** - Alarms for critical metrics
- **SNS Topic** - A topic for sending alarm notifications
- **Log Groups** - Log groups for storing API logs

The Monitoring Stack depends on resources from both the API and Database Stacks.

## Deployment

To deploy the infrastructure:

```
fastapi-bootstrap infra deploy --env <dev|test|prod> --aws-profile <your-aws-profile> --aws-region <your-aws-region>
```

This command will synthesize the CloudFormation templates from the CDK code and deploy them to your AWS account.

## Configuration

The infrastructure stacks are configured based on the following:

1. **Environment** - The environment name (`dev`, `test`, or `prod`)
2. **Organization Name** - The organization name used for resource naming
3. **AWS Account ID** - The AWS account ID
4. **AWS Region** - The AWS region

These configurations are stored in the config file (`~/.fastapi-bootstrap/config.yaml`) after running the `init project` command.

## Resource Naming

Resources are named using the following pattern:

```
<org-name>-<environment>-<resource-type>
```

For example:
- `myorg-dev-api-service`
- `myorg-dev-database`
- `myorg-dev-monitoring-dashboard`

## Security Considerations

The infrastructure is designed with security in mind:

1. **Network Segmentation** - The API runs in private subnets and communicates with the internet through a NAT gateway
2. **Least Privilege** - IAM roles follow the principle of least privilege
3. **Encryption** - Data is encrypted at rest and in transit
4. **Security Groups** - Security groups restrict traffic to only what is necessary

## Cost Optimization

To optimize costs:

1. **Fargate Spot** - Consider using Fargate Spot for non-production environments
2. **Auto Scaling** - The API service scales based on demand
3. **RDS Instance Sizing** - Choose appropriate instance sizes for your database based on your needs
4. **Reserved Instances** - Consider purchasing reserved instances for production environments

## Customization

You can customize the infrastructure by modifying the stack files:

- `/src/fastapi_bootstrap/infrastructure/stacks/api_stack.py`
- `/src/fastapi_bootstrap/infrastructure/stacks/database_stack.py`
- `/src/fastapi_bootstrap/infrastructure/stacks/monitoring_stack.py`

Additionally, you can modify the constants in `/src/fastapi_bootstrap/infrastructure/constants.py` to adjust resource settings.

## Cleanup

To destroy the infrastructure:

```
fastapi-bootstrap infra destroy --env <dev|test|prod> --aws-profile <your-aws-profile> --aws-region <your-aws-region> --force
```

**Note:** This will permanently delete all resources. Use with caution.
