"""
Product API Gateway - HTTP endpoints for product management
RESTful routes for CRUD operations on products
"""
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session as SQLSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from warehouse_nexus.cerebrum.psql_conductor import harvest_session
from warehouse_nexus.schema_registry.core_entities import (
    UnitOfMeasure,
    ProductCategory,
    Product,
    ProductVariant
)
from warehouse_nexus.data_contracts.core_contracts import (
    UnitOfMeasureCreate,
    UnitOfMeasureResponse,
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCreate,
    ProductResponse,
    ProductVariantCreate,
    ProductVariantResponse
)


product_gateway = APIRouter(prefix="/products", tags=["Products"])


@product_gateway.post(
    "/uom",
    response_model=UnitOfMeasureResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_unit_of_measure(
    payload: UnitOfMeasureCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create new unit of measure"""
    new_uom = UnitOfMeasure(**payload.model_dump())
    db.add(new_uom)
    db.commit()
    db.refresh(new_uom)
    return new_uom


@product_gateway.get(
    "/uom",
    response_model=List[UnitOfMeasureResponse]
)
def list_units_of_measure(
    skip: int = 0,
    limit: int = 100,
    db: SQLSession = Depends(harvest_session)
):
    """List units of measure"""
    stmt = select(UnitOfMeasure).offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@product_gateway.post(
    "/categories",
    response_model=ProductCategoryResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_category(
    payload: ProductCategoryCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create product category"""
    new_category = ProductCategory(**payload.model_dump())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@product_gateway.get(
    "/categories",
    response_model=List[ProductCategoryResponse]
)
def list_categories(
    skip: int = 0,
    limit: int = 100,
    db: SQLSession = Depends(harvest_session)
):
    """List product categories"""
    stmt = select(ProductCategory).offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@product_gateway.post(
    "/",
    response_model=ProductResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_product(
    payload: ProductCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create new product"""
    new_product = Product(**payload.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@product_gateway.get(
    "/",
    response_model=List[ProductResponse]
)
def list_products(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: SQLSession = Depends(harvest_session)
):
    """List products"""
    stmt = select(Product)
    if active_only:
        stmt = stmt.where(Product.is_active)
    stmt = stmt.offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@product_gateway.get(
    "/{product_id}",
    response_model=ProductResponse
)
def get_product(
    product_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Get single product"""
    stmt = select(Product).where(Product.product_id == product_id)
    product = db.execute(stmt).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
    return product


@product_gateway.post(
    "/variants",
    response_model=ProductVariantResponse,
    status_code=http_status.HTTP_201_CREATED
)
def create_variant(
    payload: ProductVariantCreate,
    db: SQLSession = Depends(harvest_session)
):
    """Create product variant"""
    new_variant = ProductVariant(**payload.model_dump())
    db.add(new_variant)
    db.commit()
    db.refresh(new_variant)
    return new_variant


@product_gateway.get(
    "/{product_id}/variants",
    response_model=List[ProductVariantResponse]
)
def list_product_variants(
    product_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """List variants for product"""
    stmt = select(ProductVariant).where(ProductVariant.product_id == product_id)
    results = db.execute(stmt).scalars().all()
    return results
