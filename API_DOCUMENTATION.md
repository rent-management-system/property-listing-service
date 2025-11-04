# Property Listing Service API Documentation

This document provides a detailed guide for frontend developers on how to interact with the Property Listing Service API.

**Base URL:** `https://property-listing-service.onrender.com/api/v1/properties`

**Authentication:** Endpoints that require authentication expect a `Bearer` token in the `Authorization` header. Tokens are obtained from the User Management Service.

---

# Frontend Quick Start: Submitting a Property

This is the most common end-to-end workflow for a user listing a new property.

1.  **User Login:** The user enters their credentials into a login form. The frontend sends these directly to the User Management Service.
    - **API Call:** `POST https://rent-managment-system-user-magt.onrender.com/api/v1/auth/login`

2.  **Receive & Store Token:** The User Management Service returns an `access_token`. The frontend must store this securely.

3.  **Submit Property:** The user, who must have the "Owner" role, fills out and submits the new property form. The frontend sends the property data to this service, including the stored token in the header.
    - **API Call:** `POST /api/v1/properties/submit`
    - **Header:** `Authorization: Bearer <your_access_token>`

4.  **Receive Payment URL:** The Property Listing Service responds with a `payment_url`.

5.  **Redirect to Payment:** The frontend immediately redirects the user's browser to this `payment_url`.
    - **Example Code:** `window.location.href = response.payment_url;`

6.  **Handle Return from Payment:** The user completes (or cancels) the payment and is redirected back to a "success" or "cancel" page on the frontend application. The backend will handle the final property approval via a separate webhook call from the payment service.

---

# API Endpoint Details

## 1. Public Endpoints

### Get All Approved Properties

Retrieves a paginated and filterable list of all properties that have been approved for public viewing.

-   **Method:** `GET`
-   **Path:** `/`
-   **Permissions:** Public

#### Query Parameters

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `location` | `string` | (Optional) Filter properties by location (case-insensitive search). |
| `min_price` | `number` | (Optional) Filter for properties with a price greater than or equal to this value. |
| `max_price` | `number` | (Optional) Filter for properties with a price less than or equal to this value. |
| `amenities` | `array[string]` | (Optional) Filter for properties that have all the specified amenities. Example: `?amenities=wifi&amenities=pool` |
| `search` | `string` | (Optional) Perform a full-text search across property titles and descriptions. |
| `offset` | `integer` | (Optional) The number of items to skip for pagination. Default: `0`. |
| `limit` | `integer` | (Optional) The maximum number of items to return. Default: `20`. |

#### Example Request

```bash
curl -X GET "https://property-listing-service.onrender.com/api/v1/properties?location=addis%20ababa&limit=5"
```

#### Success Response (200 OK)

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "title": "Cozy Downtown Apartment",
    "location": "Addis Ababa",
    "price": 1500.00,
    "amenities": ["wifi", "kitchen"],
    "status": "APPROVED"
  }
]
```

---

## 2. Property Owner Endpoints

### Submit a New Property

Submits a new property for review. The property will initially have a `PENDING` status.

-   **Method:** `POST`
-   **Path:** `/submit`
-   **Permissions:** `Owner`

#### Request Body

```json
{
  "title": "Spacious Villa with Garden",
  "description": "A beautiful villa perfect for families, with a large private garden.",
  "location": "Bole, Addis Ababa",
  "price": 4500.00,
  "amenities": ["garden", "parking", "security"],
  "photos": ["url_to_photo1.jpg", "url_to_photo2.jpg"]
}
```

#### Example Request

```bash
curl -X POST "https://property-listing-service.onrender.com/api/v1/properties/submit" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My New Place",
    "description": "A great place to live.",
    "location": "Bole",
    "price": 2000,
    "amenities": ["wifi", "parking"],
    "photos": []
  }'
```

#### Success Response (201 Created)

```json
{
  "property_id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210",
  "status": "PENDING",
  "payment_url": "http://payment-service.example.com/payments/initiate/f0e9d8c7-b6a5-4321-fedc-ba9876543210"
}
```

---

## 3. Authenticated User Endpoints

### Get a Specific Property by ID

Retrieves the full, detailed information for a single property.

-   **Method:** `GET`
-   **Path:** `/{id}`
-   **Permissions:** `Owner` of the property or `Admin`.

#### Path Parameters

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` | The unique ID of the property. |

#### Example Request

```bash
curl -X GET "https://property-listing-service.onrender.com/api/v1/properties/YOUR_PROPERTY_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Success Response (200 OK)

```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "title": "Cozy Downtown Apartment",
  "description": "A small but well-furnished apartment in the heart of the city.",
  "location": "Addis Ababa",
  "price": 1500.00,
  "amenities": ["wifi", "kitchen"],
  "photos": ["url_to_photo1.jpg"],
  "status": "APPROVED"
}
```

---

## 4. Service-to-Service Endpoints

### Approve a Property

Marks a property as `APPROVED`. This is intended to be called by the Payment Service after a successful listing fee payment. **It should not be called by the frontend.**

-   **Method:** `POST`
-   **Path:** `/{id}/approve`
-   **Permissions:** None (relies on network security).

#### Path Parameters

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `id` | `uuid` | The unique ID of the property. |

#### Request Body

```json
{
  "payment_id": "c9b8a7d6-e5f4-3210-abcd-ef1234567890"
}
```

#### Success Response (200 OK)

```json
{
  "status": "success"
}
```

---

## 5. Admin / Metrics Endpoints

### Get Listing Metrics

Retrieves a count of properties by status.

-   **Method:** `GET`
-   **Path:** `/metrics`
-   **Permissions:** Public

#### Example Request

```bash
curl -X GET "https://property-listing-service.onrender.com/api/v1/properties/metrics"
```

#### Success Response (200 OK)

```json
{
  "total_listings": 150,
  "pending": 10,
  "approved": 135,
  "rejected": 5
}
```