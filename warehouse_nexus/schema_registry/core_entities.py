"""
Core Warehouse Entities - Foundational domain objects
Units of measure, product hierarchy, and variant management
"""
from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, ForeignKey, Index, func as sql_func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from warehouse_nexus.cerebrum.psql_conductor import EntityFoundation
from datetime import datetime
from uuid import uuid4


def generate_uuid_v4():
    """UUID v4 generator for primary keys"""
    return uuid4()


class UnitOfMeasure(EntityFoundation):
    """Unit of measure registry for quantification"""
    __tablename__ = "unit_of_measure"
    
    unit_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid_v4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    is_base_unit = Column(Boolean, default=False, nullable=False)
    conversion_factor = Column(Numeric(20, 6), nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('ix_uom_category', 'category'),
    )


class ProductCategory(EntityFoundation):
    """Hierarchical product categorization"""
    __tablename__ = "product_category"
    
    category_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid_v4)
    name = Column(String(150), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    parent_category_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_category.category_id', ondelete='SET NULL'), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    parent_category = relationship("ProductCategory", remote_side=[category_id], backref="child_categories")
    
    __table_args__ = (
        Index('ix_category_parent', 'parent_category_id'),
    )


class Product(EntityFoundation):
    """Master product definition"""
    __tablename__ = "product"
    
    product_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid_v4)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(250), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_category.category_id', ondelete='SET NULL'), nullable=True)
    base_uom_id = Column(PG_UUID(as_uuid=True), ForeignKey('unit_of_measure.unit_id'), nullable=False)
    track_by_lot = Column(Boolean, default=False, nullable=False)
    track_by_serial = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    category = relationship("ProductCategory", backref="products")
    base_uom = relationship("UnitOfMeasure")
    
    __table_args__ = (
        Index('ix_product_category', 'category_id'),
        Index('ix_product_active', 'is_active'),
    )


class ProductVariant(EntityFoundation):
    """Product variant with specific attributes"""
    __tablename__ = "product_variant"
    
    variant_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid_v4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey('product.product_id', ondelete='CASCADE'), nullable=False)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(250), nullable=False)
    attributes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    product = relationship("Product", backref="variants")
    
    __table_args__ = (
        Index('ix_variant_product', 'product_id'),
        Index('ix_variant_active', 'is_active'),
    )
