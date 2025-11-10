from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
# import shutil # Removed shutil
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_owner, get_current_user
from app.models.property import Property, PropertyStatus
from app.schemas.property import (
    PropertySubmit, PropertySubmitResponse, PropertyApprove, 
    PropertyResponse, PropertyPublicResponse
)
from app.services.notification import send_notification, get_approval_message
import httpx
from app.config import settings
from uuid import UUID
from typing import List, Optional
from decimal import Decimal

from sqlalchemy import func, text, select
from app.utils.object_storage import upload_file_to_object_storage # Added import

logger = structlog.get_logger(__name__)

router = APIRouter()

@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    logger.info("metrics_accessed", endpoint="metrics", service="property")
    total_listings = await db.scalar(select(func.count(Property.id)))
    pending = await db.scalar(select(func.count(Property.id)).where(Property.status == PropertyStatus.PENDING))
    approved = await db.scalar(select(func.count(Property.id)).where(Property.status == PropertyStatus.APPROVED))
    rejected = await db.scalar(select(func.count(Property.id)).where(Property.status == PropertyStatus.REJECTED))
    return {
        "total_listings": total_listings,
        "pending": pending,
        "approved": approved,
        "rejected": rejected
    }

@router.post("/submit", status_code=status.HTTP_201_CREATED, response_model=PropertySubmitResponse)
async def submit_property(
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    price: Decimal = Form(...),
    amenities: List[str] = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_owner)
):
    # Remove local file saving logic
    # file_path = f"uploads/{file.filename}"
    # with open(file_path, "wb") as buffer:
    #     shutil.copyfileobj(file.file, buffer)

    # Upload to Supabase and get URL
    image_url = await upload_file_to_object_storage(file)

    new_property = Property(
        user_id=current_user['user_id'],
        title=title,
        description=description,
        location=location,
        price=price,
        amenities=amenities,
        photos=[image_url] # Store the URL
    )
    db.add(new_property)
    await db.commit()
    await db.refresh(new_property)

    # Mock payment initiation
    payment_url = f"{settings.PAYMENT_PROCESSING_URL}/payments/initiate/{new_property.id}"

    return {
        "property_id": new_property.id,
        "status": new_property.status.value,
        "payment_url": payment_url
    }

@router.post("/{id}/approve", status_code=status.HTTP_200_OK)
async def approve_property(
    id: UUID,
    approval_data: PropertyApprove,
    db: AsyncSession = Depends(get_db)
):
    # In a real app, you'd verify approval_data.payment_id with the payment service
    prop = await db.get(Property, id)
    if not prop:
        logger.error("approval_failed", property_id=str(id), reason="Property not found")
        raise HTTPException(status_code=404, detail="Property not found")

    prop.status = PropertyStatus.APPROVED
    await db.commit()

    # Send notification
    # In a real app, you'd get the user's language from the user service
    message = get_approval_message("am", title=prop.title, location=prop.location) # Mocking Amharic
    await send_notification(str(prop.user_id), message)

    return {"status": "success"}

@router.get("/{id}", response_model=PropertyResponse)
async def get_property(
    id: UUID, 
    db: AsyncSession = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    prop = await db.get(Property, id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check ownership or admin role
    if prop.user_id != current_user['user_id'] and current_user['role'] != 'Admin':
        raise HTTPException(status_code=403, detail="Not authorized to view this property")

    return prop

@router.get("", response_model=List[PropertyPublicResponse])
async def get_all_properties(
    db: AsyncSession = Depends(get_db),
    location: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    amenities: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 20
):
    query = select(Property).where(Property.status == PropertyStatus.APPROVED)

    if search and db.bind.dialect.name != "sqlite":
        query = query.where(text("to_tsvector('english', title || ' ' || description) @@ to_tsquery('english', :search_query)").bindparams(search_query=search))
    if location:
        query = query.where(Property.location.ilike(f"%{location}%"))
    if min_price:
        query = query.where(Property.price >= min_price)
    if max_price:
        query = query.where(Property.price <= max_price)
    if amenities:
        query = query.where(Property.amenities.contains(amenities))

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
