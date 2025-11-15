from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from sqlalchemy import select # Added import
from datetime import datetime # Added datetime

from app.dependencies.database import get_db
from app.dependencies.security import get_api_key
from app.models.property import Property, PropertyStatus, PaymentStatus # Added PaymentStatus
from app.schemas.property import PaymentConfirmation, PropertyResponse, PaymentStatusEnum # Added PaymentStatusEnum
from app.services.notification import send_notification, get_approval_message
from app.config import settings # Added settings

logger = structlog.get_logger(__name__)

router = APIRouter()

@router.post("/payments/confirm", status_code=status.HTTP_200_OK)
async def payment_confirmation_webhook(
    payload: PaymentConfirmation,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Webhook to receive payment confirmation from the Payment Processing Service.
    Ensures idempotency and updates property status.
    """
    logger.info("Payment confirmation webhook received", data=payload.model_dump(mode='json'))
    
    # Ensure the API key is the one designated for property webhooks
    if api_key != settings.PROPERTY_WEBHOOK_API_KEY:
        logger.warning("Unauthorized API Key for payment confirmation webhook", received_key=api_key)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key for this endpoint",
        )

    try:
        result = await db.execute(
            select(Property).filter(Property.id == payload.property_id)
        )
        prop = result.scalar_one_or_none()

        if not prop:
            logger.warning(
                "Property not found for payment confirmation",
                property_id=str(payload.property_id),
                payment_id=str(payload.payment_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found",
            )

        logger.info("Retrieved property for payment confirmation", property_data=PropertyResponse.from_orm(prop).model_dump(mode='json'))
        
        # Idempotency check: If payment status is already SUCCESS or FAILED, do nothing.
        if prop.payment_status == PaymentStatus.SUCCESS or prop.payment_status == PaymentStatus.FAILED:
            logger.info(
                "Payment already processed for property",
                property_id=str(prop.id),
                current_payment_status=prop.payment_status.value,
            )
            return {"status": "already_processed"}

        # Update payment_status based on payload status
        if payload.status == PaymentStatusEnum.SUCCESS.value:
            prop.payment_status = PaymentStatus.SUCCESS
            prop.status = PropertyStatus.APPROVED # Approve the property
            prop.approval_timestamp = datetime.utcnow() # Set approval timestamp
            logger.info("Property payment successful and approved", property_id=str(prop.id))

            # Send notification to the property owner
            try:
                # Fetch user data to get preferred language if needed, or default to English
                # For now, defaulting to English and using fixed payment details from settings
                message = get_approval_message(
                    "en", # Assuming English for now, can be dynamic
                    title=prop.title,
                    location=prop.location,
                    payment_amount=settings.PAYMENT_AMOUNT,
                    payment_currency=settings.PAYMENT_CURRENCY
                )
                await send_notification(str(prop.user_id), message)
                logger.info("Approval notification sent", user_id=str(prop.user_id))
            except Exception as e:
                logger.error("Failed to send notification", property_id=str(prop.id), error=str(e), exc_info=True)

        elif payload.status == PaymentStatusEnum.FAILED.value:
            prop.payment_status = PaymentStatus.FAILED
            # Optionally, set PropertyStatus to REJECTED or keep PENDING based on business logic
            # For now, we'll keep it PENDING if payment failed, awaiting user action or timeout
            logger.warning(
                "Payment failed for property",
                property_id=str(prop.id),
                payment_status=payload.status,
                tx_ref=payload.tx_ref,
                error_message=payload.error_message,
            )
        else:
            logger.warning(
                "Payment confirmation received with unknown status",
                property_id=str(prop.id),
                payment_status=payload.status,
            )
        
        await db.commit()
        await db.refresh(prop)

        return {"status": "received", "property_status": prop.status.value, "payment_status": prop.payment_status.value}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(
            "An unexpected error occurred in payment confirmation webhook",
            payload=payload.model_dump(mode='json'),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the payment confirmation."
        )
