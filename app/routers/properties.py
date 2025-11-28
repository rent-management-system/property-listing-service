import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
# import shutil # Removed shutil
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
import httpx
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_owner, get_current_user
from app.models.property import Property, PropertyStatus, PaymentStatus # Added PaymentStatus
from app.schemas.property import (
    PropertySubmit, PropertySubmitResponse, 
    PropertyResponse, PropertyPublicResponse, HouseType, PaymentStatusEnum, PropertyUpdate, PaymentInitiationResponse, MetricsResponse, PropertyListResponse, PropertyOwnerContactResponse # Added PropertyOwnerContactResponse
)
from app.services.gebeta import geocode_location_with_fallback
from app.services.payment_service import initiate_payment
from app.services.user_service import get_user_by_id
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from datetime import datetime # Added datetime

from sqlalchemy import func, text, select
from app.utils.object_storage import upload_file_to_object_storage
from app.config import settings # Added settings

logger = structlog.get_logger(__name__)

router = APIRouter()

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(db: AsyncSession = Depends(get_db)):
    logger.info("metrics_accessed", endpoint="metrics", service="property")
    total_listings = await db.scalar(select(func.count(Property.id)))
    pending = await db.scalar(select(func.count(Property.id)).where(Property.status == PropertyStatus.PENDING))
    approved = await db.scalar(select(func.count(Property.id)).where(Property.status == PropertyStatus.APPROVED))
    rejected = await db.scalar(select(func.count(Property.id)).where(Property.status == PropertyStatus.REJECTED))
    total_revenue = await db.scalar(
        select(func.coalesce(func.sum(Property.price), 0)).where(
            Property.payment_status.in_([PaymentStatus.SUCCESS, PaymentStatus.PAID])
        )
    )
    return {
        "total_listings": total_listings,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "total_revenue": total_revenue
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
    bedrooms: Optional[int] = Form(None),
    bathrooms: Optional[int] = Form(None),
    area_sqm: Optional[float] = Form(None),
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
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        area_sqm=area_sqm,
        payment_status=PaymentStatus.PENDING # Set initial payment status
    )
    db.add(new_property)
    await db.commit()
    await db.refresh(new_property)

    return {
        "property_id": new_property.id,
        "status": new_property.status.value,
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
        Property.status != PropertyStatus.DELETED
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


@router.get("", response_model=PropertyListResponse)
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

    # Compute total count without pagination
    count_query = select(func.count(Property.id)).where(Property.status == PropertyStatus.APPROVED)
    if search and db.bind.dialect.name != "sqlite":
        count_query = count_query.where(text("to_tsvector('english', title || ' ' || description) @@ to_tsquery('english', :search_query)").bindparams(search_query=search))
    if location:
        count_query = count_query.where(Property.location.ilike(f"%{location}%"))
    if min_price:
        count_query = count_query.where(Property.price >= min_price)
    if max_price:
        count_query = count_query.where(Property.price <= max_price)
    if amenities:
        count_query = count_query.where(Property.amenities.op('&&')(amenities))

    total = await db.scalar(count_query)

    # Fetch paginated items
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return {"total": total or 0, "items": items}

@router.get("/public/{id}", response_model=PropertyResponse)
async def get_property_public(
    id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Public, non-auth endpoint to fetch a single approved property by id.
    Returns 404 if the property does not exist or is not APPROVED.
    """
    prop = await db.get(Property, id)
    if not prop or prop.status != PropertyStatus.APPROVED:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop

@router.get("/public", response_model=List[PropertyPublicResponse])
async def get_all_properties_public(
    db: AsyncSession = Depends(get_db),
    location: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    amenities: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 20
):
    """
    Public, non-auth endpoint to list approved properties with full details.
    Supports basic filters and pagination. Only returns APPROVED listings.
    """
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
    
    # First, get the property to check ownership
    prop = await db.get(Property, property_id)
    
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        
    if prop.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this property")
        
    # Manually construct the SQL string to embed 'DELETED' directly
    # This bypasses all parameter binding for the status value, forcing PostgreSQL to accept it as a literal.
    sql_query = text(
        f"UPDATE properties SET status = 'DELETED', updated_at = now() WHERE id = :id"
    )
    await db.execute(sql_query, {"id": property_id})
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

@router.patch("/{property_id}/unreserve", response_model=PropertyResponse)
async def unreserve_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_owner_data: dict = Depends(get_current_owner)
):
    """
    Changes a property's status from 'RESERVED' back to 'APPROVED'.
    """
    current_user_id = UUID(current_owner_data["user"]["user_id"])
    
    prop = await db.get(Property, property_id)
    
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        
    if prop.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to unreserve this property")

    if prop.status != PropertyStatus.RESERVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only reserved properties can be unreserved")
        
    prop.status = PropertyStatus.APPROVED
    await db.commit()
    await db.refresh(prop)
    
    return prop

@router.patch("/{property_id}/approve-and-pay", response_model=PaymentInitiationResponse)
async def approve_and_pay(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_owner_data: dict = Depends(get_current_owner)
):
    """
    Approves a PENDING property and initiates its payment process.
    """
    current_user = current_owner_data["user"]
    access_token = current_owner_data["token"]

    prop = await db.get(Property, property_id)

    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    if prop.user_id != UUID(current_user['user_id']):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to approve this property")

    if prop.status != PropertyStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending properties can be approved for payment.")
    
    if prop.payment_status != PaymentStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment process already initiated or completed for this property.")

    max_retries = 3
    backoff_factor = 1  # seconds

    for attempt in range(max_retries + 1):
        try:
            # Initiate payment with the payment service
            request_id, payment_id, chapa_tx_ref, checkout_url = await initiate_payment(
                property_id=prop.id,
                user_id=current_user['user_id'],
                access_token=access_token
            )
            
            # Store the payment_id and commit
            prop.payment_id = payment_id
            # The payment_status will be updated by the webhook after actual payment confirmation
            await db.commit()
            await db.refresh(prop)
            break  # Break out of the retry loop if successful

        except httpx.HTTPStatusError as e:
            error_detail = f"Payment service returned an error: {e.response.status_code}"
            try:
                error_detail = e.response.json().get("detail", error_detail)
            except Exception:
                pass

            logger.error(
                "HTTP status error while initiating payment",
                property_id=str(prop.id),
                status_code=e.response.status_code,
                error_detail=error_detail,
                attempt=attempt + 1,
                max_retries=max_retries
            )

            if e.response.status_code == 429:
                if attempt < max_retries:
                    # Get retry-after header if available, otherwise use exponential backoff
                    retry_after = e.response.headers.get("retry-after")
                    if retry_after and retry_after.isdigit():
                        sleep_time = float(retry_after)
                    else:
                        sleep_time = backoff_factor * (2 ** attempt)
                    
                    logger.warning(
                        "Payment service rate limit hit, retrying...",
                        property_id=str(prop.id),
                        sleep_time=sleep_time,
                        attempt=attempt + 1,
                        max_retries=max_retries
                    )
                    await asyncio.sleep(sleep_time)
                    continue  # Continue to next retry attempt
                else:
                    # If we've exhausted all retries, return a 429 with appropriate detail
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=(
                            "Payment service is currently experiencing high load. "
                            f"Please try again in {int(backoff_factor * 2 ** attempt)} seconds."
                        )
                    )
            
            # For other 4xx errors, return the original status code and message
            if 400 <= e.response.status_code < 500:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=error_detail or "Bad request to payment service"
                )
            
            # For 5xx errors, return a 502 Bad Gateway
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "The payment service is currently unavailable. "
                    "Please try again later."
                )
            )
        except httpx.RequestError as e:
            logger.error("Network error while initiating payment", property_id=str(prop.id), error_message=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to the payment service. Please try again later.",
            )
        except (ValueError, TypeError) as e:
            logger.error("Invalid response format from payment service", property_id=str(prop.id), error_message=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Received an invalid or unexpected response from the payment service.",
            )
        except Exception as e:
            logger.error("An unexpected error occurred during payment initiation", property_id=str(prop.id), error_message=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error occurred. Please try again later.",
            )
    else:
        # This else block is executed if the loop completes without a 'break'
        # meaning all retries failed for a 429 error.
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Failed to initiate payment after multiple retries due to rate limiting. Please try again later."
        )

    return {
        "property_id": prop.id,
        "status": prop.status.value, # Property status remains PENDING until payment is confirmed by webhook
        "payment_id": payment_id,
        "chapa_tx_ref": chapa_tx_ref,
        "checkout_url": checkout_url
    }

@router.get("/{property_id}/owner-contact", response_model=PropertyOwnerContactResponse)
async def get_property_owner_contact(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves the property owner's contact information for a given property ID.
    This endpoint allows authenticated users to get owner contact details including
    name, email, phone number, and other contact information.
    
    Args:
        property_id: The UUID of the property
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        PropertyOwnerContactResponse with owner contact details
    """
    # Fetch the property
    prop = await db.get(Property, property_id)
    
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Only allow access to approved properties for contact information
    if prop.status != PropertyStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Contact information is only available for approved properties"
        )
    
    try:
        # Fetch owner details from User Management Service
        owner_data = await get_user_by_id(str(prop.user_id))
        
        # Extract contact information
        return PropertyOwnerContactResponse(
            property_id=prop.id,
            owner_id=prop.user_id,
            owner_name=owner_data.get("full_name", owner_data.get("name", "N/A")),
            owner_email=owner_data.get("email", "N/A"),
            owner_phone=owner_data.get("phone_number", owner_data.get("phone")),
            property_title=prop.title,
            property_location=prop.location
        )
        
    except Exception as e:
        logger.error(
            "Failed to fetch owner contact information",
            property_id=str(property_id),
            owner_id=str(prop.user_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve owner contact information at this time"
        )
