"""
Partner Entities - External relationship management
Supplier and customer business partner records
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from warehouse_nexus.cerebrum.psql_conductor import EntityFoundation
from warehouse_nexus.schema_registry.categorical_taxonomy import PartnerTypeCode
from datetime import datetime
from uuid import uuid4


class Supplier(EntityFoundation):
    """Supplier/vendor business partner"""
    __tablename__ = "supplier"
    
    supplier_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(250), nullable=False, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    partner_type = Column(Enum(PartnerTypeCode, name='partner_type'), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    payment_terms = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('ix_supplier_active', 'is_active'),
    )


class Customer(EntityFoundation):
    """Customer business partner"""
    __tablename__ = "customer"
    
    customer_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(250), nullable=False, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    partner_type = Column(Enum(PartnerTypeCode, name='partner_type'), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    credit_limit = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('ix_customer_active', 'is_active'),
    )
