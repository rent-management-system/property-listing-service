import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4
from decimal import Decimal

from app.config import settings
from app.models.property import Property, PropertyStatus

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_owner_user():
    return {"user_id": uuid4(), "role": "owner"}

@pytest.fixture
def mock_property_data():
    return {
        "title": "Test Property",
        "description": "A nice place",
        "location": "Test Location",
        "price": "1000.00",
        "house_type": "apartment",
        "amenities": ["WiFi", "Parking"],
    }

@patch("app.routers.properties.upload_file_to_object_storage", return_value="http://fake.url/image.jpg")
@patch("app.routers.properties.geocode_location_with_fallback", return_value={"lat": 9.0, "lon": 38.0})
@patch("app.dependencies.auth.get_current_owner")
class TestSubmitProperty:
    async def test_submit_success(
        self, mock_get_owner, mock_geocode, mock_upload, client: TestClient, mock_owner_user, mock_property_data
    ):
        mock_get_owner.return_value = mock_owner_user
        fake_payment_id = uuid4()

        with patch("app.services.payment_service.initiate_payment", return_value=fake_payment_id) as mock_initiate_payment:
            files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
            response = client.post(
                "/api/v1/properties/submit",
                data=mock_property_data,
                files=files,
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "PENDING"
            assert data["payment_id"] == str(fake_payment_id)
            
            mock_initiate_payment.assert_called_once()
            # Further checks can be added for the arguments of the call

    async def test_submit_payment_initiation_fails(
        self, mock_get_owner, mock_geocode, mock_upload, client: TestClient, mock_owner_user, mock_property_data
    ):
        mock_get_owner.return_value = mock_owner_user

        with patch("app.services.payment_service.initiate_payment", side_effect=Exception("Payment service timeout")) as mock_initiate_payment:
            files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
            response = client.post(
                "/api/v1/properties/submit",
                data=mock_property_data,
                files=files,
            )

            assert response.status_code == 503
            assert response.json()["detail"] == "Payment service is currently unavailable. Please try again later."
            mock_initiate_payment.assert_called_once()


class TestPaymentConfirmationWebhook:
    @pytest.fixture
    async def setup_property(self, client: TestClient):
        # Helper to create a property directly in the DB for testing the webhook
        from app.dependencies.database import TestingSessionLocal
        
        prop_id = uuid4()
        payment_id = uuid4()
        
        async with TestingSessionLocal() as session:
            new_prop = Property(
                id=prop_id,
                user_id=uuid4(),
                payment_id=payment_id,
                title="Webhook Test",
                description="Desc",
                location="Loc",
                price=Decimal("500.00"),
                house_type="private home",
                status=PropertyStatus.PENDING
            )
            session.add(new_prop)
            await session.commit()
        
        return prop_id, payment_id

    async def test_confirmation_success(self, client: TestClient, setup_property):
        prop_id, payment_id = await setup_property
        
        with patch("app.routers.payments.send_notification", new_callable=MagicMock) as mock_send_notification:
            payload = {
                "property_id": str(prop_id),
                "payment_id": str(payment_id),
                "status": "SUCCESS"
            }
            headers = {"X-API-Key": settings.PAYMENT_SERVICE_API_KEY}
            
            response = client.post("/api/v1/payments/confirm", json=payload, headers=headers)
            
            assert response.status_code == 200
            assert response.json()["status"] == "received"
            mock_send_notification.assert_called_once()

            # Verify property status in DB
            from app.dependencies.database import TestingSessionLocal
            async with TestingSessionLocal() as session:
                prop = await session.get(Property, prop_id)
                assert prop.status == PropertyStatus.APPROVED

    async def test_confirmation_invalid_api_key(self, client: TestClient, setup_property):
        prop_id, payment_id = await setup_property
        payload = {"property_id": str(prop_id), "payment_id": str(payment_id), "status": "SUCCESS"}
        headers = {"X-API-Key": "wrong_key"}
        
        response = client.post("/api/v1/payments/confirm", json=payload, headers=headers)
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Invalid API Key"

    async def test_confirmation_missing_header(self, client: TestClient, setup_property):
        prop_id, payment_id = await setup_property
        payload = {"property_id": str(prop_id), "payment_id": str(payment_id), "status": "SUCCESS"}
        
        response = client.post("/api/v1/payments/confirm", json=payload)
        
        assert response.status_code == 403
        assert response.json()["detail"] == "X-API-Key header missing"

    async def test_confirmation_property_not_found(self, client: TestClient):
        payload = {
            "property_id": str(uuid4()),
            "payment_id": str(uuid4()),
            "status": "SUCCESS"
        }
        headers = {"X-API-Key": settings.PAYMENT_SERVICE_API_KEY}
        
        response = client.post("/api/v1/payments/confirm", json=payload, headers=headers)
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Property or payment ID not found"

    async def test_confirmation_payment_failed(self, client: TestClient, setup_property):
        prop_id, payment_id = await setup_property
        payload = {
            "property_id": str(prop_id),
            "payment_id": str(payment_id),
            "status": "FAILED"
        }
        headers = {"X-API-Key": settings.PAYMENT_SERVICE_API_KEY}
        
        response = client.post("/api/v1/payments/confirm", json=payload, headers=headers)
        
        assert response.status_code == 200
        assert response.json()["status"] == "received"

        # Verify property status is unchanged
        from app.dependencies.database import TestingSessionLocal
        async with TestingSessionLocal() as session:
            prop = await session.get(Property, prop_id)
            assert prop.status == PropertyStatus.PENDING
