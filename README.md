# Payment Processing Microservice

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
- [API Endpoints](#api-endpoints)
  - [Authentication](#authentication)
  - [Payments](#payments)
  - [Webhooks](#webhooks)
  - [Health Check](#health-check)
  - [Metrics](#metrics)
- [Scheduled Tasks](#scheduled-tasks)
- [Inter-Service Communication](#inter-service-communication)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

## Introduction
The Payment Processing Microservice is a core component of the Rent Management System, meticulously designed to handle all payment-related operations with a strong emphasis on leveraging the **Chapa Payment Gateway**. This integration provides a robust, secure, and locally relevant solution for payment initiation, status tracking, and webhook processing. By utilizing Chapa, this service ensures that property listing payments are processed efficiently, verified reliably, and communicated seamlessly to relevant services within the ecosystem, offering a superior payment experience tailored for the Ethiopian market.

## Features
-   **Chapa Payment Integration**: Seamlessly integrates with the Chapa Payment Gateway for secure and localized payment processing, supporting various local payment methods.
-   **Payment Initiation**: Securely initiates payments through the Chapa payment gateway, generating unique checkout URLs.
-   **Idempotency**: Prevents duplicate payment processing for the same request, ensuring reliable transactions.
-   **Payment Status Tracking**: Monitors and updates the status of payments (PENDING, SUCCESS, FAILED) in real-time.
-   **Chapa Webhook Handling**: Processes real-time payment status updates from Chapa via secure webhooks, ensuring immediate reflection of payment outcomes.
-   **Scheduled Payment Timeout**: Automatically marks pending payments as FAILED after a configurable period, maintaining data accuracy.
-   **Inter-Service Communication**: Integrates with User Management, Property Listing, and Notification services for a cohesive ecosystem.
-   **Authentication & Authorization**: Secures API endpoints using JWT and API keys for robust access control.
-   **Caching**: Utilizes Redis for caching user authentication data to improve performance and reduce load on upstream services.
-   **Rate Limiting**: Implements API rate limiting using Redis to protect against abuse and ensure service stability.
-   **Structured Logging**: Provides detailed, structured logs for better observability, debugging, and monitoring.
-   **Health Checks & Metrics**: Offers endpoints for monitoring service health and operational metrics, ensuring high availability.

## Architecture
The Payment Processing Microservice operates within a broader microservices ecosystem. Below is a C4 Context diagram illustrating its interactions with other key systems.

```mermaid
C4Context
    title System Context for Rent Management System

    System_Ext(User, "User", "End-users interacting with the system")
    System_Ext(Landlord, "Landlord", "Property owners using the system")
    System_Ext(ChapaPaymentGateway, "Chapa Payment Gateway", "External payment processing service")
    System_Ext(Redis, "Redis", "External caching and rate limiting service")

    System(UserManagementService, "User Management Service", "Manages user authentication and profiles")
    System(PropertyListingService, "Property Listing Service", "Manages property listings and approvals")
    System(NotificationService, "Notification Service", "Handles sending notifications to users")
    System(PaymentProcessingMicroservice, "Payment Processing Microservice", "Handles payment initiation, status tracking, and webhooks")

    Rel(User, PaymentProcessingMicroservice, "Initiates payments via")
    Rel(Landlord, PaymentProcessingMicroservice, "Initiates payments via")
    Rel(PaymentProcessingMicroservice, ChapaPaymentGateway, "Initiates and verifies payments with")
    Rel(ChapaPaymentGateway, PaymentProcessingMicroservice, "Sends webhook notifications to")
    Rel(PaymentProcessingMicroservice, UserManagementService, "Verifies user tokens and fetches user details from")
    Rel(PaymentProcessingMicroservice, PropertyListingService, "Notifies about payment status (success/failure)")
    Rel(PaymentProcessingMicroservice, NotificationService, "Sends payment-related notifications via")
    Rel(PaymentProcessingMicroservice, Redis, "Uses for caching and rate limiting")
    Rel(PaymentProcessingMicroservice, UserManagementService, "Proxies authentication requests to")
```

## Technologies Used
-   **FastAPI**: High-performance web framework for building APIs.
-   **SQLAlchemy (Async)**: Asynchronous ORM for interacting with PostgreSQL.
-   **PostgreSQL**: Relational database for storing payment records.
-   **Pydantic**: Data validation and settings management.
-   **Chapa API**: Integration with the Chapa payment gateway.
-   **Redis**: In-memory data store for caching user authentication and API rate limiting.
-   **APScheduler**: For scheduling background tasks, specifically payment timeouts.
-   **httpx**: A fully featured asynchronous HTTP client for making requests to external services.
-   **python-jose**: For JSON Web Token (JWT) handling.
-   **cryptography**: For secure data encryption (Fernet).
-   **structlog**: For structured, machine-readable logging.
-   **Docker**: For containerization and deployment.

## Setup Guide

### Prerequisites
Before you begin, ensure you have the following installed:
-   Python 3.10+
-   Docker and Docker Compose (for local development with services like PostgreSQL and Redis)
-   `pip` (Python package installer)

### Environment Variables
Create a `.env` file in the root directory of the project based on the `.env.example` (which you should create if it doesn't exist).

```
# .env.example
DATABASE_URL="postgresql+asyncpg://user:password@host:port/dbname"
CHAPA_API_KEY="your_chapa_api_key"
CHAPA_SECRET_KEY="your_chapa_secret_key"
CHAPA_WEBHOOK_SECRET="your_chapa_webhook_secret"
JWT_SECRET="your_jwt_secret_key_for_signing_tokens"
USER_MANAGEMENT_URL="http://localhost:8001" # URL of the User Management Service
NOTIFICATION_SERVICE_URL="http://localhost:8002" # URL of the Notification Service
PROPERTY_LISTING_SERVICE_URL="http://localhost:8003" # URL of the Property Listing Service
ENCRYPTION_KEY="your_fernet_encryption_key_32_url_safe_base64_bytes" # Generate with `Fernet.generate_key().decode()`
REDIS_URL="redis://localhost:6379/0"
PAYMENT_SERVICE_API_KEY="your_service_to_service_api_key" # API key for this service to authenticate with others
FRONTEND_REDIRECT_URL="http://localhost:3000/payment-status" # Frontend URL for post-payment redirection
```
**Note**: For `ENCRYPTION_KEY`, you can generate one using `from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())` in a Python console.

### Installation
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/rent-management-system/Rent-management--system--payment-processing-service
    cd Rent-management--system -payment-processing-service
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
    This script will apply the `sql/schema.sql` to your database. Make sure `psql` is available in your PATH or adjust the script accordingly.

### Running the Application
1.  **Start dependent services**: Ensure your PostgreSQL, Redis, User Management, Property Listing, and Notification services are running and accessible as configured in your `.env` file.
2.  **Run the FastAPI application**:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    The `--reload` flag is useful for development as it restarts the server on code changes. For production, remove this flag.

The API documentation will be available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc` (ReDoc).

## API Endpoints

### Authentication
-   **`POST /token`**
    -   **Description**: Logs in a user by proxying the request to the User Management microservice and returns an access token.
    -   **Permissions**: Public
    -   **User Types**: Any authenticated user (via User Management Service)
    -   **Parameters**:
        -   `username` (form data): User's username.
        -   `password` (form data): User's password.
    -   **Responses**:
        -   `200 OK`: Returns JWT access token.
        -   `401 Unauthorized`: Invalid credentials.
        -   `503 Service Unavailable`: User Management service is down.

### Payments
-   **`POST /api/v1/payments/initiate`**
    -   **Description**: Initiates a payment for a property listing through the Chapa gateway. This endpoint is idempotent.
    -   **Permissions**: Authenticated (Owner role via JWT or Service-to-Service via API Key)
    -   **User Types**: Landlord (Owner), Internal Services
    -   **Parameters (Request Body - `PaymentCreate`)**:
        -   `request_id` (UUID): Unique ID for idempotency.
        -   `property_id` (UUID): ID of the property listing.
        -   `user_id` (UUID): ID of the user initiating the payment.
        -   `amount` (float): The fixed amount for the payment (currently hardcoded to 500.00 ETB).
    -   **Responses**:
        -   `202 Accepted`: Payment initiation successful, returns `PaymentResponse` including `checkout_url`.
        -   `400 Bad Request`: Invalid input or Chapa initialization failure.
        -   `401 Unauthorized`: Missing or invalid authentication.
        -   `403 Forbidden`: User not authorized (e.g., not an Owner).
        -   `404 Not Found`: User details not found for service-initiated payments.
        -   `429 Too Many Requests`: Rate limit exceeded.
        -   `500 Internal Server Error`: Unexpected server error.

-   **`GET /api/v1/payments/{payment_id}/status`**
    -   **Description**: Retrieves the current status of a specific payment.
    -   **Permissions**: Authenticated (User who initiated payment or Admin role)
    -   **User Types**: Landlord, Admin
    -   **Parameters (Path)**:
        -   `payment_id` (UUID): The ID of the payment to retrieve.
    -   **Responses**:
        -   `200 OK`: Returns `PaymentResponse` with payment details.
        -   `401 Unauthorized`: Missing or invalid authentication.
        -   `403 Forbidden`: User not authorized to view this payment.
        -   `404 Not Found`: Payment not found.

### Webhooks
-   **`GET/POST /api/v1/webhook/chapa`**
    -   **Description**: Endpoint for Chapa payment gateway to send real-time payment status updates (POST) or for redirecting users after payment (GET).
    -   **Permissions**: Public (Chapa gateway)
    -   **User Types**: N/A (System-to-System)
    -   **Parameters**:
        -   **POST (Request Body)**: Chapa webhook payload containing `tx_ref`, `status`, and `meta` data.
        -   **POST (Header)**: `X-Chapa-Signature` for webhook verification.
        -   **GET (Query Params)**: `trx_ref` and `status` for redirect.
    -   **Responses**:
        -   `200 OK`: Webhook processed successfully.
        -   `400 Bad Request`: Invalid payload or missing parameters.
        -   `401 Unauthorized`: Invalid webhook signature.

### Health Check
-   **`GET /api/v1/health`**
    -   **Description**: Performs a health check on the service, including database and Chapa API connectivity.
    -   **Permissions**: Public
    -   **User Types**: Monitoring Systems
    -   **Responses**:
        -   `200 OK`: Service is healthy.
        -   `503 Service Unavailable`: Service is unhealthy, details provided in response.

### Metrics
-   **`GET /api/v1/metrics`**
    -   **Description**: Returns in-memory operational metrics for the service (e.g., total payments, successful payments, webhook calls).
    -   **Permissions**: Public
    -   **User Types**: Monitoring Systems
    -   **Responses**:
        -   `200 OK`: Returns a JSON object with various metrics.

## Chapa Payment Gateway Integration
This microservice deeply integrates with the **Chapa Payment Gateway**, a leading payment solution tailored for the Ethiopian market. This integration is a cornerstone of the service, offering several key advantages:

-   **Localized Payment Options**: Chapa enables support for various local payment methods, making the payment process accessible and convenient for users in Ethiopia.
-   **Seamless Checkout Experience**: By leveraging Chapa's API, the service provides a smooth and secure checkout flow, redirecting users to Chapa's hosted payment page and handling post-payment redirects back to the frontend.
-   **Real-time Status Updates**: Chapa's robust webhook system allows the microservice to receive instant notifications on payment status changes (success, failure, pending), ensuring that payment records are always up-to-date.
-   **Enhanced Security**: The integration includes webhook signature verification, adding an extra layer of security to ensure that incoming webhook notifications are legitimate and untampered.
-   **Reliable Transaction Verification**: Beyond webhooks, the service actively verifies payment statuses with Chapa's API, providing a double-check mechanism for critical transactions.

This strategic integration with Chapa not only streamlines payment processing but also significantly enhances the user experience by providing a trusted and efficient payment infrastructure.

## Scheduled Tasks
The service includes an asynchronous scheduler (`APScheduler`) to run background tasks:
-   **`timeout_pending_payments`**: Runs every 24 hours. It queries the database for payments with `PENDING` status that were created more than `PAYMENT_TIMEOUT_DAYS` (configured in `.env`) ago and updates their status to `FAILED`. It also attempts to notify the Property Listing Service about these failed payments.

## Inter-Service Communication
This microservice interacts with several other services:

-   **User Management Service**:
    -   **Authentication Proxy**: The `/token` endpoint forwards authentication requests to the User Management Service.
    -   **Token Verification**: During API calls, JWT tokens are verified against the User Management Service.
    -   **User Details Fetch**: When a service initiates a payment, user details are fetched from the User Management Service for Chapa and notification purposes.
-   **Property Listing Service**:
    -   **Payment Confirmation**: After a payment is successfully processed or times out/fails, this service sends a confirmation to the Property Listing Service to update the property's status (e.g., approve listing).
-   **Notification Service**:
    -   **Event Notifications**: Sends notifications to users (e.g., payment initiated, payment successful, payment failed) via the Notification Service. It supports multi-language templates.
-   **Chapa Payment Gateway**:
    -   **Payment Initialization**: Initiates payment transactions and retrieves checkout URLs.
    -   **Payment Verification**: Verifies the status of transactions with Chapa's API.
    -   **Webhook Reception**: Receives real-time updates from Chapa regarding payment status changes.

## Logging
The service uses `structlog` for structured logging. This provides machine-readable logs that are easier to parse, filter, and analyze with log management tools. Logs are output to `stdout` and can be configured for JSON or console rendering.

## Error Handling
-   **HTTPException**: FastAPI's `HTTPException` is used for standard HTTP error responses (e.g., 400 Bad Request, 401 Unauthorized, 404 Not Found).
-   **Retry Mechanism**: The `app.utils.retry.py` module provides an `@async_retry` decorator for resilient communication with external services, handling transient network issues or service unavailability with exponential backoff.
-   **Service Unavailable**: Specific `HTTPException`s are raised when dependent services (User Management, Property Listing, Chapa) are unresponsive.

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