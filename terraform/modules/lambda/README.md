# Lambda Module

This module creates Lambda functions for CodeDeploy hooks used in the blue/green deployment process.

## Functions

1. **validate_before_install**: Validates prerequisites before deployment
2. **validate_deployment**: Validates the deployment was successful
3. **validate_test_traffic**: Validates the application with test traffic
4. **run_migrations**: Runs database migrations before production traffic
5. **validate_production**: Final validation after production traffic is routed

## Usage

```hcl
module "lambda" {
  source = "../modules/lambda"

  app_name    = var.app_name
  environment = var.environment
}
```

## Outputs

- `validate_before_install_arn`: ARN of the BeforeInstall Lambda function
- `validate_deployment_arn`: ARN of the AfterInstall Lambda function
- `validate_test_traffic_arn`: ARN of the AfterAllowTestTraffic Lambda function
- `run_migrations_arn`: ARN of the BeforeAllowTraffic Lambda function
- `validate_production_arn`: ARN of the AfterAllowTraffic Lambda function