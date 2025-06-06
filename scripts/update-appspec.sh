#!/bin/bash
# Script to update appspec files with Lambda ARNs from Terraform outputs

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

echo "Updating appspec files for $ENVIRONMENT environment"

# Get Lambda ARNs from Terraform outputs
cd "$(dirname "$0")/../terraform/environments/$ENVIRONMENT"
VALIDATE_BEFORE_INSTALL_ARN=$(terraform output -raw lambda_validate_before_install_arn)
VALIDATE_DEPLOYMENT_ARN=$(terraform output -raw lambda_validate_deployment_arn)
VALIDATE_TEST_TRAFFIC_ARN=$(terraform output -raw lambda_validate_test_traffic_arn)
RUN_MIGRATIONS_ARN=$(terraform output -raw lambda_run_migrations_arn)
VALIDATE_PRODUCTION_ARN=$(terraform output -raw lambda_validate_production_arn)

# Create a temporary file with the updated hooks
cd ../../../
cat > .aws/appspec-v1-${ENVIRONMENT}.yaml.new << EOF
version: 0.0

Resources:
  - TargetService:
      Type: AWS::ECS::Service
      Properties:
        TaskDefinition: <TASK_DEFINITION>
        LoadBalancerInfo:
          ContainerName: "fastapi-bootstrap-v1"
          ContainerPort: 8000
        PlatformVersion: "LATEST"
        NetworkConfiguration:
          AwsvpcConfiguration:
            Subnets: ["<SUBNET_1>", "<SUBNET_2>"]
            SecurityGroups: ["<SECURITY_GROUP>"]
            AssignPublicIp: "DISABLED"

Hooks:
  - BeforeInstall: "${VALIDATE_BEFORE_INSTALL_ARN}"
  - AfterInstall: "${VALIDATE_DEPLOYMENT_ARN}"
  - AfterAllowTestTraffic: "${VALIDATE_TEST_TRAFFIC_ARN}"
  - BeforeAllowTraffic: "${RUN_MIGRATIONS_ARN}"
  - AfterAllowTraffic: "${VALIDATE_PRODUCTION_ARN}"
EOF

# Replace the original file
mv .aws/appspec-v1-${ENVIRONMENT}.yaml.new .aws/appspec-v1-${ENVIRONMENT}.yaml

echo "Successfully updated appspec-v1-${ENVIRONMENT}.yaml with Lambda ARNs"