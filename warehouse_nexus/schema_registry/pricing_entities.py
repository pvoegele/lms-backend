"""
Pricing Entities - Price list and rule management
Strategic pricing with rule-based calculations
"""
from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, ForeignKey, Date, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from warehouse_nexus.cerebrum.psql_conductor import EntityFoundation
from datetime import datetime
from uuid import uuid4


class PriceList(EntityFoundation):
    """Price list header"""
    __tablename__ = "price_list"
    
    price_list_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('ix_price_list_active', 'is_active'),
    )


class PriceRule(EntityFoundation):
    """Price rule within price list"""
    __tablename__ = "price_rule"
    
    price_rule_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    price_list_id = Column(PG_UUID(as_uuid=True), ForeignKey('price_list.price_list_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey('product.product_id', ondelete='CASCADE'), nullable=True)
    variant_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_variant.variant_id', ondelete='CASCADE'), nullable=True)
    unit_price = Column(Numeric(15, 4), nullable=False)
    min_quantity = Column(Numeric(15, 3), nullable=True)
    discount_percent = Column(Numeric(5, 2), nullable=True)
    priority = Column(String(10), default="medium", nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    price_list = relationship("PriceList", backref="price_rules")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    
    __table_args__ = (
        Index('ix_price_rule_list', 'price_list_id'),
        Index('ix_price_rule_product', 'product_id'),
        Index('ix_price_rule_variant', 'variant_id'),
    )
