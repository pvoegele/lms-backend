"""
Facility Entities - Warehouse and storage location structures
Physical infrastructure and location hierarchy
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from warehouse_nexus.cerebrum.psql_conductor import EntityFoundation
from warehouse_nexus.schema_registry.categorical_taxonomy import LocationCategory
from datetime import datetime
from uuid import uuid4


class Warehouse(EntityFoundation):
    """Warehouse facility"""
    __tablename__ = "warehouse"
    
    warehouse_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(Text, nullable=True)
    manager = Column(String(150), nullable=True)
    capacity_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    storage_locations = relationship("StorageLocation", back_populates="warehouse", foreign_keys="StorageLocation.warehouse_id")
    
    __table_args__ = (
        Index('ix_warehouse_active', 'is_active'),
    )


class StorageLocation(EntityFoundation):
    """Storage location within warehouse"""
    __tablename__ = "storage_location"
    
    location_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey('warehouse.warehouse_id', ondelete='CASCADE'), nullable=False)
    code = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    location_type = Column(Enum(LocationCategory, name='location_type'), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    warehouse = relationship("Warehouse", back_populates="storage_locations", foreign_keys=[warehouse_id])
    
    __table_args__ = (
        Index('ix_location_warehouse', 'warehouse_id'),
        Index('ix_location_available', 'is_available'),
        Index('ix_location_composite', 'warehouse_id', 'code', unique=True),
    )
