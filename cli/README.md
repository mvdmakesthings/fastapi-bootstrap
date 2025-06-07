# FastAPI Bootstrap CLI

The FastAPI Bootstrap CLI is a comprehensive command-line tool for managing the entire lifecycle of your FastAPI application, from initialization to development, infrastructure management, and deployment.

## Installation

The CLI is automatically installed when you install the FastAPI Bootstrap package:

```bash
# Using Poetry
poetry install

# Using pip
pip install -e .
```

## Commands

### Initialization

Initialize your FastAPI Bootstrap project:

```bash
# Initialize with specific parameters
fastapi-bootstrap init project --org-name mycompany --aws-profile dev --aws-region us-east-1 --environment dev

# Use AWS credentials instead of a profile
fastapi-bootstrap init project --org-name mycompany --aws-region us-east-1 --environment dev --use-credentials

# Initialize database credentials
fastapi-bootstrap init database --env dev --username admin --host localhost --port 5432 --database mydb
```

### Local Development

Start and manage your local development environment:

```bash
# Start development environment
fastapi-bootstrap dev start

# Stop development environment
fastapi-bootstrap dev stop

# View logs from the development environment
fastapi-bootstrap dev logs

# Run database migrations
fastapi-bootstrap dev migrate
```

### Infrastructure Management

Manage your AWS infrastructure using CDK:

```bash
# Bootstrap AWS environment for CDK (first-time setup)
fastapi-bootstrap infra bootstrap --aws-profile dev --aws-region us-east-1

# Deploy infrastructure
fastapi-bootstrap infra deploy --env dev --aws-profile dev --aws-region us-east-1

# Check infrastructure status
fastapi-bootstrap infra status --env dev --aws-profile dev --aws-region us-east-1

# Destroy infrastructure
fastapi-bootstrap infra destroy --env dev --aws-profile dev --aws-region us-east-1 --force
```

### Application Deployment

Deploy your FastAPI application to AWS:

```bash
# Deploy with specific parameters
fastapi-bootstrap deploy app --env dev --aws-profile dev --aws-region us-east-1 --image-tag v1.0.0

# Skip building the Docker image (use existing image)
fastapi-bootstrap deploy app --env dev --image-tag v1.0.0 --skip-build

# Check deployment status
fastapi-bootstrap deploy status --env dev --aws-profile dev --aws-region us-east-1
```

## Configuration

The CLI stores configuration in `~/.fastapi-bootstrap/config.yaml`. This includes:

- Environment configurations (dev, test, prod)
- AWS credentials and resource names
- Organization name and other settings

Example configuration:

```yaml
environments:
  dev:
    org_name: mycompany
    aws_profile: dev
    aws_region: us-east-1
    account_id: 123456789012
    state_bucket: mycompany-dev-terraform-state-123456789012
    lock_table: mycompany-dev-terraform-locks
    cdk_bootstrap_bucket: cdk-bootstrap-mycompany-dev-123456789012
    use_credentials: false
  prod:
    org_name: mycompany
    aws_profile: prod
    aws_region: us-east-1
    account_id: 123456789012
    state_bucket: mycompany-prod-terraform-state-123456789012
    lock_table: mycompany-prod-terraform-locks
    cdk_bootstrap_bucket: cdk-bootstrap-mycompany-prod-123456789012
    use_credentials: false
```

## Secure Credential Handling

The CLI provides secure credential management:

- AWS credentials can be stored securely with encryption
- Database credentials can be stored locally and optionally in AWS Secrets Manager
- Sensitive information is never logged or exposed

Credentials are stored in encrypted files in the `~/.fastapi-bootstrap/` directory:

- `~/.fastapi-bootstrap/dev_credentials.enc` - Encrypted credentials for dev environment
- `~/.fastapi-bootstrap/test_credentials.enc` - Encrypted credentials for test environment
- `~/.fastapi-bootstrap/prod_credentials.enc` - Encrypted credentials for prod environment

## Poetry Tasks

The CLI can be used with Poetry tasks for a better development experience:

```bash
# Initialize project
poetry run poe init

# Start development environment
poetry run poe dev

# Deploy infrastructure
poetry run poe deploy_infra

# Deploy application
poetry run poe deploy_app
```

## AWS CDK Infrastructure

The CLI uses AWS CDK to manage infrastructure. The infrastructure code is organized into stacks:

- **API Stack** - ECS Fargate service, load balancer, and VPC
- **Database Stack** - RDS PostgreSQL database
- **Monitoring Stack** - CloudWatch dashboards and alarms

For more details on the CDK infrastructure, see the [CDK Infrastructure Documentation](../../docs/cdk-infrastructure.md).

## Extending the CLI

The CLI is designed to be extensible. You can add new commands by:

1. Creating a new command module in `src/fastapi_bootstrap/cli/commands/`
2. Registering the command in `src/fastapi_bootstrap/cli/main.py`

Example of a custom command:

```python
@click.command(name="custom")
@click.option("--param", help="A custom parameter")
def custom_command(param):
    """A custom command."""
    click.echo(f"Custom command with param: {param}")

# In main.py
from cli.commands.custom import custom_command
cli.add_command(custom_command)
```
