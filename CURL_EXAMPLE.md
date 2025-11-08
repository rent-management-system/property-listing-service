# cURL Example for Submitting a Property

This document provides a template for making a `POST` request to the `/api/v1/properties/submit` endpoint using `curl`.

**Important:**
*   Replace `<YOUR_ACCESS_TOKEN_HERE>` with your actual JWT `access_token`. Ensure there are **no line breaks or extra spaces** within the token string.
*   Modify the JSON data in the `-d` flag with your desired property details.
*   Ensure the URL `http://127.0.0.1:4580` matches the address where your Property Listing Service is running.

```bash
curl -X POST "http://127.0.0.1:4580/api/v1/properties/submit" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMGU5OTA1Mi03YzhkLTQ4ZWUtODAyYS0yODIwYmZiYmE0YWQiLCJyb2xlIjoib3duZXIiLCJlbWFpbCI6Im93bmVyMkBnbWFpbC5jb20iLCJwaG9uZV9udW1iZXIiOiIrMjUxNzQ0MTA0NTM1IiwicHJlZmVycmVkX2xhbmd1YWdlIjoiZW4iLCJleHAiOjE3NjIyNzg0NTEsImlhdCI6MTc2MjI3NzU1MX0.z7b2O8UEBMr8kLFjWDHDkv58XA4POXXe9TNzW3krD9A" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Example Property Title",
    "description": "A detailed description of the property.",
    "location": "Addis Ababa",
    "price": 50000.00,
    "amenities": ["wifi", "parking", "garden"],
    "photos": ["http://example.com/photo1.jpg", "http://example.com/photo2.jpg"]
  }'
```
