#!/bin/bash
set -e

# Load environment variables safely
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    if ! source .env; then
        echo "Error: Failed to source .env. Ensure every line is KEY=VALUE (no bare URLs)." >&2
        exit 1
    fi
    set +a
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL is not set in .env file."
    exit 1
fi

echo "Running Alembic migrations..."
# Use the project's virtual environment Alembic binary
"$(pwd)/Bate/bin/alembic" upgrade head

# Apply seed data only if seed.sql exists and after migrations
if [ -f sql/seed.sql ]; then
    echo "Applying seed.sql..."
    # Extract DB connection details for psql from DATABASE_URL
    # Assuming DATABASE_URL is in the format: postgresql+asyncpg://user:password@host:port/dbname
    DB_USER=$(echo $DATABASE_URL | sed -r "s/postgresql\+asyncpg:\/\/(.*):.*@.*/\1/")
    DB_PASSWORD=$(echo $DATABASE_URL | sed -r "s/postgresql\+asyncpg:\/\/.*:(.*)@.*/\1/")
    DB_HOST=$(echo $DATABASE_URL | sed -r "s/postgresql\+asyncpg:\/\/.*@(.*):.*/\1/")
    DB_PORT=$(echo $DATABASE_URL | sed -r "s/postgresql\+asyncpg:\/\/.*:.*@.*:(.*)\/.*/\1/")
    DB_NAME=$(echo $DATABASE_URL | sed -r "s/postgresql\+asyncpg:\/\/.*@.*\/([^?]*).*/\1/")

    export PGPASSWORD=$DB_PASSWORD

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f sql/seed.sql
else
    echo "sql/seed.sql not found, skipping."
fi

echo "Database migration and seeding complete."