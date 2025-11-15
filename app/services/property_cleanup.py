from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import structlog

from app.models.property import Property, PropertyStatus, PaymentStatus
from app.services.notification import send_notification, get_approval_message
from app.config import settings
from app.dependencies.database import AsyncSessionLocal # Import AsyncSessionLocal

logger = structlog.get_logger(__name__)

async def cleanup_stale_pending_properties():
    """
    Background task to identify and update stale PENDING properties.
    A property is considered stale if its payment_status is PENDING
    and it was created more than 7 days ago.
    """
    logger.info("Running cleanup for stale pending properties")
    
    async with AsyncSessionLocal() as db: # Use AsyncSessionLocal to get a session
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        stale_properties_query = select(Property).where(
            Property.payment_status == PaymentStatus.PENDING,
            Property.created_at < seven_days_ago
        )
        
        result = await db.execute(stale_properties_query)
        stale_properties = result.scalars().all()
        
        if not stale_properties:
            logger.info("No stale pending properties found")
            return

        for prop in stale_properties:
            logger.info(
                "Marking stale property as FAILED",
                property_id=str(prop.id),
                created_at=prop.created_at.isoformat()
            )
            prop.payment_status = PaymentStatus.FAILED
            prop.status = PropertyStatus.REJECTED # Optionally reject the property status as well
            
            # Send notification to the owner about the failed payment/rejected property
            try:
                message = get_approval_message(
                    "en", # Assuming English, can be dynamic
                    title=prop.title,
                    location=prop.location,
                    payment_amount=settings.PAYMENT_AMOUNT,
                    payment_currency=settings.PAYMENT_CURRENCY
                )
                # Modify message for rejection
                message = f"Your listing '{prop.title}' in {prop.location} has been rejected due to payment timeout. Please resubmit if you wish to list it again."
                await send_notification(str(prop.user_id), message)
                logger.info("Stale property notification sent", user_id=str(prop.user_id))
            except Exception as e:
                logger.error("Failed to send notification for stale property", property_id=str(prop.id), error=str(e), exc_info=True)
        
        await db.commit()
        logger.info(f"Cleaned up {len(stale_properties)} stale pending properties")
