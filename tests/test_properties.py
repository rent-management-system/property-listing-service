from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest

# A mock JWT for a user with the 'Owner' role
OWNER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6Ik93bmVyIiwiaWF0IjoxNTE2MjM5MDIyfQ.f4o8_b-hK_TzNxlABf_Y9h6hI5_BfBvNcg_l-gK_b-A"

# A mock JWT for a regular user
USER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6IlVzZXIiLCJpYXQiOjE1MTYyMzkwMjJ9.4oF8-b_hK_TzNxlABf_Y9h6hI5_BfBvNcg_l-gK_b-A"

@pytest.fixture
def mock_auth():
    with patch('app.dependencies.auth.get_user_data') as mock_get_user:
        mock_get_user.return_value = {
            'user_id': 'a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6',
            'role': 'Owner',
            'preferred_language': 'en'
        }
        yield mock_get_user

def test_submit_property_success(client: TestClient, mock_auth):
    """Tests successful property submission by an Owner."""
    headers = {"Authorization": f"Bearer {OWNER_TOKEN}"}
    property_data = {
        "title": "Test Property",
        "description": "A property for testing.",
        "location": "Test Location",
        "price": 1000.00,
        "amenities": ["Test Amenity"],
        "photos": ["test.jpg"]
    }

    response = client.post("/api/v1/properties/submit", json=property_data, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert "property_id" in data
    assert "payment_url" in data

def test_submit_property_not_owner(client: TestClient):
    """Tests that a non-owner cannot submit a property."""
    # This mock simulates the user service returning a 'User' role
    with patch('app.dependencies.auth.get_user_data') as mock_get_user:
        mock_get_user.return_value = {
            'user_id': 'some_user_id',
            'role': 'User' # Not an owner
        }
        headers = {"Authorization": f"Bearer {USER_TOKEN}"}
        property_data = {
            "title": "Test Property",
            "description": "A property for testing.",
            "location": "Test Location",
            "price": 1000.00,
            "amenities": [],
            "photos": []
        }

        response = client.post("/api/v1/properties/submit", json=property_data, headers=headers)

        assert response.status_code == 403
        assert response.json()["detail"] == "The user is not an Owner"

def test_get_all_properties_public(client: TestClient):
    """Tests that the public endpoint for approved properties is accessible."""
    # This test doesn't require authentication
    response = client.get("/api/v1/properties")
    assert response.status_code == 200
    # The response should be a list, even if it's empty
    assert isinstance(response.json(), list)
