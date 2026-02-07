"""
Audit Entities - Stocktake and system audit trail
Physical inventory verification and comprehensive logging
"""
from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from warehouse_nexus.cerebrum.psql_conductor import EntityFoundation
from datetime import datetime
from uuid import uuid4


class Stocktake(EntityFoundation):
    """Stocktake/physical count header"""
    __tablename__ = "stocktake"
    
    stocktake_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    reference = Column(String(100), unique=True, nullable=False, index=True)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey('warehouse.warehouse_id', ondelete='SET NULL'), nullable=True)
    count_date = Column(Date, nullable=False)
    completed_date = Column(Date, nullable=True)
    is_finalized = Column(Boolean, default=False, nullable=False)
    supervisor = Column(String(150), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Note: Warehouse relationship temporarily removed to fix SQLAlchemy configuration issues
    # warehouse = relationship("Warehouse")
    
    __table_args__ = (
        Index('ix_stocktake_warehouse', 'warehouse_id'),
        Index('ix_stocktake_finalized', 'is_finalized'),
    )


class StocktakeLine(EntityFoundation):
    """Stocktake line item"""
    __tablename__ = "stocktake_line"
    
    line_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    stocktake_id = Column(PG_UUID(as_uuid=True), ForeignKey('stocktake.stocktake_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey('product.product_id', ondelete='SET NULL'), nullable=True)
    variant_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_variant.variant_id', ondelete='SET NULL'), nullable=True)
    location_id = Column(PG_UUID(as_uuid=True), ForeignKey('storage_location.location_id', ondelete='SET NULL'), nullable=True)
    lot_id = Column(PG_UUID(as_uuid=True), ForeignKey('lot.lot_id', ondelete='SET NULL'), nullable=True)
    system_quantity = Column(Numeric(15, 3), nullable=False)
    counted_quantity = Column(Numeric(15, 3), nullable=False)
    variance = Column(Numeric(15, 3), nullable=False)
    counter = Column(String(150), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    stocktake = relationship("Stocktake", backref="stocktake_lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    # Note: StorageLocation relationship temporarily removed to fix SQLAlchemy configuration issues
    # location = relationship("StorageLocation")
    lot = relationship("Lot")
    
    __table_args__ = (
        Index('ix_stocktake_line_stocktake', 'stocktake_id'),
    )


class AuditLog(EntityFoundation):
    """System audit log"""
    __tablename__ = "audit_log"
    
    log_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    category = Column(String(100), nullable=False, index=True)
    action = Column(String(250), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(PG_UUID(as_uuid=True), nullable=True)
    user_id = Column(String(150), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    ip_address = Column(String(50), nullable=True)
    extra_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('ix_audit_entity_type', 'entity_type'),
        Index('ix_audit_entity_id', 'entity_id'),
        Index('ix_audit_category', 'category'),
    )
