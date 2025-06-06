# Local Development Guide

This guide provides instructions for setting up a local development environment for the FastAPI Bootstrap project.

## Development Options

You have several options for local development:

1. **Standard Docker Compose**: Simple setup with just the FastAPI application
2. **Development Docker Compose**: Full environment with LocalStack for AWS service emulation
3. **VS Code Dev Containers**: Integrated development environment within VS Code
4. **Local Python Environment**: Direct development on your local machine

## Option 1: Standard Docker Compose

This is the simplest option for running the application locally:

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The API will be available at http://localhost:8000.

## Option 2: Development Docker Compose

This option provides a more complete environment with:
- FastAPI application with hot reload
- PostgreSQL database
- LocalStack for AWS service emulation

```bash
# Start the development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop the environment
docker-compose -f docker-compose.dev.yml down
```

The API will be available at http://localhost:8000.

### LocalStack Services

LocalStack provides local emulation of AWS services:

- **S3**: http://localhost:4566 (endpoint URL for S3)
- **DynamoDB**: http://localhost:4566 (endpoint URL for DynamoDB)
- **SSM Parameter Store**: http://localhost:4566 (endpoint URL for SSM)
- **KMS**: http://localhost:4566 (endpoint URL for KMS)

To use LocalStack with the AWS CLI:

```bash
# List S3 buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# Get SSM parameter
aws --endpoint-url=http://localhost:4566 ssm get-parameter --name "/fastapi-bootstrap/dev/database/url" --with-decryption
```

## Option 3: VS Code Dev Containers

This option provides an integrated development environment within VS Code:

1. Install the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension in VS Code
2. Open the project folder in VS Code
3. Click the green button in the bottom-left corner or run the "Remote-Containers: Reopen in Container" command
4. Wait for the container to build and initialize

The development container includes:
- Python with Poetry
- AWS CLI
- Terraform
- GitHub CLI
- VS Code extensions for Python, Terraform, Docker, etc.

## Option 4: Local Python Environment

If you prefer to develop directly on your local machine:

1. Install Python 3.11 or later
2. Install Poetry:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

5. Run the application:
   ```bash
   poetry run uvicorn src.fastapi_bootstrap.main:app --reload
   ```

## Database Migrations

To run database migrations:

```bash
# Using Poetry
poetry run alembic upgrade head

# Using Docker
docker-compose -f docker-compose.dev.yml exec app alembic upgrade head
```

To create a new migration:

```bash
# Using Poetry
poetry run alembic revision --autogenerate -m "description of changes"

# Using Docker
docker-compose -f docker-compose.dev.yml exec app alembic revision --autogenerate -m "description of changes"
```

## Testing

To run tests:

```bash
# Using Poetry
poetry run pytest

# Using Docker
docker-compose -f docker-compose.test.yml up --exit-code-from app-test
```

## Code Quality

To run linting and formatting:

```bash
# Using Poetry
poetry run poe lint
poetry run poe fix

# Using Docker
docker-compose -f docker-compose.dev.yml exec app poe lint
docker-compose -f docker-compose.dev.yml exec app poe fix
```

## Working with AWS Services Locally

When developing locally, you can use LocalStack to emulate AWS services:

### SSM Parameter Store

```python
import boto3

# Create a boto3 client for SSM with LocalStack endpoint
ssm = boto3.client('ssm', endpoint_url='http://localhost:4566')

# Get a parameter
response = ssm.get_parameter(
    Name='/fastapi-bootstrap/dev/database/url',
    WithDecryption=True
)
db_url = response['Parameter']['Value']
```

### S3

```python
import boto3

# Create a boto3 client for S3 with LocalStack endpoint
s3 = boto3.client('s3', endpoint_url='http://localhost:4566')

# List buckets
response = s3.list_buckets()
buckets = [bucket['Name'] for bucket in response['Buckets']]
```

## Debugging

### VS Code Debugging

A launch configuration is provided for debugging in VS Code:

1. Set breakpoints in your code
2. Press F5 or select "Run > Start Debugging"
3. The application will start with the debugger attached

### Docker Debugging

To debug the application running in Docker:

1. Add the following to `docker-compose.dev.yml` under the `app` service:
   ```yaml
   ports:
     - "5678:5678"  # Debugging port
   environment:
     - PYTHONDONTWRITEBYTECODE=1
     - PYTHONUNBUFFERED=1
   command: python -m debugpy --listen 0.0.0.0:5678 -m uvicorn src.fastapi_bootstrap.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Configure VS Code to attach to the debugger:
   ```json
   {
     "name": "Docker: Attach",
     "type": "python",
     "request": "attach",
     "connect": {
       "host": "localhost",
       "port": 5678
     },
     "pathMappings": [
       {
         "localRoot": "${workspaceFolder}",
         "remoteRoot": "/app"
       }
     ]
   }
   ```

## Troubleshooting

### Common Issues

1. **Port conflicts**: If port 8000 is already in use, change the port mapping in `docker-compose.yml` or `docker-compose.dev.yml`:
   ```yaml
   ports:
     - "8001:8000"  # Map container port 8000 to host port 8001
   ```

2. **Database connection issues**: Ensure the database container is running:
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```

3. **LocalStack initialization issues**: Check the LocalStack logs:
   ```bash
   docker-compose -f docker-compose.dev.yml logs localstack
   ```

4. **Poetry dependency issues**: Try clearing the Poetry cache:
   ```bash
   poetry cache clear --all pypi
   ```