#!/bin/bash
# Entrypoint script for the FastAPI application

set -e

# Function to check if the database is ready
function wait_for_db() {
    echo "Waiting for database to be ready..."
    while ! nc -z db 5432; do
        sleep 0.5
    done
    echo "Database is ready!"
}

# Wait for the database to be ready
wait_for_db

# Run migrations if needed (uncomment when migrations are set up)
# echo "Running migrations..."
# alembic upgrade head

# Execute the command provided as arguments
exec "$@"
