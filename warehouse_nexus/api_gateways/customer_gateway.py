"""
Customer API Gateway - HTTP endpoints for customer management
RESTful routes for CRUD operations on customer-related entities
"""
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session as SQLSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from warehouse_nexus.cerebrum.psql_conductor import harvest_session
from warehouse_nexus.schema_registry.customer_entities import (
    Country,
    LegalForm,
    AddressType,
    Address,
    PaymentTerm,
    DeliveryCondition,
    ContactPerson,
    ChangeHistory,
    CustomerEntity
)
from warehouse_nexus.data_contracts.customer_contracts import (
    CountryCreate,
    CountryUpdate,
    CountryResponse,
    LegalFormCreate,
    LegalFormUpdate,
    LegalFormResponse,
    AddressTypeCreate,
    AddressTypeUpdate,
    AddressTypeResponse,
    AddressCreate,
    AddressUpdate,
    AddressResponse,
    PaymentTermCreate,
    PaymentTermUpdate,
    PaymentTermResponse,
    DeliveryConditionCreate,
    DeliveryConditionUpdate,
    DeliveryConditionResponse,
    ContactPersonCreate,
    ContactPersonUpdate,
    ContactPersonResponse,
    ChangeHistoryCreate,
    ChangeHistoryResponse,
    CustomerEntityCreate,
    CustomerEntityUpdate,
    CustomerEntityResponse
)


customer_gateway = APIRouter(prefix="/customers", tags=["Customers"])


# ============================================================================
# Country Endpoints
# ============================================================================

@customer_gateway.post(
    "/countries",
    response_model=CountryResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_country(
    payload: CountryCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create new country"""
    new_country = Country(**payload.model_dump())
    db.add(new_country)
    db.commit()
    db.refresh(new_country)
    return new_country


@customer_gateway.get(
    "/countries",
    response_model=List[CountryResponse]
)
def list_countries(
    skip: int = 0,
    limit: int = 100,
    db: SQLSession = Depends(harvest_session)
):
    """List all countries"""
    stmt = select(Country).offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@customer_gateway.get(
    "/countries/{country_id}",
    response_model=CountryResponse
)
def get_country(
    country_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Get single country"""
    stmt = select(Country).where(Country.uuid == country_id)
    country = db.execute(stmt).scalar_one_or_none()
    if not country:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Country {country_id} not found"
        )
    return country


@customer_gateway.put(
    "/countries/{country_id}",
    response_model=CountryResponse
)
def update_country(
    country_id: UUID,
    payload: CountryUpdate,
    db: SQLSession = Depends(harvest_session)
):
    """Update country"""
    stmt = select(Country).where(Country.uuid == country_id)
    country = db.execute(stmt).scalar_one_or_none()
    if not country:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Country {country_id} not found"
        )
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(country, field, value)
    
    db.commit()
    db.refresh(country)
    return country


