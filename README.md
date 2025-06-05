# FastAPI Bootstrap Template

A production-ready template for quickly bootstrapping scalable, reliable API services using [FastAPI](https://fastapi.tiangolo.com/), [SQLModel](https://sqlmodel.tiangolo.com/), [PostgreSQL](https://www.postgresql.org/), and Docker. Designed for rapid development, best practices, and easy deployment.

---

## Features

- **FastAPI**: High-performance, easy-to-use Python web framework.
- **SQLModel**: Modern ORM for type-safe database access.
- **PostgreSQL**: Robust, production-grade relational database.
- **Docker**: Containerized development and deployment.
- **Poetry**: Dependency management and packaging.
- **Automated Code Quality**: Linting, spellchecking, and formatting via GitHub Actions.
- **Environment-based Configuration**: Easily switch between dev, test, and prod.

---

## Project Structure

```text
fastapi-bootstrap/
├── app/                # Main application code
│   ├── api/            # API route definitions
│   ├── core/           # Core settings, config, and utilities
│   ├── db/             # Database models and session
│   └── main.py         # FastAPI entrypoint
├── tests/              # Unit and integration tests
├── Dockerfile          # Docker image definition
├── docker-compose.yml  # Multi-container orchestration
├── pyproject.toml      # Project metadata and dependencies
├── .env.example        # Example environment variables
└── README.md           # Project documentation
```

---

## Getting Started

### 1. Requirements

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/) for dependency management
- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) (for containerized setup)
- PostgreSQL (local or via Docker)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/your-org/fastapi-bootstrap.git
cd fastapi-bootstrap

# Copy environment variables template and edit as needed
cp .env.example .env

# Install dependencies
poetry install
```

### 3. Running the Application

#### Local Development (with Docker)

```bash
# Start API and PostgreSQL using Docker Compose
docker-compose up --build
```

- FastAPI will be available at `http://localhost:8000`
- PostgreSQL will be available at `localhost:5432` (see `.env` for credentials)

#### Local Development (without Docker)

1. Ensure PostgreSQL is running and accessible.
2. Update `.env` with your database credentials.
3. Run the API:

```bash
poetry run uvicorn app.main:app --reload
```

---

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
```

---

## Configuration

- All configuration is managed via environment variables (see `.env.example`).
- Sensitive values (e.g., database credentials, secret keys) should never be committed.
- Use [Pydantic Settings](https://docs.pydantic.dev/latest/usage/pydantic_settings/) for structured config in `app/core/config.py`.

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
poetry run pytest
```

---

## API Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

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