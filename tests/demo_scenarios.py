import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1/properties"

# Replace with actual tokens from your User Management service for testing
VALID_OWNER_JWT = "your_valid_owner_jwt_here" 
NON_OWNER_JWT = "your_valid_non_owner_jwt_here"
INVALID_JWT = "invalid.jwt.token"

HEADERS_OWNER = {"Authorization": f"Bearer {VALID_OWNER_JWT}"}
HEADERS_NON_OWNER = {"Authorization": f"Bearer {NON_OWNER_JWT}"}
HEADERS_INVALID = {"Authorization": f"Bearer {INVALID_JWT}"}


def print_scenario(title, response):
    print(f"\n--- {title} ---")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    except json.JSONDecodeError:
        print(f"Response Body: {response.text}")
    print("---------------------" + "-" * len(title))

def run_demo_scenarios():
    """Runs a series of requests to demonstrate API error handling."""

    # 1. Invalid JWT Scenario
    title = "Scenario 1: Submitting a listing with an Invalid JWT"
    property_data = {"title": "Fail", "description": "...", "location": "...", "price": 0, "amenities": [], "photos": []}
    response = requests.post(f"{BASE_URL}/submit", json=property_data, headers=HEADERS_INVALID)
    print_scenario(title, response)

    # 2. Non-Owner Role Scenario
    title = "Scenario 2: Submitting a listing with a Non-Owner Role"
    response = requests.post(f"{BASE_URL}/submit", json=property_data, headers=HEADERS_NON_OWNER)
    print_scenario(title, response)

    # 3. Failed Payment Approval Scenario (Property Not Found)
    title = "Scenario 3: Approving a non-existent property"
    non_existent_id = "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6"
    approval_data = {"payment_id": "p1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d7"}
    response = requests.post(f"{BASE_URL}/{non_existent_id}/approve", json=approval_data)
    print_scenario(title, response)

    # 4. Validation Error Scenario (e.g., missing 'title')
    title = "Scenario 4: Submitting a listing with missing required fields"
    invalid_property_data = {"description": "...", "location": "...", "price": 1000, "amenities": [], "photos": []}
    response = requests.post(f"{BASE_URL}/submit", json=invalid_property_data, headers=HEADERS_OWNER)
    print_scenario(title, response)

if __name__ == "__main__":
    print("Starting Demo Scenarios...")
    print("NOTE: Replace placeholder JWTs in this script with real ones from your User service.")
    run_demo_scenarios()
