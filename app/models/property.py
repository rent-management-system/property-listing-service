import enum
from sqlalchemy import (Column, String, Text, Numeric, JSON, Enum, 
                        create_engine, MetaData, Float, DateTime, Index, Integer) # Added DateTime, Index, Integer
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR # Added TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime # Added datetime
from sqlalchemy.sql import func # Added func for server_default

Base = declarative_base()

class PropertyStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RESERVED = "RESERVED"
    DELETED = "DELETED"

class PaymentStatus(enum.Enum): # New Enum for payment status
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PAID = "PAID"

class Property(Base):
    __tablename__ = 'properties'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    payment_id = Column(UUID(as_uuid=True), nullable=True, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    house_type = Column(String(50), nullable=False, default='private home') # Changed to house_type
    amenities = Column(JSON, default=[])
    photos = Column(JSON, default=[])
    status = Column(Enum(PropertyStatus, native_enum=False), nullable=False, default=PropertyStatus.PENDING)
    payment_status = Column(Enum(PaymentStatus, native_enum=False), nullable=False, default=PaymentStatus.PENDING) # New payment status
    approval_timestamp = Column(DateTime, nullable=True) # New approval timestamp
    lat = Column(Float, nullable=True) # Added lat
    lon = Column(Float, nullable=True) # Added lon
    bedrooms = Column(Integer, nullable=True) # Added bedrooms
    bathrooms = Column(Integer, nullable=True) # Added bathrooms
    area_sqm = Column(Float, nullable=True) # Added area in square meters
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) # Added created_at
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False) # Added updated_at
    fts = Column(TSVECTOR, nullable=True) # Added fts for full-text search

    __table_args__ = (
        Index('idx_properties_user_id', user_id),
        Index('idx_properties_status', status),
        Index('idx_properties_location', location),
        Index('idx_properties_price', price),
        Index('idx_properties_lat_lon', func.ll_to_earth(lat, lon), postgresql_using='gist'), # For earthdistance
        Index('fts_idx', fts, postgresql_using='gin'), # For full-text search
    )
