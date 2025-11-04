# Property Listing Service API Documentation

This document provides a detailed guide for frontend developers on how to interact with the Property Listing Service API.

**Base URL:** All endpoints are prefixed with `/api/v1/properties`.

**Authentication:** Endpoints that require authentication expect a `Bearer` token in the `Authorization` header. Tokens are obtained from the User Management Service.

---

# Integration with External Services

For the entire platform to function, the frontend application must interact with multiple backend services. This service (Property Listing) is just one piece. This section explains how the frontend should handle interactions with other key services.

## 1. User Management Service

This service handles everything related to users, including registration, login, and profile management. The frontend will interact with it directly.

- **Service URL:** `https://rent-managment-system-user-magt.onrender.com/api/v1`

### Key Frontend Interaction: User Login

- **Endpoint:** `POST /auth/login`
- **Description:** The frontend must provide a login form where the user can enter their email and password. This form will send a request directly to the User Management Service.

#### What the Frontend Sends:

A standard HTML form POST request with the following fields:
- `username`: The user's email address.
- `password`: The user's password.

#### What the Frontend Receives (on Success):

A JSON response containing the user's session tokens.

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Frontend Responsibility:

1.  **Store Tokens:** Securely store the `access_token` and `refresh_token`.
2.  **Send Access Token:** For any authenticated request to the **Property Listing Service**, the frontend must include the `access_token` in the `Authorization` header.
    - **Example:** `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
3.  **Refresh Token:** When the `access_token` expires, the frontend should use the `refresh_token` to get a new one from the User Management Service's `/auth/refresh` endpoint.

## 2. Payment Service

This service handles the processing of listing fees. The frontend's interaction with it is very simple.

### Key Frontend Interaction: Redirect to Payment

- **Trigger:** After an "Owner" user submits a new property, the Property Listing Service responds with a `payment_url`.

#### What the Frontend Does:

The frontend's only responsibility is to perform a full-page redirect to the `payment_url` it receives.

- **Example Code:** `window.location.href = response.payment_url;`

### Frontend Responsibility:

1.  **Redirect:** Immediately navigate the user to the payment gateway.
2.  **Handle Return:** Prepare "success" and "cancel" pages in the frontend application. The Payment Service will redirect the user back to one of these pages after the transaction is complete or aborted. The actual approval of the property is handled between the Payment and Property services on the backend.

---

# API Endpoint Details

## 1. Public Endpoints

These endpoints are publicly accessible and do not require authentication.

### Get All Approved Properties

Retrieves a paginated and filterable list of all properties that have been approved for public viewing.

- **Method:** `GET`
- **Path:** `/`
- **Permissions:** Public

#### Query Parameters

| Parameter   | Type            | Description                                          |
|-------------|-----------------|------------------------------------------------------|
| `location`  | `string`        | (Optional) Filter properties by location (case-insensitive search). |
| `min_price` | `number`        | (Optional) Filter for properties with a price greater than or equal to this value. |
| `max_price` | `number`        | (Optional) Filter for properties with a price less than or equal to this value. |
| `amenities` | `array[string]` | (Optional) Filter for properties that have all the specified amenities. Example: `?amenities=wifi&amenities=pool` |
| `search`    | `string`        | (Optional) Perform a full-text search across property titles and descriptions. |
| `offset`    | `integer`       | (Optional) The number of items to skip for pagination. Default: `0`. |
| `limit`     | `integer`       | (Optional) The maximum number of items to return. Default: `20`. |

#### Success Response (200 OK)

An array of property objects.

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

These endpoints are for users with the **"Owner"** role.

### Submit a New Property

Submits a new property for review. The property will initially have a `PENDING` status.

- **Method:** `POST`
- **Path:** `/submit`
- **Permissions:** `Owner`

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

#### Success Response (201 Created)

Returns the new property's ID, its status, and a mock payment URL to continue the listing process.

```json
{
  "property_id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210",
  "status": "PENDING",
  "payment_url": "http://payment-service.example.com/payments/initiate/f0e9d8c7-b6a5-4321-fedc-ba9876543210"
}
```

#### Error Responses

- `401 Unauthorized`: If the user is not logged in.
- `403 Forbidden`: If the user's role is not "Owner".

---

## 3. Authenticated User Endpoints

These endpoints require a valid user session.

### Get a Specific Property by ID

Retrieves the full, detailed information for a single property.

- **Method:** `GET`
- **Path:** `/{id}`
- **Permissions:** `Owner` of the property or `Admin`.

#### Path Parameters

| Parameter | Type   | Description                  |
|-----------|--------|------------------------------|
| `id`      | `uuid` | The unique ID of the property. |

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

#### Error Responses

- `401 Unauthorized`: If the user is not logged in.
- `403 Forbidden`: If the user is not the owner of the property and is not an Admin.
- `404 Not Found`: If a property with the specified ID does not exist.

---

## 4. Service-to-Service Endpoints

These endpoints are designed to be called by other backend services, not directly by a frontend client.

### Approve a Property

Marks a property as `APPROVED`. This is intended to be called by the Payment Service after a successful listing fee payment.

- **Method:** `POST`
- **Path:** `/{id}/approve`
- **Permissions:** None (relies on network security).

#### Path Parameters

| Parameter | Type   | Description                  |
|-----------|--------|------------------------------|
| `id`      | `uuid` | The unique ID of the property. |

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

#### Error Responses

- `404 Not Found`: If a property with the specified ID does not exist.

---

## 5. Admin / Metrics Endpoints

### Get Listing Metrics

Retrieves a count of properties by status.

- **Method:** `GET`
- **Path:** `/metrics`
- **Permissions:** Public (can be restricted to `Admin` in a future update if needed).

#### Success Response (200 OK)

```json
{
  "total_listings": 150,
  "pending": 10,
  "approved": 135,
  "rejected": 5
}
```

---

# Frontend Implementation Guide

This section provides suggestions for frontend features based on the available API endpoints.

## 1. Core User Flow

- **Authentication:** Implement a full authentication flow (Login, Logout, Registration pages) that communicates with the User Management Service. User JWTs must be stored securely (e.g., in an HttpOnly cookie or secure local storage) and sent with every request to protected endpoints in this service.
- **Role-Based UI:** The UI should dynamically change based on the user's role (`Owner`, `Admin`, or a regular user). For example, only show the "Submit Property" button to users with the "Owner" role.

## 2. Property Browsing and Searching

- **Main Property Listings Page:** Create a page that uses the `GET /` endpoint to display all approved properties.
- **Search and Filtering:** Implement UI controls (search bars, dropdowns, sliders) that map to the available query parameters (`search`, `location`, `min_price`, `max_price`, `amenities`). As the user interacts with these controls, re-fetch the data from the API.
- **Pagination:** Add "Next" and "Previous" buttons or page numbers to navigate through the list of properties using the `offset` and `limit` parameters.
- **Property Detail Page:** When a user clicks on a property from the list, navigate to a details page that shows more information. Note that this public view might be different from the detailed view an owner sees.

## 3. Owner Dashboard

- **Submit Property Form:** Create a comprehensive form for the `POST /submit` endpoint. This should include fields for all the required data, including a way to manage a list of photo URLs and amenities.
- **Payment Redirection:** After an owner successfully submits a property, the API returns a `payment_url`. The frontend **must** redirect the user to this URL to complete the payment. You will also need to design a "payment success" or "callback" page for when the user returns from the payment gateway.
- **"My Properties" Page:** Create a dashboard page for owners to see a list of all the properties they have submitted.
    - This would involve fetching the user's own properties (the API currently only has a public `GET /` and a private `GET /{id}`). A new endpoint like `GET /my-properties` might be needed in the future for efficiency.
    - For now, an owner can view their properties one by one if they have the IDs, using the `GET /{id}` endpoint.
    - Display the `status` of each property (`PENDING`, `APPROVED`, `REJECTED`) clearly.

## 4. Admin Features

- **Metrics Dashboard:** Use the `GET /metrics` endpoint to build a simple dashboard for administrators to see the overall health of the property listing system.
- **Property Management:** An admin should be able to view any property's details using their admin privileges on the `GET /{id}` endpoint. Future enhancements could include endpoints for admins to approve/reject properties directly.