@customer_gateway.delete(
    "/countries/{country_id}",
    status_code=http_status.HTTP_204_NO_CONTENT
)
def delete_country(
    country_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Delete country"""
    stmt = select(Country).where(Country.uuid == country_id)
    country = db.execute(stmt).scalar_one_or_none()
    if not country:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Country {country_id} not found"
        )
    db.delete(country)
    db.commit()
    return None


# ============================================================================
# Legal Form Endpoints
# ============================================================================

@customer_gateway.post(
    "/legal-forms",
    response_model=LegalFormResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_legal_form(
    payload: LegalFormCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create new legal form"""
    new_legal_form = LegalForm(**payload.model_dump())
    db.add(new_legal_form)
    db.commit()
    db.refresh(new_legal_form)
    return new_legal_form


@customer_gateway.get(
    "/legal-forms",
    response_model=List[LegalFormResponse]
)
def list_legal_forms(
    skip: int = 0,
    limit: int = 100,
    country_id: UUID = None,
    db: SQLSession = Depends(harvest_session)
):
    """List all legal forms, optionally filtered by country"""
    stmt = select(LegalForm)
    if country_id:
        stmt = stmt.where(LegalForm.country_uuid == country_id)
    stmt = stmt.offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@customer_gateway.get(
    "/legal-forms/{legal_form_id}",
    response_model=LegalFormResponse
)
def get_legal_form(
    legal_form_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Get single legal form"""
    stmt = select(LegalForm).where(LegalForm.uuid == legal_form_id)
    legal_form = db.execute(stmt).scalar_one_or_none()
    if not legal_form:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Legal form {legal_form_id} not found"
        )
    return legal_form


@customer_gateway.put(
    "/legal-forms/{legal_form_id}",
    response_model=LegalFormResponse
)
def update_legal_form(
    legal_form_id: UUID,
    payload: LegalFormUpdate,
    db: SQLSession = Depends(harvest_session)
):
    """Update legal form"""
    stmt = select(LegalForm).where(LegalForm.uuid == legal_form_id)
    legal_form = db.execute(stmt).scalar_one_or_none()
    if not legal_form:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Legal form {legal_form_id} not found"
        )
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(legal_form, field, value)
    
    db.commit()
    db.refresh(legal_form)
    return legal_form


@customer_gateway.delete(
    "/legal-forms/{legal_form_id}",
    status_code=http_status.HTTP_204_NO_CONTENT
)
def delete_legal_form(
    legal_form_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Delete legal form"""
    stmt = select(LegalForm).where(LegalForm.uuid == legal_form_id)
    legal_form = db.execute(stmt).scalar_one_or_none()
    if not legal_form:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Legal form {legal_form_id} not found"
        )
    db.delete(legal_form)
    db.commit()
    return None


# ============================================================================
# Address Type Endpoints
# ============================================================================

@customer_gateway.post(
    "/address-types",
    response_model=AddressTypeResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_address_type(
    payload: AddressTypeCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create new address type"""
    new_address_type = AddressType(**payload.model_dump())
    db.add(new_address_type)
    db.commit()
    db.refresh(new_address_type)
    return new_address_type


@customer_gateway.get(
    "/address-types",
    response_model=List[AddressTypeResponse]
)
def list_address_types(
    skip: int = 0,
    limit: int = 100,
    db: SQLSession = Depends(harvest_session)
):
    """List all address types"""
    stmt = select(AddressType).offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@customer_gateway.get(
    "/address-types/{address_type_id}",
    response_model=AddressTypeResponse
)
def get_address_type(
    address_type_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Get single address type"""
    stmt = select(AddressType).where(AddressType.uuid == address_type_id)
    address_type = db.execute(stmt).scalar_one_or_none()
    if not address_type:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Address type {address_type_id} not found"
        )
    return address_type


@customer_gateway.put(
    "/address-types/{address_type_id}",
    response_model=AddressTypeResponse
)
def update_address_type(
    address_type_id: UUID,
    payload: AddressTypeUpdate,
    db: SQLSession = Depends(harvest_session)
):
    """Update address type"""
    stmt = select(AddressType).where(AddressType.uuid == address_type_id)
    address_type = db.execute(stmt).scalar_one_or_none()
    if not address_type:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Address type {address_type_id} not found"
        )
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(address_type, field, value)
    
    db.commit()
    db.refresh(address_type)
    return address_type


@customer_gateway.delete(
    "/address-types/{address_type_id}",
    status_code=http_status.HTTP_204_NO_CONTENT
)
def delete_address_type(
    address_type_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Delete address type"""
    stmt = select(AddressType).where(AddressType.uuid == address_type_id)
    address_type = db.execute(stmt).scalar_one_or_none()
    if not address_type:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Address type {address_type_id} not found"
        )
    db.delete(address_type)
    db.commit()
    return None


# ============================================================================
# Address Endpoints
# ============================================================================

@customer_gateway.post(
    "/addresses",
    response_model=AddressResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_address(
    payload: AddressCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create new address"""
    new_address = Address(**payload.model_dump())
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address


@customer_gateway.get(
    "/addresses",
    response_model=List[AddressResponse]
)
def list_addresses(
    skip: int = 0,
    limit: int = 100,
    customer_id: UUID = None,
    db: SQLSession = Depends(harvest_session)
):
    """List all addresses, optionally filtered by customer"""
    stmt = select(Address)
    if customer_id:
        stmt = stmt.where(Address.customer_uuid == customer_id)
    stmt = stmt.offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@customer_gateway.get(
    "/addresses/{address_id}",
    response_model=AddressResponse
)
def get_address(
    address_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Get single address"""
    stmt = select(Address).where(Address.uuid == address_id)
    address = db.execute(stmt).scalar_one_or_none()
    if not address:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Address {address_id} not found"
        )
    return address


@customer_gateway.put(
    "/addresses/{address_id}",
    response_model=AddressResponse
)
def update_address(
    address_id: UUID,
    payload: AddressUpdate,
    db: SQLSession = Depends(harvest_session)
):
    """Update address"""
    stmt = select(Address).where(Address.uuid == address_id)
    address = db.execute(stmt).scalar_one_or_none()
    if not address:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Address {address_id} not found"
        )
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(address, field, value)
    
    db.commit()
    db.refresh(address)
    return address


@customer_gateway.delete(
    "/addresses/{address_id}",
    status_code=http_status.HTTP_204_NO_CONTENT
)
def delete_address(
    address_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Delete address"""
    stmt = select(Address).where(Address.uuid == address_id)
    address = db.execute(stmt).scalar_one_or_none()
    if not address:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Address {address_id} not found"
        )
    db.delete(address)
    db.commit()
    return None


# ============================================================================
# Payment Term Endpoints
# ============================================================================

@customer_gateway.post(
    "/payment-terms",
    response_model=PaymentTermResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_payment_term(
    payload: PaymentTermCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create new payment term"""
    new_payment_term = PaymentTerm(**payload.model_dump())
    db.add(new_payment_term)
    db.commit()
    db.refresh(new_payment_term)
    return new_payment_term


@customer_gateway.get(
    "/payment-terms",
    response_model=List[PaymentTermResponse]
)
def list_payment_terms(
    skip: int = 0,
    limit: int = 100,
    db: SQLSession = Depends(harvest_session)
):
    """List all payment terms"""
    stmt = select(PaymentTerm).offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@customer_gateway.get(
    "/payment-terms/{payment_term_id}",
    response_model=PaymentTermResponse
)
def get_payment_term(
    payment_term_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Get single payment term"""
    stmt = select(PaymentTerm).where(PaymentTerm.uuid == payment_term_id)
    payment_term = db.execute(stmt).scalar_one_or_none()
    if not payment_term:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Payment term {payment_term_id} not found"
        )
    return payment_term


@customer_gateway.put(
    "/payment-terms/{payment_term_id}",
    response_model=PaymentTermResponse
)
def update_payment_term(
    payment_term_id: UUID,
    payload: PaymentTermUpdate,
    db: SQLSession = Depends(harvest_session)
):
    """Update payment term"""
    stmt = select(PaymentTerm).where(PaymentTerm.uuid == payment_term_id)
    payment_term = db.execute(stmt).scalar_one_or_none()
    if not payment_term:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Payment term {payment_term_id} not found"
        )
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(payment_term, field, value)
    
    db.commit()
    db.refresh(payment_term)
    return payment_term


@customer_gateway.delete(
    "/payment-terms/{payment_term_id}",
    status_code=http_status.HTTP_204_NO_CONTENT
)
def delete_payment_term(
    payment_term_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Delete payment term"""
    stmt = select(PaymentTerm).where(PaymentTerm.uuid == payment_term_id)
    payment_term = db.execute(stmt).scalar_one_or_none()
    if not payment_term:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Payment term {payment_term_id} not found"
        )
    db.delete(payment_term)
    db.commit()
    return None


# ============================================================================
# Delivery Condition Endpoints
# ============================================================================

@customer_gateway.post(
    "/delivery-conditions",
    response_model=DeliveryConditionResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_delivery_condition(
    payload: DeliveryConditionCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create new delivery condition"""
    new_delivery_condition = DeliveryCondition(**payload.model_dump())
    db.add(new_delivery_condition)
    db.commit()
    db.refresh(new_delivery_condition)
    return new_delivery_condition


@customer_gateway.get(
    "/delivery-conditions",
    response_model=List[DeliveryConditionResponse]
)
def list_delivery_conditions(
    skip: int = 0,
    limit: int = 100,
    db: SQLSession = Depends(harvest_session)
):
    """List all delivery conditions"""
    stmt = select(DeliveryCondition).offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@customer_gateway.get(
    "/delivery-conditions/{delivery_condition_id}",
    response_model=DeliveryConditionResponse
)
def get_delivery_condition(
    delivery_condition_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Get single delivery condition"""
    stmt = select(DeliveryCondition).where(DeliveryCondition.uuid == delivery_condition_id)
    delivery_condition = db.execute(stmt).scalar_one_or_none()
    if not delivery_condition:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Delivery condition {delivery_condition_id} not found"
        )
    return delivery_condition


@customer_gateway.put(
    "/delivery-conditions/{delivery_condition_id}",
    response_model=DeliveryConditionResponse
)
def update_delivery_condition(
    delivery_condition_id: UUID,
    payload: DeliveryConditionUpdate,
    db: SQLSession = Depends(harvest_session)
):
    """Update delivery condition"""
    stmt = select(DeliveryCondition).where(DeliveryCondition.uuid == delivery_condition_id)
    delivery_condition = db.execute(stmt).scalar_one_or_none()
    if not delivery_condition:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Delivery condition {delivery_condition_id} not found"
        )
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(delivery_condition, field, value)
    
    db.commit()
    db.refresh(delivery_condition)
    return delivery_condition


@customer_gateway.delete(
    "/delivery-conditions/{delivery_condition_id}",
    status_code=http_status.HTTP_204_NO_CONTENT
)
def delete_delivery_condition(
    delivery_condition_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Delete delivery condition"""
    stmt = select(DeliveryCondition).where(DeliveryCondition.uuid == delivery_condition_id)
    delivery_condition = db.execute(stmt).scalar_one_or_none()
    if not delivery_condition:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Delivery condition {delivery_condition_id} not found"
        )
    db.delete(delivery_condition)
    db.commit()
    return None


# ============================================================================
# Contact Person Endpoints
# ============================================================================

@customer_gateway.post(
    "/contact-persons",
    response_model=ContactPersonResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_contact_person(
    payload: ContactPersonCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create new contact person"""
    new_contact_person = ContactPerson(**payload.model_dump())
    db.add(new_contact_person)
    db.commit()
    db.refresh(new_contact_person)
    return new_contact_person


@customer_gateway.get(
    "/contact-persons",
    response_model=List[ContactPersonResponse]
)
def list_contact_persons(
    skip: int = 0,
    limit: int = 100,
    customer_id: UUID = None,
    db: SQLSession = Depends(harvest_session)
):
    """List all contact persons, optionally filtered by customer"""
    stmt = select(ContactPerson)
    if customer_id:
        stmt = stmt.where(ContactPerson.customer_uuid == customer_id)
    stmt = stmt.offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@customer_gateway.get(
    "/contact-persons/{contact_person_id}",
    response_model=ContactPersonResponse
)
def get_contact_person(
    contact_person_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Get single contact person"""
    stmt = select(ContactPerson).where(ContactPerson.uuid == contact_person_id)
    contact_person = db.execute(stmt).scalar_one_or_none()
    if not contact_person:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Contact person {contact_person_id} not found"
        )
    return contact_person


@customer_gateway.put(
    "/contact-persons/{contact_person_id}",
    response_model=ContactPersonResponse
)
def update_contact_person(
    contact_person_id: UUID,
    payload: ContactPersonUpdate,
    db: SQLSession = Depends(harvest_session)
):
    """Update contact person"""
    stmt = select(ContactPerson).where(ContactPerson.uuid == contact_person_id)
    contact_person = db.execute(stmt).scalar_one_or_none()
    if not contact_person:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Contact person {contact_person_id} not found"
        )
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact_person, field, value)
    
    db.commit()
    db.refresh(contact_person)
    return contact_person


@customer_gateway.delete(
    "/contact-persons/{contact_person_id}",
    status_code=http_status.HTTP_204_NO_CONTENT
)
def delete_contact_person(
    contact_person_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Delete contact person"""
    stmt = select(ContactPerson).where(ContactPerson.uuid == contact_person_id)
    contact_person = db.execute(stmt).scalar_one_or_none()
    if not contact_person:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Contact person {contact_person_id} not found"
        )
    db.delete(contact_person)
    db.commit()
    return None


# ============================================================================
# Change History Endpoints
# ============================================================================

@customer_gateway.post(
    "/change-history",
    response_model=ChangeHistoryResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_change_history(
    payload: ChangeHistoryCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create new change history record"""
    new_change_history = ChangeHistory(**payload.model_dump())
    db.add(new_change_history)
    db.commit()
    db.refresh(new_change_history)
    return new_change_history


@customer_gateway.get(
    "/change-history",
    response_model=List[ChangeHistoryResponse]
)
def list_change_history(
    skip: int = 0,
    limit: int = 100,
    customer_id: UUID = None,
    db: SQLSession = Depends(harvest_session)
):
    """List change history, optionally filtered by customer"""
    stmt = select(ChangeHistory)
    if customer_id:
        stmt = stmt.where(ChangeHistory.customer_uuid == customer_id)
    stmt = stmt.offset(skip).limit(limit).order_by(ChangeHistory.changed_at.desc())
    results = db.execute(stmt).scalars().all()
    return results


# ============================================================================
# Customer Entity Endpoints
# ============================================================================

@customer_gateway.post(
    "/",
    response_model=CustomerEntityResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_customer(
    payload: CustomerEntityCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create new customer"""
    new_customer = CustomerEntity(**payload.model_dump())
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


@customer_gateway.get(
    "/",
    response_model=List[CustomerEntityResponse]
)
def list_customers(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: SQLSession = Depends(harvest_session)
):
    """List all customers"""
    stmt = select(CustomerEntity)
    if active_only:
        stmt = stmt.where(CustomerEntity.is_active)
    stmt = stmt.offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@customer_gateway.get(
    "/{customer_id}",
    response_model=CustomerEntityResponse
)
def get_customer(
    customer_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Get single customer"""
    stmt = select(CustomerEntity).where(CustomerEntity.uuid == customer_id)
    customer = db.execute(stmt).scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )
    return customer


@customer_gateway.put(
    "/{customer_id}",
    response_model=CustomerEntityResponse
)
def update_customer(
    customer_id: UUID,
    payload: CustomerEntityUpdate,
    db: SQLSession = Depends(harvest_session)
):
    """Update customer"""
    stmt = select(CustomerEntity).where(CustomerEntity.uuid == customer_id)
    customer = db.execute(stmt).scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    
    db.commit()
    db.refresh(customer)
    return customer


@customer_gateway.delete(
    "/{customer_id}",
    status_code=http_status.HTTP_204_NO_CONTENT
)
def delete_customer(
    customer_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Delete customer"""
    stmt = select(CustomerEntity).where(CustomerEntity.uuid == customer_id)
    customer = db.execute(stmt).scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )
    db.delete(customer)
    db.commit()
    return None
