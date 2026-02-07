"""
Customer Domain Entities - Customer relationship management
Models for customers, addresses, countries, legal forms and related entities
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from warehouse_nexus.cerebrum.psql_conductor import EntityFoundation
from datetime import datetime
from uuid import uuid4


class Country(EntityFoundation):
    """Country master data with phone prefix"""
    __tablename__ = "country"
    
    uuid = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False, index=True)
    country_code = Column(String(10), unique=True, nullable=False, index=True)
    phone_pre = Column(String(10), nullable=True)
    field = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    legal_forms = relationship("LegalForm", back_populates="country")
    addresses = relationship("Address", foreign_keys="Address.country_uuid", back_populates="country")
    customers_tax = relationship("CustomerEntity", foreign_keys="CustomerEntity.tax_country_uuid", back_populates="tax_country")


class LegalForm(EntityFoundation):
    """Legal forms associated with countries"""
    __tablename__ = "legal_form"
    
    uuid = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False, index=True)
    country_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("country.uuid"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    country = relationship("Country", back_populates="legal_forms")
    customers = relationship("CustomerEntity", back_populates="legal_form")
    
    __table_args__ = (
        Index('ix_legal_form_country', 'country_uuid'),
    )


class AddressType(EntityFoundation):
    """Types of addresses (billing, shipping, etc.)"""
    __tablename__ = "address_type"
    
    uuid = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    addresses = relationship("Address", back_populates="address_type")


class Address(EntityFoundation):
    """Address information with full location details"""
    __tablename__ = "address"
    
    uuid = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    description = Column(String(200), nullable=True)
    street = Column(String(200), nullable=False)
    house_number = Column(String(20), nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(150), nullable=False)
    country_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("country.uuid"), nullable=False)
    customer_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("customer_entity.uuid"), nullable=True)
    type_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("address_type.uuid"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    country = relationship("Country", foreign_keys=[country_uuid], back_populates="addresses")
    customer = relationship("CustomerEntity", foreign_keys=[customer_uuid], back_populates="addresses")
    address_type = relationship("AddressType", back_populates="addresses")
    
    __table_args__ = (
        Index('ix_address_customer', 'customer_uuid'),
        Index('ix_address_country', 'country_uuid'),
        Index('ix_address_type', 'type_uuid'),
    )


class PaymentTerm(EntityFoundation):
    """Payment terms and conditions"""
    __tablename__ = "payment_term"
    
    uuid = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    days_due = Column(String(20), nullable=True)
    discount_percent = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    customers = relationship("CustomerEntity", back_populates="payment_term")


class DeliveryCondition(EntityFoundation):
    """Delivery conditions and terms"""
    __tablename__ = "delivery_condition"
    
    uuid = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    customers = relationship("CustomerEntity", back_populates="delivery_condition")


class ContactPerson(EntityFoundation):
    """Contact persons for customers"""
    __tablename__ = "contact_person"
    
    uuid = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("customer_entity.uuid"), nullable=False)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    position = Column(String(100), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    customer = relationship("CustomerEntity", back_populates="contact_persons")
    
    __table_args__ = (
        Index('ix_contact_person_customer', 'customer_uuid'),
    )


class ChangeHistory(EntityFoundation):
    """Track changes to customer records"""
    __tablename__ = "change_history"
    
    uuid = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("customer_entity.uuid"), nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(String(200), nullable=True)
    changed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    customer = relationship("CustomerEntity", back_populates="change_history")
    
    __table_args__ = (
        Index('ix_change_history_customer', 'customer_uuid'),
        Index('ix_change_history_date', 'changed_at'),
    )


class CustomerEntity(EntityFoundation):
    """Enhanced customer entity with comprehensive business information"""
    __tablename__ = "customer_entity"
    
    uuid = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(250), nullable=False, index=True)
    email_address = Column(String(200), nullable=True)
    firm_name = Column(String(250), nullable=True)
    vat_id = Column(String(50), nullable=True)
    tax_number = Column(String(50), nullable=True)
    tax_country_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("country.uuid"), nullable=True)
    legal_form_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("legal_form.uuid"), nullable=True)
    payment_term_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("payment_term.uuid"), nullable=True)
    delivery_condition_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("delivery_condition.uuid"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    addresses = relationship("Address", foreign_keys="Address.customer_uuid", back_populates="customer")
    tax_country = relationship("Country", foreign_keys=[tax_country_uuid], back_populates="customers_tax")
    legal_form = relationship("LegalForm", back_populates="customers")
    payment_term = relationship("PaymentTerm", back_populates="customers")
    delivery_condition = relationship("DeliveryCondition", back_populates="customers")
    contact_persons = relationship("ContactPerson", back_populates="customer")
    change_history = relationship("ChangeHistory", back_populates="customer")
    
    __table_args__ = (
        Index('ix_customer_entity_active', 'is_active'),
        Index('ix_customer_entity_legal_form', 'legal_form_uuid'),
        Index('ix_customer_entity_tax_country', 'tax_country_uuid'),
    )
