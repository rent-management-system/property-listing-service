import httpx
import structlog
from uuid import UUID, uuid4
from decimal import Decimal
from app.config import settings

logger = structlog.get_logger(__name__)

async def initiate_payment(property_id: UUID, user_id: UUID, amount: Decimal, access_token: str) -> tuple[UUID, UUID]:
    """
    Sends a request to the Payment Processing Service to initiate a payment.
    """
    initiate_url = f"{settings.PAYMENT_SERVICE_URL}/payments/initiate"
    request_id = uuid4()
    payload = {
        "request_id": str(request_id),
        "property_id": str(property_id),
        "user_id": str(user_id),
        "amount": float(amount)
    }
    headers = {
        "Authorization": f"Bearer {str(access_token)}"
    }

    logger.info(
        "Initiating payment for property - debug info",
        property_id_type=str(type(property_id)),
        user_id_type=str(type(user_id)),
        amount_type=str(type(amount)),
        access_token_type=str(type(access_token)),
        payload_request_id_type=str(type(payload["request_id"])),
        payload_property_id_type=str(type(payload["property_id"])),
        payload_user_id_type=str(type(payload["user_id"])),
        payload_amount_type=str(type(payload["amount"])),
        header_auth_type=str(type(headers["Authorization"])),
        initiate_url=initiate_url,
        payload=payload,
        headers=headers
    )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(initiate_url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            
            response_data = response.json()
            payment_id = response_data.get("payment_id")
            
            if payment_id is None:
                logger.warning(
                    "Payment initiated but payment_id not returned immediately by payment service",
                    property_id=str(property_id),
                    response_data=response_data,
                    status_code=response.status_code
                )
                # If payment_id is not returned, we can proceed without it for now,
                # assuming a background process or webhook will update it later.
                # For now, we'll return None for payment_id.
                return request_id, None
            
            payment_id = UUID(payment_id)
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
