# Stage 1: Build the application
FROM python:3.10-slim as builder

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy only files needed for dependency installation
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Stage 2: Create the production image
FROM python:3.10-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv ./.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
