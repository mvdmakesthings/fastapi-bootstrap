#!/bin/bash
# Script to generate Python Lambda function zip files for deployment hooks

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Create directory for Lambda functions if it doesn't exist
mkdir -p "$PROJECT_ROOT/terraform/modules/lambda/lambda_functions"

# Create a simple Python Lambda function
cat > /tmp/lambda_handler.py << 'EOF'
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Simple Lambda function for CodeDeploy hooks
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Get the deployment ID from the event
    deployment_id = event.get('deploymentId', 'unknown')
    lifecycle_event_hook_execution_id = event.get('lifecycleEventHookExecutionId', 'unknown')
    
    logger.info(f"Deployment ID: {deployment_id}")
    logger.info(f"Lifecycle Event Hook Execution ID: {lifecycle_event_hook_execution_id}")
    
    # Return success
    return {
        'status': 'Succeeded',
        'message': 'Validation successful'
    }
EOF

# Create a more complex function for migrations
cat > /tmp/migrations_handler.py << 'EOF'
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Lambda function for running database migrations
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Get the deployment ID from the event
    deployment_id = event.get('deploymentId', 'unknown')
    environment = os.environ.get('ENVIRONMENT', 'dev')
    
    logger.info(f"Running migrations for deployment: {deployment_id}")
    logger.info(f"Environment: {environment}")
    
    # In a real scenario, you would run migrations here
    # For example, by invoking a container task or connecting to the database
    
    # Simulate migration execution
    logger.info("Migrations completed successfully")
    
    # Return success
    return {
        'status': 'Succeeded',
        'message': 'Migrations completed successfully'
    }
EOF

# Create zip files for each Lambda function
echo "Creating Lambda function zip files..."

# Create validate_before_install function
cd /tmp
zip -q validate_before_install.zip lambda_handler.py
mv validate_before_install.zip "$PROJECT_ROOT/terraform/modules/lambda/lambda_functions/"

# Create validate_deployment function
zip -q validate_deployment.zip lambda_handler.py
mv validate_deployment.zip "$PROJECT_ROOT/terraform/modules/lambda/lambda_functions/"

# Create validate_test_traffic function
zip -q validate_test_traffic.zip lambda_handler.py
mv validate_test_traffic.zip "$PROJECT_ROOT/terraform/modules/lambda/lambda_functions/"

# Create run_migrations function
zip -q run_migrations.zip migrations_handler.py
mv run_migrations.zip "$PROJECT_ROOT/terraform/modules/lambda/lambda_functions/"

# Create validate_production function
zip -q validate_production.zip lambda_handler.py
mv validate_production.zip "$PROJECT_ROOT/terraform/modules/lambda/lambda_functions/"

echo "Lambda function zip files created successfully"