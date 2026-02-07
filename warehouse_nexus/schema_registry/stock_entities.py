"""
Stock Document Entities - Stock movement documentation and transactions
Document-driven inventory flow with materialized movements
"""
from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, Date, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from warehouse_nexus.cerebrum.psql_conductor import EntityFoundation
from warehouse_nexus.schema_registry.categorical_taxonomy import StockDocumentCategory, DocumentStateCode
from datetime import datetime
from uuid import uuid4


class StockDocument(EntityFoundation):
    """Stock document header"""
    __tablename__ = "stock_document"
    
    doc_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    doc_number = Column(String(100), unique=True, nullable=False, index=True)
    doc_type = Column(Enum(StockDocumentCategory, name='doc_type'), nullable=False)
    doc_status = Column(Enum(DocumentStateCode, name='doc_status'), nullable=False, default=DocumentStateCode.DRAFT)
    source_warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey('warehouse.warehouse_id', ondelete='SET NULL'), nullable=True)
    dest_warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey('warehouse.warehouse_id', ondelete='SET NULL'), nullable=True)
    doc_date = Column(Date, nullable=False)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Note: Warehouse relationships temporarily removed to fix SQLAlchemy configuration issues
    # source_warehouse = relationship("Warehouse", foreign_keys=[source_warehouse_id], viewonly=True)
    # dest_warehouse = relationship("Warehouse", foreign_keys=[dest_warehouse_id], viewonly=True)
    
    __table_args__ = (
        Index('ix_stock_doc_type', 'doc_type'),
        Index('ix_stock_doc_status', 'doc_status'),
        Index('ix_stock_doc_source', 'source_warehouse_id'),
    )


class StockDocumentLine(EntityFoundation):
    """Stock document line item"""
    __tablename__ = "stock_document_line"
    
    line_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    doc_id = Column(PG_UUID(as_uuid=True), ForeignKey('stock_document.doc_id', ondelete='CASCADE'), nullable=False)
    line_number = Column(String(10), nullable=False)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey('product.product_id', ondelete='SET NULL'), nullable=True)
    variant_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_variant.variant_id', ondelete='SET NULL'), nullable=True)
    lot_id = Column(PG_UUID(as_uuid=True), ForeignKey('lot.lot_id', ondelete='SET NULL'), nullable=True)
    source_location_id = Column(PG_UUID(as_uuid=True), ForeignKey('storage_location.location_id', ondelete='SET NULL'), nullable=True)
    dest_location_id = Column(PG_UUID(as_uuid=True), ForeignKey('storage_location.location_id', ondelete='SET NULL'), nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    uom_id = Column(PG_UUID(as_uuid=True), ForeignKey('unit_of_measure.unit_id'), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    stock_document = relationship("StockDocument", backref="document_lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    lot = relationship("Lot")
    # Note: StorageLocation relationships temporarily removed to fix SQLAlchemy configuration issues
    # source_location = relationship("StorageLocation", foreign_keys=[source_location_id])
    # dest_location = relationship("StorageLocation", foreign_keys=[dest_location_id])
    uom = relationship("UnitOfMeasure")
    
    __table_args__ = (
        Index('ix_stock_line_doc', 'doc_id'),
    )


class StockMovement(EntityFoundation):
    """Materialized stock movement transaction"""
    __tablename__ = "stock_movement"
    
    movement_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    doc_id = Column(PG_UUID(as_uuid=True), ForeignKey('stock_document.doc_id', ondelete='SET NULL'), nullable=True)
    line_id = Column(PG_UUID(as_uuid=True), ForeignKey('stock_document_line.line_id', ondelete='SET NULL'), nullable=True)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey('product.product_id', ondelete='CASCADE'), nullable=True)
    variant_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_variant.variant_id', ondelete='CASCADE'), nullable=True)
    lot_id = Column(PG_UUID(as_uuid=True), ForeignKey('lot.lot_id', ondelete='SET NULL'), nullable=True)
    source_warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey('warehouse.warehouse_id', ondelete='SET NULL'), nullable=True)
    source_location_id = Column(PG_UUID(as_uuid=True), ForeignKey('storage_location.location_id', ondelete='SET NULL'), nullable=True)
    dest_warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey('warehouse.warehouse_id', ondelete='SET NULL'), nullable=True)
    dest_location_id = Column(PG_UUID(as_uuid=True), ForeignKey('storage_location.location_id', ondelete='SET NULL'), nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    movement_timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    stock_document = relationship("StockDocument", viewonly=True)
    document_line = relationship("StockDocumentLine", viewonly=True)
    product = relationship("Product", viewonly=True)
    variant = relationship("ProductVariant", viewonly=True)
    lot = relationship("Lot", viewonly=True)
    # Note: Warehouse and StorageLocation relationships temporarily removed to fix SQLAlchemy configuration issues
    # source_warehouse = relationship("Warehouse", foreign_keys=[source_warehouse_id], viewonly=True)
    # source_location = relationship("StorageLocation", foreign_keys=[source_location_id], viewonly=True)
    # dest_warehouse = relationship("Warehouse", foreign_keys=[dest_warehouse_id], viewonly=True)
    # dest_location = relationship("StorageLocation", foreign_keys=[dest_location_id], viewonly=True)
    
    __table_args__ = (
        Index('ix_movement_doc', 'doc_id'),
        Index('ix_movement_product', 'product_id'),
        Index('ix_movement_timestamp', 'movement_timestamp'),
        Index('ix_movement_source_wh', 'source_warehouse_id'),
        Index('ix_movement_dest_wh', 'dest_warehouse_id'),
    )
