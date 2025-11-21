# Property Listing Service API Documentation

This document provides a detailed guide for frontend developers on how to interact with the Property Listing Service API.

**Base URL:** `https://property-listing-service.onrender.com/api/v1`

**Authentication:** Endpoints that require authentication expect a `Bearer` token in the `Authorization` header. Tokens are obtained from the User Management Service.

---

# Frontend Quick Start: Submitting a Property

This is the most common end-to-end workflow for a user listing a new property.

1.  **User Login:** The user enters their credentials into a login form. The frontend sends these directly to the User Management Service.
    - **API Call:** `POST https://rent-managment-system-user-magt.onrender.com/api/v1/auth/login`

2.  **Receive & Store Token:** The User Management Service returns an `access_token`. The frontend must store this securely.

3.  **Submit Property:** The user, who must have the "Owner" role, fills out and submits the new property form, including an image file. The frontend sends the property data as `multipart/form-data` to this service, including the stored token in the header.
    - **API Call:** `POST /properties/submit`
    - **Header:** `Authorization: Bearer <your_access_token>`

4.  **Receive Payment Initiation Response:** The Property Listing Service responds with details to initiate payment, including a `checkout_url`.

5.  **Redirect to Payment:** The frontend immediately redirects the user's browser to this `checkout_url`.
    - **Example Code:** `window.location.href = response.checkout_url;`

6.  **Handle Return from Payment:** The user completes (or cancels) the payment and is redirected back to a "success" or "cancel" page on the frontend application. The backend will handle the final property approval via a separate webhook call from the payment service.

---

# API Endpoint Details

## 1. Public Endpoints

### Get All Approved Properties

Retrieves a paginated and filterable list of all properties that have been approved for public viewing.

-   **Method:** `GET`
-   **Path:** `/properties`
-   **Permissions:** Public

#### Query Parameters

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `location` | `string` | (Optional) Filter properties by location (case-insensitive search). |
| `min_price` | `number` | (Optional) Filter for properties with a price greater than or equal to this value. |
| `max_price` | `number` | (Optional) Filter for properties with a price less than or equal to this value. |
| `amenities` | `array[string]` | (Optional) Filter for properties that have all the specified amenities. Example: `?amenities=wifi&amenities=pool` |
| `house_type` | `string` | (Optional) Filter properties by house type (e.g., `apartment`, `villa`). |
| `search` | `string` | (Optional) Perform a full-text search across property titles and descriptions. |
| `offset` | `integer` | (Optional) The number of items to skip for pagination. Default: `0`. |
| `limit` | `integer` | (Optional) The maximum number of items to return. Default: `20`. |

#### Example Request

```bash
curl -X GET "https://property-listing-service.onrender.com/api/v1/properties?location=addis%20ababa&house_type=apartment&limit=5"
```

#### Success Response (200 OK)

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "title": "Cozy Downtown Apartment",
    "description": "A small but well-furnished apartment in the heart of the city.",
    "location": "Addis Ababa",
    "price": 1500.00,
    "house_type": "apartment",
    "amenities": ["wifi", "kitchen"],
    "photos": ["http://example.com/image1.jpg"],
    "bedrooms": 2,
    "bathrooms": 1,
    "area_sqm": 75,
    "status": "APPROVED",
    "payment_status": "SUCCESS",
    "approval_timestamp": "2023-10-27T10:00:00Z",
    "lat": 9.005401,
    "lon": 38.790374
  }
]
```

---

## 2. Property Owner Endpoints

### Submit a New Property

Submits a new property for review. The property will initially have a `PENDING` status and `PENDING` payment status. This endpoint expects `multipart/form-data` due to file upload.

-   **Method:** `POST`
-   **Path:** `/properties/submit`
-   **Permissions:** `Owner`

#### Form Data Parameters

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `title` | `string` | The title of the property. |
| `description` | `string` | A detailed description of the property. |
| `location` | `string` | The physical location of the property. |
| `price` | `number` | The price of the property. |
| `house_type` | `string` | The type of house (e.g., `apartment`, `villa`). See `HouseType` enum for valid values. |
| `amenities` | `array[string]` | A list of amenities (e.g., `["WiFi", "Parking"]`). |
| `file` | `file` | The main image file for the property. |
| `bedrooms` | `integer` | (Optional) Number of bedrooms. |
| `bathrooms` | `integer` | (Optional) Number of bathrooms. |
| `area_sqm` | `number` | (Optional) Total area in square meters. |

#### Example Request

```bash
curl -X POST "https://property-listing-service.onrender.com/api/v1/properties/submit" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "title=Spacious Villa" \
  -F "description=A beautiful villa with a large garden." \
  -F "location=Bole, Addis Ababa" \
  -F "price=4500.00" \
  -F "house_type=villa" \
  -F "amenities=garden" \
  -F "amenities=parking" \
  -F "bedrooms=4" \
  -F "bathrooms=3" \
  -F "area_sqm=220" \
  -F "file=@/path/to/your/image.jpg;type=image/jpeg"
