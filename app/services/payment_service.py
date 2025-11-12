import httpx
import structlog
from uuid import UUID, uuid4
from decimal import Decimal
from app.config import settings

logger = structlog.get_logger(__name__)

async def initiate_payment(property_id: UUID, user_id: UUID, amount: Decimal) -> UUID:
    """
    Sends a request to the Payment Processing Service to initiate a payment.
    """
    initiate_url = f"{settings.PAYMENT_SERVICE_URL}/payments/initiate"
    request_id = UUID(uuid4()) # Generate a new UUID for request_id
    payload = {
        "request_id": str(request_id),
        "property_id": str(property_id),
        "user_id": str(user_id),
        "amount": float(amount)
    }
    headers = {
        "X-API-Key": settings.PAYMENT_SERVICE_API_KEY
    }

    logger.info("Initiating payment for property", property_id=str(property_id))

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(initiate_url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            
            response_data = response.json()
            payment_id = UUID(response_data["payment_id"])
            
            logger.info(
                "Payment initiated successfully",
                property_id=str(property_id),
                payment_id=str(payment_id)
            )
            return payment_id
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error occurred while initiating payment",
                property_id=str(property_id),
                status_code=e.response.status_code,
                response_body=e.response.text,
            )
            raise
        except (httpx.RequestError, KeyError, TypeError) as e:
            logger.error(
                "Error initiating payment",
                property_id=str(property_id),
                error=str(e),
            )
            raise
