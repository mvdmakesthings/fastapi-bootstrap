# FastAPI Bootstrap with AWS Fargate Multi-Environment Deployment

A production-ready FastAPI template with versioned APIs, zero-downtime deployments, and complete infrastructure as code for AWS Fargate.

[![GitHub Actions Status](https://github.com/mvdmakesthings/fastapi-bootstrap/workflows/CI/badge.svg)](https://github.com/mvdmakesthings/fastapi-bootstrap/actions)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0+-teal.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Gitingest](https://img.shields.io/badge/Gitingest-green.svg)](https://gitingest.com/mvdmakesthings/fastapi_bootstrap)

## Overview

FastAPI Bootstrap provides a complete foundation for building production-grade APIs with infrastructure designed to scale. This project implements industry best practices for continuous deployment, security, and multi-environment management.

## Key Features

- **Versioned API Architecture**: Built-in support for API versioning (v1, v2, etc.)
- **Multi-Environment Deployments**: Separate configurations for dev, test, and production
- **Zero-Downtime Deployments**: Blue/green deployment via AWS CodeDeploy
- **Infrastructure as Code**: Complete Terraform modules for AWS infrastructure
- **CI/CD Pipeline**: Automated GitHub Actions workflows for testing and deployment
- **Containerization**: Docker configurations for development, testing, and production
- **Local Development**: LocalStack integration for AWS service emulation
- **Security Best Practices**: WAF, VPC isolation, encrypted storage, least privilege IAM

## Documentation

- [Architecture](docs/architecture.md): System architecture and component details
- [Infrastructure](docs/infrastructure.md): AWS infrastructure design and management
- [Local Development](docs/local-development.md): Setting up your local development environment
- [Deployment Guide](docs/deployment-guide.md): Step-by-step deployment instructions
- [Blue/Green Deployment](docs/blue-green-deployment.md): Zero-downtime deployment strategy
- [Security](docs/security.md): Security features and best practices
- [Observability](docs/observability.md): Monitoring, logging, and tracing
- [Cost Optimization](docs/cost-optimization.md): Cost management strategies

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Poetry (for dependency management)
- AWS CLI (for deployment)
- Terraform CLI (for infrastructure)

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/mvdmakesthings/fastapi-bootstrap.git
   cd fastapi-bootstrap
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Start the local development environment:
   ```bash
   docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d
   ```

4. Access the API:
   - API: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

See [Local Development Guide](docs/local-development.md) for detailed instructions.

### AWS Deployment

1. Set up the Terraform backend:
   ```bash
   ./scripts/setup-terraform-backend.sh --org-name YOUR-ORGANIZATION-NAME
   ```

2. Deploy to your AWS environment:
   ```bash
   ./scripts/deploy.sh --environment dev --account-id YOUR_AWS_ACCOUNT_ID --region us-east-1 --domain example.com
   ```

See [Deployment Guide](docs/deployment-guide.md) for detailed instructions.

## Project Structure

```
├── .aws/                    # AWS deployment configuration files
├── .github/workflows/       # GitHub Actions CI/CD configuration
├── docs/                    # Documentation
├── infrastructure/          # Infrastructure-related components
│   ├── docker/              # Docker configurations
│   │   ├── Dockerfile       # Production Docker configuration
│   │   ├── Dockerfile.dev   # Development Docker configuration
│   │   ├── Dockerfile.test  # Testing Docker configuration
│   │   └── docker-compose.* # Docker Compose configurations
│   ├── localstack/          # LocalStack configurations for AWS
├── src/                     # Application source code
│   └── fastapi_bootstrap/   # FastAPI application
│       ├── api/             # API endpoints by version
│       │   ├── v1/          # Version 1 API
│       │   └── v2/          # Version 2 API (example)
│       └── utils/           # Utility functions and middleware
├── tests/                 # Test suite
```

## Development Workflow

```bash
# Run linting and formatting
poetry run poe lint
poetry run poe fix

# Run tests
poetry run poe unittest

# Check spelling
poetry run poe spellcheck

# Version management
poetry run poe version_bump_patch  # For patch version (0.0.x)
poetry run poe version_bump_minor  # For minor version (0.x.0)
poetry run poe version_bump_major  # For major version (x.0.0)
```

## Database Migrations

```bash
# Generate a new migration
poetry run alembic revision --autogenerate -m "create users table"

# Apply migrations
poetry run alembic upgrade head
```