```

#### Success Response (201 Created)

```json
{
  "property_id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210",
  "status": "PENDING"
}
```

### Get My Properties

Retrieves all properties owned by the currently authenticated user, excluding soft-deleted ones.

-   **Method:** `GET`
-   **Path:** `/properties/my-properties`
-   **Permissions:** `Owner`

#### Example Request

```bash
curl -X GET "https://property-listing-service.onrender.com/api/v1/properties/my-properties" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Success Response (200 OK)

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "title": "My Apartment",
    "description": "...",
    "location": "...",
    "price": 1200.00,
    "house_type": "apartment",
    "amenities": ["wifi"],
    "photos": ["http://example.com/image1.jpg"],
    "bedrooms": 2,
    "bathrooms": 1,
    "area_sqm": 70,
    "status": "PENDING",
    "payment_status": "PENDING",
    "approval_timestamp": null,
    "lat": 9.005401,
    "lon": 38.790374
  }
]
```

### Update Property

Updates an existing property owned by the authenticated user. Only the owner can update their properties.

-   **Method:** `PUT`
-   **Path:** `/properties/{property_id}`
-   **Permissions:** `Owner` (of the specific property)

#### Path Parameters

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `property_id` | `uuid` | The unique ID of the property to update. |

#### Request Body

```json
{
  "title": "Updated Property Title",
  "description": "This is an updated description.",
  "price": 5000.00,
  "amenities": ["new amenity", "another amenity"],
  "bedrooms": 3,
  "bathrooms": 2,
  "area_sqm": 120
}
```

#### Example Request

```bash
curl -X PUT "https://property-listing-service.onrender.com/api/v1/properties/YOUR_PROPERTY_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Updated Place",
    "price": 2500
  }'
```

#### Success Response (200 OK)

```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "title": "My Updated Place",
  "description": "A great place to live.",
  "location": "Bole",
  "price": 2500.00,
  "house_type": "apartment",
  "amenities": ["wifi", "parking"],
  "photos": ["http://example.com/image1.jpg"],
  "bedrooms": 3,
  "bathrooms": 2,
  "area_sqm": 120,
  "status": "PENDING",
  "payment_status": "PENDING",
  "approval_timestamp": null,
  "lat": 9.005401,
  "lon": 38.790374
}
```

### Delete Property (Soft Delete)

Soft deletes a property by changing its status to `DELETED`. Only the owner can delete their properties.

-   **Method:** `DELETE`
-   **Path:** `/properties/{property_id}`
-   **Permissions:** `Owner` (of the specific property)

#### Path Parameters

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `property_id` | `uuid` | The unique ID of the property to delete. |

#### Example Request

```bash
curl -X DELETE "https://property-listing-service.onrender.com/api/v1/properties/YOUR_PROPERTY_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Success Response (204 No Content)

### Reserve Property

Marks an `APPROVED` property as `RESERVED`. Only the owner can reserve their properties.

