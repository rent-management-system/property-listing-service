import httpx
import structlog
from uuid import UUID, uuid4
from decimal import Decimal
from typing import Optional # Added this import
from app.config import settings
from datetime import datetime # Added datetime

logger = structlog.get_logger(__name__)

async def initiate_payment(property_id: UUID, user_id: UUID, access_token: str) -> tuple[UUID, Optional[UUID], Optional[str], Optional[str]]:
    """
    Sends a request to the Payment Processing Service to initiate a payment.
    The amount and currency are fixed from settings.
    """
    initiate_url = f"{settings.PAYMENT_SERVICE_URL}/payments/initiate"
    
    # Generate a unique request_id based on property_id and timestamp for idempotency
    request_id = uuid4()
    
    payload = {
        "request_id": str(request_id),
        "property_id": str(property_id),
        "user_id": str(user_id),
        "amount": float(settings.PAYMENT_AMOUNT), # Use fixed amount from settings
        "currency": settings.PAYMENT_CURRENCY, # Use fixed currency from settings
        "is_test_mode": settings.CHAPA_IS_TEST_MODE # Pass test mode flag
    }
    headers = {
        "Authorization": f"Bearer {str(access_token)}"
    }

    logger.info(
        "Initiating payment for property",
        property_id=str(property_id),
        user_id=str(user_id),
        amount=settings.PAYMENT_AMOUNT,
        currency=settings.PAYMENT_CURRENCY,
        is_test_mode=settings.CHAPA_IS_TEST_MODE,
        initiate_url=initiate_url,
    )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(initiate_url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            
            response_data = response.json()
            payment_id = response_data.get("id")
            chapa_tx_ref = response_data.get("chapa_tx_ref")
            checkout_url = response_data.get("checkout_url") # Get checkout_url
            
            if payment_id is None:
                logger.warning(
                    "Payment initiated but payment_id not returned immediately by payment service",
                    property_id=str(property_id),
                    response_data=response_data,
                    status_code=response.status_code
                )
                return request_id, None, chapa_tx_ref, checkout_url
            
            payment_id = UUID(payment_id)
            return request_id, payment_id, chapa_tx_ref, checkout_url
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
                exc_info=True,  # Add full exception info to the log
            )
            raise
