from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.dependencies.database import get_db
from app.dependencies.security import get_api_key
from app.models.property import Property, PropertyStatus
from app.schemas.property import PaymentConfirmation
from app.services.notification import send_notification, get_approval_message

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
    """
    logger.info("Received payment confirmation webhook", payload=payload)

    prop = await db.query(Property).filter(
        Property.id == payload.property_id,
        Property.payment_id == payload.payment_id
    ).first()

    if not prop:
        logger.warning(
            "Property not found for payment confirmation",
            property_id=str(payload.property_id),
            payment_id=str(payload.payment_id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property or payment ID not found",
        )

    if payload.status == "SUCCESS":
        if prop.status == PropertyStatus.APPROVED:
            logger.info("Property already approved", property_id=str(prop.id))
            return {"status": "already_approved"}

        prop.status = PropertyStatus.APPROVED
        await db.commit()
        logger.info("Property approved successfully", property_id=str(prop.id))

        # Send notification to the property owner
        try:
            message = get_approval_message("en", title=prop.title, location=prop.location)
            await send_notification(str(prop.user_id), message)
            logger.info("Approval notification sent", user_id=str(prop.user_id))
        except Exception as e:
            logger.error("Failed to send notification", property_id=str(prop.id), error=str(e))

    else:
        logger.warning(
            "Payment confirmation received with non-success status",
            property_id=str(prop.id),
            payment_status=payload.status,
        )
        # Optionally, handle failed payment (e.g., move property to REJECTED)
        # For now, we just log it.

    return {"status": "received"}
