import httpx
import structlog
from uuid import UUID, uuid4
from typing import Optional
from fastapi import HTTPException, status
from app.config import settings

logger = structlog.get_logger(__name__)

async def initiate_payment(property_id: UUID, user_id: UUID, access_token: str) -> tuple[UUID, Optional[UUID], Optional[str], Optional[str]]:
    """
    Sends a request to the Payment Processing Service to initiate a payment.
    The amount and currency are fixed from settings.
    
    Args:
        property_id: The ID of the property to pay for
        user_id: The ID of the user making the payment
        access_token: The access token for authentication
        
    Returns:
        A tuple containing (request_id, payment_id, chapa_tx_ref, checkout_url)
        
    Raises:
        HTTPException: If the payment cannot be initiated
    """
    initiate_url = f"{settings.PAYMENT_SERVICE_URL}/payments/initiate"
    
    # Generate a unique request_id based on property_id and timestamp for idempotency
    request_id = uuid4()
    
    payload = {
        "request_id": str(request_id),
        "property_id": str(property_id),
        "user_id": str(user_id),
        "amount": float(settings.PAYMENT_AMOUNT),
        "currency": settings.PAYMENT_CURRENCY,
        "is_test_mode": settings.CHAPA_IS_TEST_MODE
    }
    
    headers = {
        "Authorization": f"Bearer {str(access_token)}",
        "Content-Type": "application/json"
    }

    logger.info(
        "Initiating payment for property",
        property_id=str(property_id),
        user_id=str(user_id),
        amount=settings.PAYMENT_AMOUNT,
        currency=settings.PAYMENT_CURRENCY,
        is_test_mode=settings.CHAPA_IS_TEST_MODE
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(initiate_url, json=payload, headers=headers)
            
            # Handle rate limiting (429)
            if response.status_code == 429:
                logger.warning(
                    "Rate limited by payment service",
                    property_id=str(property_id),
                    status_code=429
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Payment service is currently experiencing high load. Please try again later."
                )
            
            # Raise exception for other non-2xx responses
            response.raise_for_status()
            
            # Process successful response
            response_data = response.json()
            payment_id = response_data.get("id")
            chapa_tx_ref = response_data.get("chapa_tx_ref")
            checkout_url = response_data.get("checkout_url")
            
            if payment_id is None:
                logger.warning(
                    "Payment initiated but payment_id not returned by payment service",
                    property_id=str(property_id),
                    response_data=response_data
                )
                
            return request_id, UUID(payment_id) if payment_id else None, chapa_tx_ref, checkout_url
            
    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP error from payment service",
            property_id=str(property_id),
            status_code=e.response.status_code if hasattr(e, 'response') else None,
            error=str(e)
        )
        
        if hasattr(e, 'response') and 400 <= e.response.status_code < 500:
            detail = f"Payment service error: {e.response.text}"
            if e.response.status_code == 400:
                detail = "Invalid payment request. Please check your input and try again."
            raise HTTPException(status_code=e.response.status_code, detail=detail)
        
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment service is currently unavailable. Please try again later."
        )
        
    except httpx.RequestError as e:
        logger.error(
            "Network error connecting to payment service",
            property_id=str(property_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to the payment service. Please try again later."
        )
        
    except (ValueError, TypeError, KeyError) as e:
        logger.error(
            "Invalid response format from payment service",
            property_id=str(property_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Received an invalid response from the payment service."
        )
