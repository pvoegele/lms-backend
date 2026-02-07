"""
Customer Data Contracts - Pydantic models for customer domain
Request/Response validation schemas for customer-related entities
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============================================================================
# Country Schemas
# ============================================================================

class CountryCreate(BaseModel):
    name: str = Field(..., max_length=200)
    country_code: str = Field(..., max_length=10)
    phone_pre: Optional[str] = Field(None, max_length=10)
    field: Optional[str] = Field(None, max_length=100)


class CountryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    country_code: Optional[str] = Field(None, max_length=10)
    phone_pre: Optional[str] = Field(None, max_length=10)
    field: Optional[str] = Field(None, max_length=100)


class CountryResponse(CountryCreate):
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Legal Form Schemas
# ============================================================================

class LegalFormCreate(BaseModel):
    name: str = Field(..., max_length=200)
    country_uuid: UUID


class LegalFormUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    country_uuid: Optional[UUID] = None


class LegalFormResponse(LegalFormCreate):
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Address Type Schemas
# ============================================================================

class AddressTypeCreate(BaseModel):
    name: str = Field(..., max_length=100)


class AddressTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)


class AddressTypeResponse(AddressTypeCreate):
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Address Schemas
# ============================================================================

class AddressCreate(BaseModel):
    description: Optional[str] = Field(None, max_length=200)
    street: str = Field(..., max_length=200)
    house_number: Optional[str] = Field(None, max_length=20)
    postal_code: Optional[str] = Field(None, max_length=20)
    city: str = Field(..., max_length=150)
    country_uuid: UUID
    customer_uuid: Optional[UUID] = None
    type_uuid: UUID


class AddressUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=200)
    street: Optional[str] = Field(None, max_length=200)
    house_number: Optional[str] = Field(None, max_length=20)
    postal_code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=150)
    country_uuid: Optional[UUID] = None
    customer_uuid: Optional[UUID] = None
    type_uuid: Optional[UUID] = None


class AddressResponse(AddressCreate):
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Payment Term Schemas
# ============================================================================

class PaymentTermCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    days_due: Optional[str] = Field(None, max_length=20)
    discount_percent: Optional[str] = Field(None, max_length=20)


class PaymentTermUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    days_due: Optional[str] = Field(None, max_length=20)
    discount_percent: Optional[str] = Field(None, max_length=20)


class PaymentTermResponse(PaymentTermCreate):
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Delivery Condition Schemas
# ============================================================================

class DeliveryConditionCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None


class DeliveryConditionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None


class DeliveryConditionResponse(DeliveryConditionCreate):
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Contact Person Schemas
# ============================================================================

class ContactPersonCreate(BaseModel):
    customer_uuid: UUID
    name: str = Field(..., max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    position: Optional[str] = Field(None, max_length=100)
    is_primary: bool = False


class ContactPersonUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    position: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = None


class ContactPersonResponse(ContactPersonCreate):
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Change History Schemas
# ============================================================================

class ChangeHistoryCreate(BaseModel):
    customer_uuid: UUID
    field_name: str = Field(..., max_length=100)
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: Optional[str] = Field(None, max_length=200)


class ChangeHistoryResponse(ChangeHistoryCreate):
    uuid: UUID
    changed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Customer Entity Schemas
# ============================================================================

class CustomerEntityCreate(BaseModel):
    name: str = Field(..., max_length=250)
    email_address: Optional[str] = Field(None, max_length=200)
    firm_name: Optional[str] = Field(None, max_length=250)
    vat_id: Optional[str] = Field(None, max_length=50)
    tax_number: Optional[str] = Field(None, max_length=50)
    tax_country_uuid: Optional[UUID] = None
    legal_form_uuid: Optional[UUID] = None
    payment_term_uuid: Optional[UUID] = None
    delivery_condition_uuid: Optional[UUID] = None
    is_active: bool = True


class CustomerEntityUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=250)
    email_address: Optional[str] = Field(None, max_length=200)
    firm_name: Optional[str] = Field(None, max_length=250)
    vat_id: Optional[str] = Field(None, max_length=50)
    tax_number: Optional[str] = Field(None, max_length=50)
    tax_country_uuid: Optional[UUID] = None
    legal_form_uuid: Optional[UUID] = None
    payment_term_uuid: Optional[UUID] = None
    delivery_condition_uuid: Optional[UUID] = None
    is_active: Optional[bool] = None


class CustomerEntityResponse(CustomerEntityCreate):
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
