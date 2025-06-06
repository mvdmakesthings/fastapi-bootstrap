# Lambda Module

This module creates Lambda functions for CodeDeploy hooks used in the blue/green deployment process for the FastAPI Bootstrap project.

## Overview

The Lambda module provisions AWS Lambda functions that serve as deployment hooks in the CodeDeploy blue/green deployment process. These functions perform critical validation checks and operations during different stages of the deployment lifecycle.

## Function Details

### 1. Validate Before Install (`validate_before_install`)

**Purpose**: Validates prerequisites before beginning deployment.
**Execution Timing**: Before the new task set is created.
**Key Operations**:
- Verifies required AWS resources exist
- Checks service health
- Validates task definition
- Verifies infrastructure configuration

**Implementation**:
```python
def handler(event, context):
    # Validate ECS service exists
    ecs_client = boto3.client('ecs')
    try:
        ecs_client.describe_services(
            cluster=os.environ['ECS_CLUSTER'],
            services=[os.environ['ECS_SERVICE']]
        )
    except Exception as e:
        return {
            'status': 'FAILED',
            'message': f'ECS service validation failed: {str(e)}'
        }

    # Other validation logic...

    return {
        'status': 'SUCCEEDED',
        'message': 'All pre-deployment checks passed successfully'
    }
```

### 2. Validate Deployment (`validate_deployment`)

**Purpose**: Validates the deployment was successful after installation.
**Execution Timing**: After the new task set is created.
**Key Operations**:
- Confirms new tasks are running
- Verifies service health checks
- Checks container status
- Validates expected task count

### 3. Validate Test Traffic (`validate_test_traffic`)

**Purpose**: Validates the application with test traffic.
**Execution Timing**: After test traffic is routed to the new deployment.
**Key Operations**:
- Performs smoke tests on critical endpoints
- Validates HTTP responses
- Checks error rates
- Monitors response times

### 4. Run Migrations (`run_migrations`)

**Purpose**: Executes database migrations before full production traffic is routed.
**Execution Timing**: Before production traffic is routed to the new deployment.
**Key Operations**:
- Runs database migration scripts
- Validates schema changes
- Performs data verification
- Implements rollback capability if needed

### 5. Validate Production (`validate_production`)

**Purpose**: Final validation after production traffic is routed.
**Execution Timing**: After production traffic is routed to the new deployment.
**Key Operations**:
- Monitors application metrics
- Verifies performance under load
- Validates business functionality
- Confirms CloudWatch alarms are in expected state

## Implementation Notes

- All Lambda functions are configured with a 15-minute timeout
- Functions use Python 3.9 runtime
- Each function has appropriate IAM permissions via role policies
- Environment variables provide context about the deployment
- CloudWatch Logs capture function execution details

## Usage

```hcl
module "lambda" {
  source = "../modules/lambda"

  app_name         = var.app_name
  environment      = var.environment
  aws_region       = var.aws_region
  ecs_cluster_name = module.ecs.cluster_name
  ecs_service_name = module.ecs.service_name
  log_retention    = var.log_retention_days
  tags             = local.tags
}
```

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| app_name | Application name | string | - | yes |
| environment | Deployment environment | string | - | yes |
| aws_region | AWS region | string | - | yes |
| ecs_cluster_name | ECS cluster name | string | - | yes |
| ecs_service_name | ECS service name | string | - | yes |
| log_retention | CloudWatch log retention in days | number | 30 | no |
| tags | Resource tags | map(string) | {} | no |

## Outputs

| Name | Description |
|------|-------------|
| validate_before_install_arn | ARN of the BeforeInstall Lambda function |
| validate_deployment_arn | ARN of the AfterInstall Lambda function |
| validate_test_traffic_arn | ARN of the AfterAllowTestTraffic Lambda function |
| run_migrations_arn | ARN of the BeforeAllowTraffic Lambda function |
| validate_production_arn | ARN of the AfterAllowTraffic Lambda function |

## Integration with CodeDeploy

These Lambda functions are referenced in the CodeDeploy AppSpec file:

```yaml
version: 0.0
Resources:
  - TargetService:
      Type: AWS::ECS::Service
      Properties:
        TaskDefinition: <TASK_DEFINITION>
        LoadBalancerInfo:
          ContainerName: "app"
          ContainerPort: 8000
        PlatformVersion: "1.4.0"
Hooks:
  - BeforeInstall: "arn:aws:lambda:region:account:function:validate-before-install"
  - AfterInstall: "arn:aws:lambda:region:account:function:validate-deployment"
  - AfterAllowTestTraffic: "arn:aws:lambda:region:account:function:validate-test-traffic"
  - BeforeAllowTraffic: "arn:aws:lambda:region:account:function:run-migrations"
  - AfterAllowTraffic: "arn:aws:lambda:region:account:function:validate-production"
```

## Custom Hook Development

To customize Lambda hook functionality:
1. Modify the Python scripts in the `lambdas/` directory
2. Update the Lambda module to include any additional environment variables
3. Add any required IAM permissions to the Lambda role policy