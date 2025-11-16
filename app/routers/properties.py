from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
# import shutil # Removed shutil
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_owner, get_current_user
from app.models.property import Property, PropertyStatus, PaymentStatus # Added PaymentStatus
from app.schemas.property import (
    PropertySubmit, PropertySubmitResponse, 
    PropertyResponse, PropertyPublicResponse, HouseType, PaymentStatusEnum, PropertyUpdate # Added PaymentStatusEnum
)
from app.services.gebeta import geocode_location_with_fallback
from app.services.payment_service import initiate_payment
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from datetime import datetime # Added datetime

from sqlalchemy import func, text, select, cast, TEXT
from app.utils.object_storage import upload_file_to_object_storage
from app.config import settings # Added settings

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
    house_type: HouseType = Form(...),
    amenities: List[str] = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_owner_data: dict = Depends(get_current_owner)
):
    current_user = current_owner_data["user"]
    access_token = current_owner_data["token"]
    image_url = await upload_file_to_object_storage(file)
    geocoded_data = await geocode_location_with_fallback(location)

    new_property = Property(
        user_id=UUID(current_user['user_id']),
        title=title,
        description=description,
        location=location,
        price=price,
        house_type=house_type,
        amenities=amenities,
        photos=[image_url],
        lat=geocoded_data["lat"],
        lon=geocoded_data["lon"],
        payment_status=PaymentStatus.PENDING # Set initial payment status
    )
    db.add(new_property)
    await db.commit()
    await db.refresh(new_property)

    try:
        # Initiate payment with the payment service
        request_id, payment_id, chapa_tx_ref, checkout_url = await initiate_payment(
            property_id=new_property.id,
            user_id=current_user['user_id'],
            access_token=access_token
        )
        
        # Store the payment_id and commit
        new_property.payment_id = payment_id
        await db.commit()
        await db.refresh(new_property)

    except Exception as e:
        # If payment initiation fails, roll back property creation by deleting it.
        logger.error("Failed to initiate payment, rolling back property creation", property_id=str(new_property.id), error_message=str(e))
        await db.delete(new_property)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is currently unavailable. Please try again later.",
        )

    return {
        "property_id": new_property.id,
        "status": new_property.status.value,
        "payment_id": new_property.payment_id,
        "chapa_tx_ref": chapa_tx_ref,
        "checkout_url": checkout_url # Return checkout_url
    }

@router.get("/my-properties", response_model=List[PropertyResponse])
async def get_my_properties(
    db: AsyncSession = Depends(get_db),
    current_owner_data: dict = Depends(get_current_owner)
):
    """
    Retrieves all properties owned by the currently authenticated user.
    """
    current_user_id = UUID(current_owner_data["user"]["user_id"])
    
    query = select(Property).where(
        Property.user_id == current_user_id,
        cast(Property.status, TEXT) != PropertyStatus.DELETED.value
    )
    result = await db.execute(query)
    properties = result.scalars().all()
    
    return properties


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
    if str(prop.user_id) != current_user['user_id'] and current_user['role'].lower() != 'admin': # Ensure comparison is correct
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
        # Ensure amenities are treated as an array in the query
        query = query.where(Property.amenities.op('&&')(amenities))

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: UUID,
    property_update: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_owner_data: dict = Depends(get_current_owner)
):
    """
    Updates a property owned by the currently authenticated user.
    """
    current_user_id = UUID(current_owner_data["user"]["user_id"])
    
    prop = await db.get(Property, property_id)
    
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        
    if prop.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this property")

    update_data = property_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prop, key, value)
        
    await db.commit()
    await db.refresh(prop)
    
    return prop

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_owner_data: dict = Depends(get_current_owner)
):
    """
    Deletes a property owned by the currently authenticated user (soft delete).
    """
    current_user_id = UUID(current_owner_data["user"]["user_id"])
    
    prop = await db.get(Property, property_id)
    
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        
    if prop.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this property")
        
    prop.status = PropertyStatus.DELETED
    await db.commit()
    
    return

@router.patch("/{property_id}/reserve", response_model=PropertyResponse)
async def reserve_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_owner_data: dict = Depends(get_current_owner)
):
    """
    Marks a property as 'RESERVED'.
    """
    current_user_id = UUID(current_owner_data["user"]["user_id"])
    
    prop = await db.get(Property, property_id)
    
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        
    if prop.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to reserve this property")

    if prop.status != PropertyStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only approved properties can be reserved")
        
    prop.status = PropertyStatus.RESERVED
    await db.commit()
    await db.refresh(prop)
    
    return prop
