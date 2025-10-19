from pydantic import BaseModel, UUID4
from decimal import Decimal
from typing import List, Optional

class PropertySubmit(BaseModel):
    title: str
    description: str
    location: str
    price: Decimal
    amenities: List[str]
    photos: List[str]

class PropertyResponse(BaseModel):
    id: UUID4
    title: str
    description: str
    location: str
    price: Decimal
    amenities: List[str]
    photos: List[str]
    status: str

    class Config:
        orm_mode = True

class PropertySubmitResponse(BaseModel):
    property_id: UUID4
    status: str
    payment_url: str

class PropertyApprove(BaseModel):
    payment_id: UUID4

class PropertyPublicResponse(BaseModel):
    id: UUID4
    title: str
    location: str
    price: Decimal
    amenities: List[str]
    status: str

    class Config:
        orm_mode = True
