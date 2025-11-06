from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest
import io
import uuid

# A mock JWT for a user with the 'Owner' role
OWNER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6Ik93bmVyIiwiaWF0IjoxNTE2MjM5MDIyfQ.f4o8_b-hK_TzNxlABf_Y9h6hI5_BfBvNcg_l-gK_b-A"

# A mock JWT for a regular user
USER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6IlVzZXIiLCJpYXQiOjE1MTYyMzkwMjJ9.4oF8-b_hK_TzNxlABf_Y9h6hI5_BfBvNcg_l-gK_b-A"

@pytest.fixture
def mock_auth():
    with patch('app.dependencies.auth.get_user_data') as mock_get_user, \
         patch('app.dependencies.auth.jwt.decode') as mock_jwt_decode:
        mock_get_user.return_value = {
            'user_id': uuid.UUID('a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6'),
            'role': 'Owner',
            'preferred_language': 'en'
        }
        mock_jwt_decode.return_value = {
            'sub': 'a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6'
        }
        yield mock_get_user, mock_jwt_decode

def test_submit_property_success(client: TestClient, mock_auth):
    """Tests successful property submission by an Owner."""
    headers = {"Authorization": f"Bearer {OWNER_TOKEN}"}
    property_data = {
        "title": "Test Property",
        "description": "A property for testing.",
        "location": "Test Location",
        "price": "1000.00",
        "amenities": ["Test Amenity"],
    }
    image_content = b"fake image data"
    image = io.BytesIO(image_content)
    image.name = "test_image.jpg"

    response = client.post(
        "/api/v1/properties/submit", 
        data=property_data, 
        files={"file": (image.name, image, "image/jpeg")},
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert "property_id" in data
    assert "payment_url" in data

def test_submit_property_not_owner(client: TestClient, mock_auth):
    """Tests that a non-owner cannot submit a property."""
    mock_get_user, _ = mock_auth
    mock_get_user.return_value = {
        'user_id': 'some_user_id',
        'role': 'User' # Not an owner
    }
    headers = {"Authorization": f"Bearer {USER_TOKEN}"}
    property_data = {
        "title": "Test Property",
        "description": "A property for testing.",
        "location": "Test Location",
        "price": "1000.00",
        "amenities": [],
    }
    image_content = b"fake image data"
    image = io.BytesIO(image_content)
    image.name = "test_image.jpg"

    response = client.post(
        "/api/v1/properties/submit", 
        data=property_data, 
        files={"file": (image.name, image, "image/jpeg")},
        headers=headers
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "The user is not an Owner"

def test_get_all_properties_public(client: TestClient):
    """Tests that the public endpoint for approved properties is accessible."""
    # This test doesn't require authentication
    response = client.get("/api/v1/properties")
    assert response.status_code == 200
    # The response should be a list, even if it's empty
    assert isinstance(response.json(), list)

def test_get_metrics(client: TestClient):
    """Tests the metrics endpoint."""
    response = client.get("/api/v1/properties/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_listings" in data
    assert "pending" in data
    assert "approved" in data
    assert "rejected" in data

def test_full_text_search(client: TestClient):
    """Tests the full-text search functionality."""
    # This test assumes some data has been seeded
    response = client.get("/api/v1/properties?search=apartment")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_pagination(client: TestClient):
    """Tests the pagination functionality."""
    response = client.get("/api/v1/properties?offset=0&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5
