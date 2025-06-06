#!/bin/bash
# Create initial database schema

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create schemas
    CREATE SCHEMA IF NOT EXISTS app;

    -- Create extension for UUID generation
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Create example table
    CREATE TABLE IF NOT EXISTS app.users (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        username VARCHAR(100) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );

    -- Create index on username and email
    CREATE INDEX IF NOT EXISTS idx_users_username ON app.users(username);
    CREATE INDEX IF NOT EXISTS idx_users_email ON app.users(email);

    -- Grant privileges
    GRANT ALL PRIVILEGES ON SCHEMA app TO postgres;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app TO postgres;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA app TO postgres;
EOSQL

echo "Database initialization completed"
