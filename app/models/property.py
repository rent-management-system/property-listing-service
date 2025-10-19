import enum
from sqlalchemy import (Column, String, Text, Numeric, JSON, Enum, 
                        create_engine, MetaData)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class PropertyStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class Property(Base):
    __tablename__ = 'properties'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    amenities = Column(JSON, default=[])
    photos = Column(JSON, default=[])
    status = Column(Enum(PropertyStatus), nullable=False, default=PropertyStatus.PENDING)
