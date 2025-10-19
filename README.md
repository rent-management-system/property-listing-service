# Property Listing Microservice

This microservice handles property listings for a Rental Management System. It's designed for an Ethiopian market, with a pay-per-post model for landlords (Owners).

## Features

- **Pay-Per-Post**: Owners pay a one-time fee to submit a listing.
- **Verification Workflow**: Listings are `PENDING` until payment is confirmed, then become `APPROVED`.
- **Search and Filtering**: Tenants can search for `APPROVED` listings by location, price, and amenities.
- **Multilingual Support**: Notifications can be sent in English, Amharic, or Afaan Oromo based on user preference.
- **Secure**: Implements JWT authentication, input validation, and rate limiting.
- **Scalable**: Built with FastAPI and async database queries for high performance.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with `asyncpg`
- **Authentication**: JWT
- **Deployment**: Docker, AWS ECS/Fargate

## Folder Structure

```
/
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
├── sql/
│   ├── schema.sql
│   └── seed.sql
├── app/
│   ├── main.py
│   ├── config.py
│   ├── core/
│   ├── dependencies/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── tests/
└── migrate.sh
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd property-listing-service
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the database:**
    - Ensure you have PostgreSQL running.
    - Create a new database.
    - Copy `.env.example` to `.env` and update the `DATABASE_URL` and other variables.
    ```bash
    cp .env.example .env
    # Edit .env with your details
    ```

5.  **Run database migrations and seed data:**
    ```bash
    chmod +x migrate.sh
    ./migrate.sh
    ```

6.  **Run the application:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The service will be available at `http://127.0.0.1:8000`.

## API Endpoints

### 1. Submit a Property Listing

- **Endpoint**: `POST /api/v1/properties/submit`
- **Role**: Owner
- **Description**: Submits a new property listing. The status is set to `PENDING`, and a payment link is generated.
- **Headers**: `Authorization: Bearer <JWT>`

**Request Body**:
```json
{
  "title": "Cozy Apartment in Bole",
  "description": "A beautiful one-bedroom apartment located in the heart of Bole, Addis Ababa.",
  "location": "Bole, Addis Ababa",
  "price": 15000.00,
  "amenities": ["WiFi", "Parking", "Security"],
  "photos": ["http://example.com/photo1.jpg", "http://example.com/photo2.jpg"]
}
```

**Success Response (201)**:
```json
{
  "property_id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
  "status": "PENDING",
  "payment_url": "https://checkout.chapa.co/checkout/payment/some-token"
}
```

### 2. Approve a Property Listing

- **Endpoint**: `POST /api/v1/properties/{id}/approve`
- **Role**: Called by the Payment Processing service.
- **Description**: Approves a listing after successful payment verification.

**Request Body**:
```json
{
  "payment_id": "p1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d7"
}
```

**Success Response (200)**:
```json
{
  "status": "success"
}
```

### 3. Get a Single Property

- **Endpoint**: `GET /api/v1/properties/{id}`
- **Role**: Owner (own listing) or Admin.
- **Description**: Retrieves the full details of a single property.
- **Headers**: `Authorization: Bearer <JWT>`

**Success Response (200)**:
```json
{
  "id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
  "title": "Cozy Apartment in Bole",
  "description": "A beautiful one-bedroom apartment...",
  "location": "Bole, Addis Ababa",
  "price": 15000.00,
  "amenities": ["WiFi", "Parking", "Security"],
  "photos": ["http://example.com/photo1.jpg"],
  "status": "APPROVED"
}
```

### 4. Get All Properties (Public Search)

- **Endpoint**: `GET /api/v1/properties`
- **Role**: Public
- **Description**: Retrieves all `APPROVED` listings. Supports filtering.

**Query Parameters**:
- `location` (str): Filter by location (e.g., `?location=Bole`).
- `min_price` (Decimal): Filter by minimum price.
- `max_price` (Decimal): Filter by maximum price.
- `amenities` (list[str]): Filter by amenities (e.g., `?amenities=WiFi&amenities=Parking`).

**Success Response (200)**:
```json
[
  {
    "id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
    "title": "Cozy Apartment in Bole",
    "location": "Bole, Addis Ababa",
    "price": 15000.00,
    "amenities": ["WiFi", "Parking", "Security"],
    "status": "APPROVED"
  }
]
```

## Demo Walkthrough (cURL)

1.  **Submit a Listing (as an Owner)**:
    *Replace `<your-jwt>` with a valid JWT for an Owner.*
    ```bash
    curl -X POST http://127.0.0.1:8000/api/v1/properties/submit \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <your-jwt>" \
    -d '{
      "title": "Spacious Villa in CMC",
      "description": "A family-friendly villa with a garden.",
      "location": "CMC, Addis Ababa",
      "price": 45000.00,
      "amenities": ["Garden", "Parking", "24/7 Water"],
      "photos": ["http://example.com/villa.jpg"]
    }'
    ```

2.  **Approve the Listing (simulated callback from Payment Service)**:
    *Replace `{property_id}` with the ID from the previous step.*
    ```bash
    curl -X POST http://127.0.0.1:8000/api/v1/properties/{property_id}/approve \
    -H "Content-Type: application/json" \
    -d '{
      "payment_id": "..."
    }'
    ```

3.  **View All Approved Listings (Public)**:
    ```bash
    curl http://127.0.0.1:8000/api/v1/properties?location=CMC
    ```

```