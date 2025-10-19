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

# Run the schema and seed SQL files
psql $DATABASE_URL -f sql/schema.sql
psql $DATABASE_URL -f sql/seed.sql

echo "Database migration and seeding completed."