-   **Method:** `PATCH`
-   **Path:** `/properties/{property_id}/reserve`
-   **Permissions:** `Owner` (of the specific property)

#### Path Parameters

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `property_id` | `uuid` | The unique ID of the property to reserve. |

#### Example Request

```bash
curl -X PATCH "https://property-listing-service.onrender.com/api/v1/properties/YOUR_PROPERTY_ID/reserve" \
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
  "house_type": "apartment",
  "amenities": ["wifi", "kitchen"],
  "photos": ["http://example.com/image1.jpg"],
  "status": "RESERVED",
  "payment_status": "SUCCESS",
  "approval_timestamp": "2023-10-27T10:00:00Z",
  "lat": 9.005401,
  "lon": 38.790374
}
```

### Unreserve Property

Changes a property's status from `RESERVED` back to `APPROVED`. Only the owner can unreserve their properties.

-   **Method:** `PATCH`
-   **Path:** `/properties/{property_id}/unreserve`
-   **Permissions:** `Owner` (of the specific property)

#### Path Parameters

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `property_id` | `uuid` | The unique ID of the property to unreserve. |

#### Example Request

```bash
curl -X PATCH "https://property-listing-service.onrender.com/api/v1/properties/YOUR_PROPERTY_ID/unreserve" \
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
  "house_type": "apartment",
    "amenities": ["wifi", "kitchen"],
    "photos": ["http://example.com/image1.jpg"],
    "status": "APPROVED",
    "payment_status": "SUCCESS",
    "approval_timestamp": "2023-10-27T10:00:00Z",
    "lat": 9.005401,
    "lon": 38.790374
}
```

### Approve and Pay for Property

Initiates the payment process for a `PENDING` property. This endpoint will return a `checkout_url` to which the frontend should redirect the user. The property's status will remain `PENDING` until the payment is confirmed via webhook.

-   **Method:** `PATCH`
-   **Path:** `/properties/{property_id}/approve-and-pay`
-   **Permissions:** `Owner` (of the specific property)

#### Path Parameters

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `property_id` | `uuid` | The unique ID of the property to approve and pay for. |

#### Example Request

```bash
curl -X PATCH "https://property-listing-service.onrender.com/api/v1/properties/YOUR_PROPERTY_ID/approve-and-pay" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Success Response (200 OK)

```json
{
  "property_id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210",
  "status": "PENDING",
  "payment_id": "p1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d7",
  "chapa_tx_ref": "chapa-tx-12345",
  "checkout_url": "https://api.chapa.co/v1/checkout/url/chapa-tx-12345"
}
```

---

## 4. Service-to-Service Endpoints

### Payment Confirmation Webhook

Receives payment confirmation from the Payment Processing Service. This endpoint updates the property's payment status and, if successful, approves the property. **This is an internal webhook and should not be called by the frontend.**

-   **Method:** `POST`
-   **Path:** `/payments/confirm`
-   **Permissions:** Requires `X-API-Key` header with `PROPERTY_WEBHOOK_API_KEY`.

#### Request Body

```json
{
  "property_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "payment_id": "c9b8a7d6-e5f4-3210-abcd-ef1234567890",
  "status": "SUCCESS",
  "tx_ref": "chapa-tx-12345",
  "error_message": null
}
```

#### Example Request

```bash
curl -X POST "https://property-listing-service.onrender.com/api/v1/payments/confirm" \
  -H "X-API-Key: YOUR_PROPERTY_WEBHOOK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "payment_id": "c9b8a7d6-e5f4-3210-abcd-ef1234567890",
    "status": "SUCCESS"
  }'
```

#### Success Response (200 OK)

```json
{
  "status": "received",
  "property_status": "APPROVED",
  "payment_status": "SUCCESS"
}
```

---

## 5. Admin / Metrics Endpoints

### Get Listing Metrics

Retrieves a count of properties by status.

-   **Method:** `GET`
-   **Path:** `/properties/metrics`
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