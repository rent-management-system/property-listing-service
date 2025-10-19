from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
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

router = APIRouter()

@router.post("/submit", status_code=status.HTTP_201_CREATED, response_model=PropertySubmitResponse)
async def submit_property(
    property_data: PropertySubmit,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_owner)
):
    new_property = Property(
        user_id=current_user['user_id'],
        **property_data.dict()
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
        raise HTTPException(status_code=404, detail="Property not found")

    prop.status = PropertyStatus.APPROVED
    await db.commit()

    # Send notification
    # In a real app, you'd get the user's language from the user service
    message = get_approval_message("am") # Mocking Amharic
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
    if str(prop.user_id) != current_user['user_id'] and current_user['role'] != 'Admin':
        raise HTTPException(status_code=403, detail="Not authorized to view this property")

    return prop

@router.get("", response_model=List[PropertyPublicResponse])
async def get_all_properties(
    db: AsyncSession = Depends(get_db),
    location: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    amenities: Optional[List[str]] = Query(None)
):
    query = db.query(Property).filter(Property.status == PropertyStatus.APPROVED)

    if location:
        query = query.filter(Property.location.ilike(f"%{location}%"))
    if min_price:
        query = query.filter(Property.price >= min_price)
    if max_price:
        query = query.filter(Property.price <= max_price)
    if amenities:
        query = query.filter(Property.amenities.contains(amenities))

    result = await db.execute(query)
    return result.scalars().all()
