# Property Listing Service

This is the backend microservice for a property listing platform. It handles the creation, management, and retrieval of property listings. It is designed to work within a larger microservices ecosystem, integrating with separate services for user management, payments, and notifications.

## Features

- **Public Property Listings:** Provides a public, filterable, and paginated endpoint to browse all approved properties.
- **Owner-Specific Actions:** Allows users with an "Owner" role to submit new properties for approval.
- **Secure Authentication:** Integrates with an external user management service to authorize user actions using JWTs.
- **Database Migrations:** Includes a simple shell script to set up and seed the PostgreSQL database.
- **Asynchronous:** Built with FastAPI and `asyncpg` for high-performance, non-blocking database operations.

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL (interfaced with SQLAlchemy and `asyncpg`)
- **Data Validation:** Pydantic
- **Authentication:** JWT (via `python-jose`)
- **HTTP Client:** `httpx` for service-to-service communication
- **Server:** Uvicorn

## API Documentation

For detailed information about all API endpoints, request/response models, and usage examples, please see the **[API Documentation](API_DOCUMENTATION.md)**.

---

## Live API Docs

The API is deployed and accessible. The interactive documentation (Swagger UI) can be found at:

[https://property-listing-service.onrender.com/docs](https://property-listing-service.onrender.com/docs)

---

## Getting Started

Follow these instructions to set up and run the project on your local machine.

### 1. Prerequisites

- Python 3.10+
- PostgreSQL server running locally or on a network accessible to you.
- `psql` command-line tool installed (for running migrations).

### 2. Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd property-listing-service
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    # On Windows, use: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your environment:**
    -   Create a `.env` file in the root directory by copying the example file:
        ```bash
        cp .env.example .env
        ```
    -   Open the `.env` file and edit the variables, especially `DATABASE_URL` and `JWT_SECRET`, to match your local setup.

### 3. Database Migration

Run the migration script to set up your database tables. This script uses the `DATABASE_URL` from your `.env` file.

```bash
# Make the script executable (run once)
chmod +x migrate.sh

# Run the migrations
./migrate.sh
```

### 4. Running the Application

Use `uvicorn` to start the development server.

```bash


```

The API will now be running at `http://127.0.0.1:8000`.
