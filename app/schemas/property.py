from pydantic import BaseModel, UUID4
from decimal import Decimal
from typing import List, Optional
from enum import Enum
from datetime import datetime # Added datetime

class HouseType(str, Enum):
    CONDOMINIUM = "condominium"
    PRIVATE_HOME = "private home"
    APARTMENT = "apartment"
    STUDIO = "studio"
    VILLA = "villa"
    COMMERCIAL = "commercial"
    OFFICE = "office"
    HOUSE = "house"
    GUESTHOUSE = "guesthouse"
    PENTHOUSE = "penthouse"

class PaymentStatusEnum(str, Enum): # Renamed to avoid conflict with model enum
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class PropertySubmit(BaseModel):
    title: str
    description: str
    location: str
    price: Decimal
    house_type: HouseType # Make it required
    amenities: List[str]

class PropertyResponse(BaseModel):
    id: UUID4
    title: str
    description: str
    location: str
    price: Decimal
    house_type: HouseType
    amenities: List[str]
    photos: List[str]
    status: str
    payment_status: Optional[PaymentStatusEnum] = None # Added payment_status
    approval_timestamp: Optional[datetime] # Added approval_timestamp
    lat: Optional[float]
    lon: Optional[float]

    class Config:
        from_attributes = True

class PropertySubmitResponse(BaseModel):
    property_id: UUID4
    status: str

class PaymentInitiationResponse(BaseModel):
    property_id: UUID4
    status: str
    payment_id: UUID4
    chapa_tx_ref: str
    checkout_url: str


class PaymentConfirmation(BaseModel):
    property_id: UUID4
    payment_id: UUID4
    status: str
    tx_ref: Optional[str] = None # Added optional tx_ref
    error_message: Optional[str] = None # Added optional error_message

class PropertyPublicResponse(BaseModel):
    id: UUID4
    title: str
    location: str
    price: Decimal
    house_type: HouseType
    amenities: List[str]
    status: str
    payment_status: Optional[PaymentStatusEnum] = None # Added payment_status
    approval_timestamp: Optional[datetime] # Added approval_timestamp
    lat: Optional[float]
    lon: Optional[float]

    class Config:
        from_attributes = True

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    amenities: Optional[List[str]] = None
