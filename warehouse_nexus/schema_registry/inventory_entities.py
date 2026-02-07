"""
Inventory Entities - Balance tracking and reservations
Real-time inventory state with lot and serial tracking
"""
from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, Date, ForeignKey, Enum, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from warehouse_nexus.cerebrum.psql_conductor import EntityFoundation
from warehouse_nexus.schema_registry.categorical_taxonomy import ReservationStateCode, SerialStateCode
from datetime import datetime
from uuid import uuid4


class InventoryBalance(EntityFoundation):
    """Inventory balance by location"""
    __tablename__ = "inventory_balance"
    
    balance_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey('product.product_id', ondelete='CASCADE'), nullable=True)
    variant_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_variant.variant_id', ondelete='CASCADE'), nullable=True)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey('warehouse.warehouse_id', ondelete='CASCADE'), nullable=False)
    location_id = Column(PG_UUID(as_uuid=True), ForeignKey('storage_location.location_id', ondelete='CASCADE'), nullable=True)
    lot_id = Column(PG_UUID(as_uuid=True), ForeignKey('lot.lot_id', ondelete='SET NULL'), nullable=True)
    quantity_on_hand = Column(Numeric(15, 3), nullable=False, default=0)
    quantity_reserved = Column(Numeric(15, 3), nullable=False, default=0)
    quantity_available = Column(Numeric(15, 3), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    product = relationship("Product")
    variant = relationship("ProductVariant")
    # Note: Warehouse/StorageLocation relationships temporarily removed to fix SQLAlchemy configuration issues
    # warehouse = relationship("Warehouse")
    # location = relationship("StorageLocation")
    lot = relationship("Lot")
    
    __table_args__ = (
        Index('ix_balance_product', 'product_id'),
        Index('ix_balance_variant', 'variant_id'),
        Index('ix_balance_warehouse', 'warehouse_id'),
        Index('ix_balance_location', 'location_id'),
        Index('ix_balance_composite', 'product_id', 'variant_id', 'warehouse_id', 'location_id', 'lot_id'),
        CheckConstraint('quantity_on_hand >= 0', name='chk_qoh_positive'),
        CheckConstraint('quantity_reserved >= 0', name='chk_reserved_positive'),
    )


class InventoryReservation(EntityFoundation):
    """Inventory reservation record"""
    __tablename__ = "inventory_reservation"
    
    reservation_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey('product.product_id', ondelete='CASCADE'), nullable=True)
    variant_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_variant.variant_id', ondelete='CASCADE'), nullable=True)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey('warehouse.warehouse_id', ondelete='CASCADE'), nullable=False)
    location_id = Column(PG_UUID(as_uuid=True), ForeignKey('storage_location.location_id', ondelete='CASCADE'), nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    status = Column(Enum(ReservationStateCode, name='reservation_status'), nullable=False, default=ReservationStateCode.ACTIVE)
    reference = Column(String(100), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    product = relationship("Product")
    variant = relationship("ProductVariant")
    # Note: Warehouse/StorageLocation relationships temporarily removed to fix SQLAlchemy configuration issues
    # warehouse = relationship("Warehouse")
    # location = relationship("StorageLocation")
    
    __table_args__ = (
        Index('ix_reservation_product', 'product_id'),
        Index('ix_reservation_status', 'status'),
        Index('ix_reservation_warehouse', 'warehouse_id'),
    )


class Lot(EntityFoundation):
    """Lot/batch tracking"""
    __tablename__ = "lot"
    
    lot_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    lot_number = Column(String(100), nullable=False, index=True)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey('product.product_id', ondelete='CASCADE'), nullable=True)
    variant_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_variant.variant_id', ondelete='CASCADE'), nullable=True)
    manufactured_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    supplier_id = Column(PG_UUID(as_uuid=True), ForeignKey('supplier.supplier_id', ondelete='SET NULL'), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    product = relationship("Product")
    variant = relationship("ProductVariant")
    # Note: Supplier relationship temporarily removed to fix SQLAlchemy configuration issues  
    # supplier = relationship("Supplier", viewonly=True)
    
    __table_args__ = (
        Index('ix_lot_product', 'product_id'),
        Index('ix_lot_variant', 'variant_id'),
        Index('ix_lot_expiry', 'expiry_date'),
    )


class SerialNumber(EntityFoundation):
    """Serial number tracking"""
    __tablename__ = "serial_number"
    
    serial_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    serial_number = Column(String(100), unique=True, nullable=False, index=True)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey('product.product_id', ondelete='CASCADE'), nullable=True)
    variant_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_variant.variant_id', ondelete='CASCADE'), nullable=True)
    lot_id = Column(PG_UUID(as_uuid=True), ForeignKey('lot.lot_id', ondelete='SET NULL'), nullable=True)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey('warehouse.warehouse_id', ondelete='SET NULL'), nullable=True)
    location_id = Column(PG_UUID(as_uuid=True), ForeignKey('storage_location.location_id', ondelete='SET NULL'), nullable=True)
    status = Column(Enum(SerialStateCode, name='serial_status'), nullable=False, default=SerialStateCode.IN_STOCK)
    warranty_expiry = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    product = relationship("Product")
    variant = relationship("ProductVariant")
    lot = relationship("Lot")
    # Note: Warehouse/StorageLocation relationships temporarily removed to fix SQLAlchemy configuration issues
    # warehouse = relationship("Warehouse")
    # location = relationship("StorageLocation")
    
    __table_args__ = (
        Index('ix_serial_product', 'product_id'),
        Index('ix_serial_status', 'status'),
        Index('ix_serial_warehouse', 'warehouse_id'),
    )
