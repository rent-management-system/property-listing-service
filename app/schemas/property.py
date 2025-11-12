from pydantic import BaseModel, UUID4
from decimal import Decimal
from typing import List, Optional
from enum import Enum

class HouseType(str, Enum):
    CONDOMINIUM = "condominium"
    PRIVATE_HOME = "private home"
    APARTMENT = "apartment"

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
    lat: Optional[float]
    lon: Optional[float]

    class Config:
        orm_mode = True

class PropertySubmitResponse(BaseModel):
    property_id: UUID4
    status: str
    payment_id: Optional[UUID4]
    chapa_tx_ref: Optional[str]


class PaymentConfirmation(BaseModel):
    property_id: UUID4
    payment_id: UUID4
    status: str

class PropertyPublicResponse(BaseModel):
    id: UUID4
    title: str
    location: str
    price: Decimal
    house_type: HouseType
    amenities: List[str]
    status: str
    lat: Optional[float]
    lon: Optional[float]

    class Config:
        orm_mode = True
