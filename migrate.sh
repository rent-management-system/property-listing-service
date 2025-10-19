#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
  export $(cat .env | sed 's/#.*//g' | xargs)
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
  echo "Error: DATABASE_URL is not set. Please check your .env file."
  exit 1
fi

# Create a psql-compatible URL by removing the '+asyncpg' driver specifier
PSQL_URL=${DATABASE_URL/+asyncpg/}

# Run the schema and seed SQL files
echo "Running schema setup..."
psql "$PSQL_URL" -f sql/schema.sql

echo "Running database seeding..."
psql "$PSQL_URL" -f sql/seed.sql

echo "Database migration and seeding completed."