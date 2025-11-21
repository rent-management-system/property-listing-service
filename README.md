# Property Listing Service

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Architecture](#architecture)
- [Technologies Used](#technologies-used)
- [Setup Guide](#setup-guide)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Installation](#installation)
  - [Database Setup](#database-setup)
  - [Running the Application](#running-the-application)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
  - [Public Endpoints](#public-endpoints)
  - [Property Owner Endpoints](#property-owner-endpoints)
  - [Service-to-Service Endpoints](#service-to-service-endpoints)
  - [Admin / Metrics Endpoints](#admin--metrics-endpoints)
- [Scheduled Tasks](#scheduled-tasks)
- [Inter-Service Communication](#inter-service-communication)
  - [Payment Processing Flow (via Chapa)](#payment-processing-flow-via-chapa)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

## Introduction
The Property Listing Service is a central component of the Rent Management System, designed to manage the lifecycle of property listings. It enables property owners to submit, update, and manage their properties, provides public access to approved listings, and integrates with other services for user authentication, payment processing, and notifications. This service ensures that properties are accurately listed, easily discoverable, and properly managed throughout their active period.

## Features
-   **Property Submission**: Allows authenticated property owners to submit new property listings with detailed information and photos.
-   **Geocoding Integration**: Automatically geocodes property locations for map-based search and display.
-   **Listing Management**: Owners can view, update, soft-delete, reserve, and unreserve their properties.
-   **Public Property Search**: Provides robust search and filtering capabilities for approved properties based on location, price, amenities, and full-text search.
-   **Payment Integration**: Seamlessly integrates with the Payment Processing Service for listing approval payments, ensuring properties are paid for before public display.
-   **Property Status Management**: Manages property lifecycle statuses (PENDING, APPROVED, REJECTED, RESERVED, DELETED).
-   **Object Storage for Photos**: Utilizes object storage for efficient and scalable handling of property images.
-   **Authentication & Authorization**: Secures API endpoints using JWT for user roles (Owner, Admin) and API keys for service-to-service communication.
-   **Structured Logging**: Provides detailed, structured logs for better observability, debugging, and monitoring.
-   **Health Checks & Metrics**: Offers endpoints for monitoring service health and operational metrics.

## Architecture
The Property Listing Service operates within a broader microservices ecosystem. Below is a C4 Context diagram illustrating its interactions with other key systems.

```mermaid
C4Context
    title System Context for Rent Management System

    System_Ext(User, "User", "End-users interacting with the system")
    System_Ext(Landlord, "Landlord", "Property owners using the system")
    System_Ext(ObjectStorage, "Object Storage", "External service for storing property photos (e.g., AWS S3, MinIO)")
    System_Ext(GeocodingService, "Geocoding Service", "External service for converting addresses to coordinates (e.g., Gebeta)")

    System(UserManagementService, "User Management Service", "Manages user authentication and profiles")
    System(PaymentProcessingService, "Payment Processing Service", "Handles payment initiation, status tracking, and webhooks")
    System(NotificationService, "Notification Service", "Handles sending notifications to users")
    System(PropertyListingService, "Property Listing Service", "Manages property listings and approvals")

    Rel(User, PropertyListingService, "Views and searches properties via")
    Rel(Landlord, PropertyListingService, "Submits and manages properties via")
    Rel(PropertyListingService, UserManagementService, "Verifies user tokens and fetches user details from")
    Rel(PropertyListingService, PaymentProcessingService, "Initiates payment for listing approval with")
    Rel(PaymentProcessingService, PropertyListingService, "Notifies about payment status (success/failure) via webhook")
    Rel(PropertyListingService, NotificationService, "Sends property-related notifications via")
    Rel(PropertyListingService, ObjectStorage, "Stores and retrieves property photos from")
    Rel(PropertyListingService, GeocodingService, "Resolves property locations to coordinates with")
```

## Technologies Used
-   **FastAPI**: High-performance web framework for building APIs.
-   **SQLAlchemy (Async)**: Asynchronous ORM for interacting with PostgreSQL.
-   **PostgreSQL**: Relational database for storing property records.
-   **Pydantic**: Data validation and settings management.
-   **Gebeta API**: Integration with a geocoding service for location data.
-   **httpx**: A fully featured asynchronous HTTP client for making requests to external services.
-   **python-jose**: For JSON Web Token (JWT) handling.
-   **structlog**: For structured, machine-readable logging.
-   **Docker**: For containerization and deployment.

## Setup Guide

### Prerequisites
Before you begin, ensure you have the following installed:
-   Python 3.10+
-   Docker and Docker Compose (for local development with services like PostgreSQL)
-   `pip` (Python package installer)

### Environment Variables
Create a `.env` file in the root directory of the project based on the `.env.example` (which you should create if it doesn't exist).

```
# .env.example
DATABASE_URL="postgresql+asyncpg://user:password@host:port/dbname"
JWT_SECRET="your_jwt_secret_key_for_signing_tokens"
USER_MANAGEMENT_URL="http://localhost:8001" # URL of the User Management Service
PAYMENT_PROCESSING_SERVICE_URL="http://localhost:8000" # URL of the Payment Processing Service
NOTIFICATION_SERVICE_URL="http://localhost:8002" # URL of the Notification Service
GEBETA_API_KEY="your_gebeta_api_key" # API key for the geocoding service
OBJECT_STORAGE_BUCKET_NAME="your-bucket-name"
OBJECT_STORAGE_ENDPOINT_URL="http://localhost:9000" # e.g., MinIO endpoint
OBJECT_STORAGE_ACCESS_KEY="your_access_key"
OBJECT_STORAGE_SECRET_KEY="your_secret_key"
PROPERTY_WEBHOOK_API_KEY="a_secret_key_for_payment_service_to_call_this_service" # API key for Payment Service to authenticate with this service
```

### Installation
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/rent-management-system/Rent-management--system--property-listing-service # Adjust repository name if different
    cd Rent-management--system--property-listing-service
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Database Setup
This service uses PostgreSQL. You can set up a local PostgreSQL instance using Docker Compose or a standalone installation.

1.  **Ensure your `DATABASE_URL` in `.env` is correctly configured.**
2.  **Run the migration script**:
    ```bash
    ./migrate.sh
    ```
    This script will apply the necessary schema and migrations to your database.

### Running the Application
1.  **Start dependent services**: Ensure your PostgreSQL, User Management, Payment Processing, and Notification services are running and accessible as configured in your `.env` file.
2.  **Run the FastAPI application**:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
    ```
    The `--reload` flag is useful for development as it restarts the server on code changes. For production, remove this flag.

The API documentation will be available at `http://localhost:8003/docs` (Swagger UI) and `http://localhost:8003/redoc` (ReDoc).

## Database Schema
The core data for this service is stored in the `properties` table. Below is a simplified representation of its schema:

```mermaid
erDiagram
    properties {
        UUID id PK
        UUID user_id FK "User Management Service"
        UUID payment_id FK "Payment Processing Service"
        VARCHAR(255) title
        TEXT description
        VARCHAR(255) location
        NUMERIC(10, 2) price
        VARCHAR(50) house_type ENUM("condominium", "private home", ...)
        JSON amenities
        JSON photos
        ENUM("PENDING", "APPROVED", "REJECTED", "RESERVED", "DELETED") status
        ENUM("PENDING", "SUCCESS", "FAILED", "PAID") payment_status
        DATETIME approval_timestamp
        FLOAT lat
        FLOAT lon
        DATETIME created_at
        DATETIME updated_at
        TSVECTOR fts
    }
```

## API Endpoints
This service exposes several API endpoints categorized by their access level and functionality. For detailed request/response examples and parameter descriptions, please refer to `API_DOCUMENTATION.md`.

### Public Endpoints
-   **`GET /properties`**: Retrieve a paginated and filterable list of all approved properties.
-   **`GET /properties/{id}`**: Retrieve details of a specific property (accessible if approved, or if user is owner/admin).

### Property Owner Endpoints
(Require `Owner` role authentication)
-   **`POST /properties/submit`**: Submit a new property listing.
-   **`GET /properties/my-properties`**: Retrieve all properties owned by the authenticated user.
-   **`PUT /properties/{property_id}`**: Update an existing property.
-   **`DELETE /properties/{property_id}`**: Soft delete a property.
-   **`PATCH /properties/{property_id}/reserve`**: Mark an approved property as reserved.
-   **`PATCH /properties/{property_id}/unreserve`**: Change a reserved property back to approved.
-   **`PATCH /properties/{property_id}/approve-and-pay`**: Initiate payment for a pending property to get it approved.

### Service-to-Service Endpoints
-   **`POST /payments/confirm`**: Internal webhook endpoint for the Payment Processing Service to confirm payment status and update property approval. (Requires `PROPERTY_WEBHOOK_API_KEY`).

### Admin / Metrics Endpoints
-   **`GET /properties/metrics`**: Retrieve operational metrics for property listings (e.g., counts by status).

## Scheduled Tasks
The service may include scheduled tasks for maintenance or background processing, such as:
-   **Property Cleanup**: Tasks to handle properties that remain in certain states for too long or require periodic review. (Refer to `app/services/property_cleanup.py` for details).

## Inter-Service Communication
This microservice is designed to operate within a larger ecosystem, communicating with other services to fulfill its responsibilities.

-   **User Management Service**:
    -   **Authentication & Authorization**: This service relies heavily on the User Management Service for authenticating users and authorizing their actions. JWT tokens issued by the User Management Service are validated for every protected endpoint. User roles (e.g., 'Owner', 'Admin') determine access levels.
    -   **User Details Fetch**: When necessary (e.g., for payment initiation or notifications), this service may fetch additional user details from the User Management Service.
-   **Payment Processing Service**:
    -   **Payment Initiation**: When a property owner wishes to get their `PENDING` property `APPROVED` for public listing, they call the `/properties/{property_id}/approve-and-pay` endpoint. This service then makes an internal service-to-service call to the Payment Processing Service to initiate the payment. The Payment Processing Service handles the actual interaction with payment gateways like Chapa.
    -   **Webhook Reception**: After a payment is processed (successfully or not) by the Payment Processing Service, it sends a webhook notification to this service's `/payments/confirm` endpoint. This webhook is crucial for updating the `payment_status` and `status` of the property (e.g., changing from `PENDING` to `APPROVED` upon successful payment).
-   **Notification Service**:
    -   **Event Notifications**: This service sends various event-driven notifications (e.g., property approval, payment status updates, listing expiry warnings) to users via the Notification Service. This ensures users are kept informed about the status of their listings.
-   **Geocoding Service (Gebeta)**:
    -   **Location Resolution**: Upon property submission, the provided `location` string is sent to the Gebeta Geocoding Service to resolve it into precise geographical coordinates (`lat`, `lon`). This enables map-based search and location-aware features.
-   **Object Storage**:
    -   **Photo Management**: Property images uploaded by owners are stored in a configured object storage solution (e.g., MinIO, AWS S3). This service handles the upload and retrieval of these photo URLs.

### Payment Processing Flow (via Chapa)
The payment process for property listing approval is orchestrated through the dedicated Payment Processing Service, which integrates with the **Chapa Payment Gateway**.

1.  **Owner Initiates Payment**: A property owner calls the `PATCH /properties/{property_id}/approve-and-pay` endpoint on this Property Listing Service.
2.  **Internal Call to Payment Service**: The Property Listing Service makes a secure, authenticated internal call to the Payment Processing Service, requesting to initiate a payment for the specified `property_id` and `user_id`.
3.  **Payment Service & Chapa**: The Payment Processing Service then interacts with the Chapa Payment Gateway to create a transaction and obtain a `checkout_url`.
4.  **Redirect to Chapa**: The `checkout_url` is returned to the Property Listing Service, which then passes it back to the frontend. The frontend is responsible for redirecting the user's browser to this Chapa `checkout_url` to complete the payment.
5.  **Chapa Webhook to Payment Service**: Once the user completes the payment on Chapa's platform, Chapa sends a webhook notification to the Payment Processing Service, updating it on the payment's final status (SUCCESS/FAILED).
6.  **Payment Service Webhook to Property Listing Service**: The Payment Processing Service, in turn, sends its own internal webhook to the Property Listing Service's `POST /payments/confirm` endpoint. This final webhook updates the `payment_status` and, if successful, changes the property's `status` from `PENDING` to `APPROVED`, making it publicly visible.

## Logging
The service uses `structlog` for structured logging. This provides machine-readable logs that are easier to parse, filter, and analyze with log management tools. Logs are output to `stdout` and can be configured for JSON or console rendering.

## Error Handling
-   **HTTPException**: FastAPI's `HTTPException` is used for standard HTTP error responses (e.g., 400 Bad Request, 401 Unauthorized, 404 Not Found).
-   **Retry Mechanism**: The `app.utils.retry.py` module provides an `@async_retry` decorator for resilient communication with external services, handling transient network issues or service unavailability with exponential backoff.
-   **Service Unavailable**: Specific `HTTPException`s are raised when dependent services are unresponsive.

## Contributing
Contributions are welcome! Please follow standard GitHub flow:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and ensure tests pass.
4.  Submit a pull request with a clear description of your changes.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact
For any inquiries or support, please reach out to the developer:
-   **Email**: dagiteferi2011@gmail.com
-   **WhatsApp**: +251920362324