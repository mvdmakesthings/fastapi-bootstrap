# FastAPI Bootstrap with AWS Fargate Multi-Environment Deployment

A bootstrapped FastAPI project with versioned APIs, blue/green deployment, and multi-environment infrastructure as code for AWS Fargate.

---

## Features

- **Versioned API**: Built-in support for API versioning (v1, v2, etc.)
- **Multi-Environment**: Separate configurations for dev, test, and production
- **AWS Fargate Deployment**: Serverless container deployment with auto-scaling
- **Blue/Green Deployment**: Zero-downtime deployments via AWS CodeDeploy
- **Infrastructure as Code**: Complete Terraform configuration
- **CI/CD Pipeline**: Automated GitHub Actions workflow
- **Docker Support**: Development and production Docker configurations
- **FastAPI**: High-performance, easy-to-use Python web framework
- **Poetry**: Dependency management and packaging

---

## Project Structure

```
├── .aws/                  # AWS deployment configuration files
├── .github/workflows/     # GitHub Actions CI/CD configuration
├── src/                   # Application source code
│   └── fastapi_bootstrap/ # FastAPI application
│       ├── api/           # API endpoints
│       │   ├── v1/        # Version 1 API
│       │   └── v2/        # Version 2 API
│       └── main.py        # Application entrypoint
├── terraform/             # Infrastructure as code
│   ├── environments/      # Environment-specific configurations
│   │   ├── dev/
│   │   ├── test/
│   │   └── prod/
│   └── modules/           # Reusable Terraform modules
│       ├── vpc/
│       ├── ecs/
│       ├── ecr/
│       ├── iam/
│       ├── security/
│       └── codedeploy/
├── docker-compose.yml     # Local development configuration
├── docker-compose.test.yml # Testing configuration
├── Dockerfile             # Production Docker image
├── Dockerfile.test        # Test Docker image
└── deploy.sh              # Deployment script
```

---

## Getting Started

## Local Development

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Poetry (for dependency management)

### Setup

1. Clone the repository:
   ```bash
   git clone git@github.com:mvdmakesthings/fastapi-bootstrap.git
   cd fastapi-bootstrap
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Run the application locally:
   ```bash
   docker-compose up -d
   ```

4. Access the API at http://localhost:8000
   - API v1: http://localhost:8000/api/v1
   - Documentation: http://localhost:8000/docs

## AWS Deployment

### Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform CLI installed
- Docker installed

### Initial Deployment

1. Update your AWS account ID in the task definition and appspec files:
   ```bash
   find .aws -name 'task-definition-*.json' -exec sed -i '' 's/ACCOUNT_ID/YOUR_AWS_ACCOUNT_ID/g' {} \;
   find .aws -name 'appspec-*.yaml' -exec sed -i '' 's/ACCOUNT_ID/YOUR_AWS_ACCOUNT_ID/g' {} \;
   ```

2. Create an S3 bucket for Terraform state (optional but recommended):
   ```bash
   aws s3 mb s3://your-terraform-state-bucket
   aws dynamodb create-table --table-name terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   ```

3. Update Terraform backend configuration in `terraform/main.tf`

4. Deploy the infrastructure:
   ```bash
   ./deploy.sh --environment dev
   ```

5. Set up GitHub repository secrets for CI/CD:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`

### Adding a New API Version

1. Create a new version directory:
   ```bash
   mkdir -p src/fastapi_bootstrap/api/v2/endpoints
   touch src/fastapi_bootstrap/api/v2/__init__.py
   ```

2. Create a router for the new version:
   ```python
   # src/fastapi_bootstrap/api/v2/router.py
   from fastapi import APIRouter

   router = APIRouter(tags=["v2"])

   @router.get("/")
   async def root_v2():
       """
       Root endpoint for API v2
       """
       return {"version": "v2", "message": "Welcome to API v2"}
   ```

3. Update the main application to include the new version:
   ```python
   # src/fastapi_bootstrap/main.py
   from fastapi_bootstrap.api.v2.router import router as router_v2

   # After existing routers
   app.include_router(router_v2, prefix="/api/v2")
   ```

4. Create new Terraform resources for v2 in the ECS and CodeDeploy modules and ensure new "output" config has been added to main.tf
   ```
   output "api_v2_url" {
      value = "https://${module.ecs.alb_dns_name}/api/v2"
   }
   ```

5. Create new task definition and appspec files for v2 in the .aws directory

## Blue/Green Deployment

The project is configured for blue/green deployments via AWS CodeDeploy. This means:

1. New application versions are deployed to a new (green) environment
2. Traffic is gradually shifted from the old (blue) to the new (green) environment
3. The old environment is terminated after successful deployment

This ensures zero-downtime deployments and easy rollbacks if issues are detected.

## Multi-Environment Configuration

The project supports multiple deployment environments:

- **dev**: Development environment for testing new features
- **test**: Testing/QA environment for pre-production validation
- **prod**: Production environment for end users

Each environment has its own configuration in `terraform/environments/`.

## CI/CD Pipeline

The GitHub Actions workflow in `.github/workflows/deploy.yml` automatically:

1. Runs tests on pull requests
2. Builds and pushes Docker images on merge to main/develop
3. Deploys to the appropriate environment based on the branch
4. Manages blue/green deployments for each API version

## Development Workflow

```bash
# Run linting
poetry run poe lint

# Run spellcheck
poetry run poe spellcheck

# Fix formatting and spelling
poetry run poe fix

# Bump version
poetry run poe version_bump_patch  # For patch version (0.0.x)
poetry run poe version_bump_minor  # For minor version (0.x.0)
poetry run poe version_bump_major  # For major version (x.0.0)

# Run test
poetry run poe unittest  # For unit tests (pytest)
```

## Configuration

- All configuration is managed via environment variables (see `.env.example`).
- Environment-specific configurations are managed through Terraform variables in `terraform/environments/`.
- AWS resources are defined as infrastructure as code in the Terraform modules.

## License
MIT

---

## Database Migrations

This template is ready for integration with [Alembic](https://alembic.sqlalchemy.org/) for schema migrations.

```bash
# Example: Generate a new migration
poetry run alembic revision --autogenerate -m "create users table"

# Apply migrations
poetry run alembic upgrade head
```

---

## Testing

```bash
# Run all tests
poetry run poe unittest
```

---

## API Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## GitHub Workflows

Automated workflows ensure code quality and reliability:

- **Code Quality and Tests**: Runs on every push.
- **Linting**: Uses [Ruff](https://docs.astral.sh/ruff/).
- **Spellchecking**: Checks for common misspellings.
- **Configuration Linting**: Validates `pyproject.toml`.

---

## Contributing

1. Fork the repository and create your branch.
2. Follow the code style enforced by linting tools.
3. Add tests for new features or bug fixes.
4. Submit a pull request with a clear description.

---

## Resources

- [SQLModel](https://sqlmodel.tiangolo.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Docker](https://www.docker.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [Poetry](https://python-poetry.org/)

---

## Contributors

- Michael VanDyke ([@mvdmakesthings](https://github.com/mvdmakesthings))

---