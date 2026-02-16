"""
Product API Gateway - RESTful HTTP Endpoints for Product Management
===================================================================

This module implements the HTTP API layer for product-related operations,
providing RESTful endpoints for:
- Unit of measure CRUD
- Product category CRUD
- Product CRUD
- Product variant CRUD

Architecture:
This gateway follows the API Gateway pattern, serving as the entry point
for all product-related HTTP requests. It:
1. Validates incoming requests (via Pydantic models)
2. Injects database sessions (via dependency injection)
3. Delegates to repository layer (SQLAlchemy ORM)
4. Transforms responses (ORM → Pydantic)
5. Handles errors (404, 422, 500)

RESTful Design:
- POST for creation (201 Created)
- GET for retrieval (200 OK)
- PUT/PATCH for updates (200 OK)
- DELETE for removal (204 No Content)
- Proper HTTP status codes
- Resource-oriented URLs

All endpoints are automatically documented in:
- Swagger UI: /api/v1/docs
- ReDoc: /api/v1/redoc
- OpenAPI JSON: /api/v1/openapi.json

Authentication:
Currently no authentication is implemented. All endpoints are public.
TODO: Add JWT token authentication for production use.

Rate Limiting:
No rate limiting currently implemented.
TODO: Add rate limiting to prevent abuse.

Usage Examples:
    # Create unit of measure
    POST /api/v1/products/uom
    {
      "code": "KG",
      "name": "Kilogram",
      "category": "weight",
      "is_base_unit": true,
      "conversion_factor": 1.0
    }
    
    # List products (paginated)
    GET /api/v1/products/?skip=0&limit=20&active_only=true
    
    # Get specific product
    GET /api/v1/products/123e4567-e89b-12d3-a456-426614174000
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

# Create API router with common prefix and tags
# Tags are used for grouping in Swagger UI
product_gateway = APIRouter(prefix="/products", tags=["Products"])


# ============================================================================
# UNIT OF MEASURE ENDPOINTS
# ============================================================================

@product_gateway.post(
    "/uom",
    response_model=UnitOfMeasureResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create unit of measure",
    description="Create a new unit of measure for quantifying products"
)
def create_unit_of_measure(
    payload: UnitOfMeasureCreate,
    db: SQLSession = Depends(harvest_session)
):
    """
    Create a new unit of measure.
    
    Units of measure define how products are quantified (pieces, kg, liters, etc.).
    Each unit belongs to a category and has a conversion factor to the base unit.
    
    Args:
        payload: Unit of measure creation data
        db: Database session (injected)
        
    Returns:
        UnitOfMeasureResponse: Created unit with generated ID and timestamps
        
    Raises:
        422: Validation error (invalid data)
        500: Database error (duplicate code, etc.)
        
    Example Request:
        POST /api/v1/products/uom
        {
          "code": "KG",
          "name": "Kilogram",
          "category": "weight",
          "is_base_unit": true,
          "conversion_factor": 1.0
        }
    """
    # Convert Pydantic model to ORM entity using model_dump()
    new_uom = UnitOfMeasure(**payload.model_dump())
    
    # Add to session and commit
    db.add(new_uom)
    db.commit()
    
    # Refresh to load generated fields (ID, timestamps)
    db.refresh(new_uom)
    
    # FastAPI automatically converts ORM to Pydantic response model
    return new_uom


@product_gateway.get(
    "/uom",
    response_model=List[UnitOfMeasureResponse],
    summary="List units of measure",
    description="Retrieve paginated list of units of measure"
)
def list_units_of_measure(
    skip: int = 0,
    limit: int = 100,
    db: SQLSession = Depends(harvest_session)
):
    """
    List all units of measure with pagination.
    
    Args:
        skip: Number of records to skip (offset) - default 0
        limit: Maximum records to return - default 100, max 100
        db: Database session (injected)
        
    Returns:
        List[UnitOfMeasureResponse]: List of units
        
    Example:
        GET /api/v1/products/uom?skip=0&limit=20
    """
    # Build query with pagination
    stmt = select(UnitOfMeasure).offset(skip).limit(limit)
    
    # Execute and fetch all results
    results = db.execute(stmt).scalars().all()
    
    return results


# ============================================================================
# PRODUCT CATEGORY ENDPOINTS
# ============================================================================

@product_gateway.post(
    "/categories",
    response_model=ProductCategoryResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create product category",
    description="Create a new product category for organizing products"
)
def create_category(
    payload: ProductCategoryCreate,
    db: SQLSession = Depends(harvest_session)
):
    """
    Create a new product category.
    
    Categories organize products hierarchically. Set parent_category_id to
    create a subcategory, or leave it null for a root category.
    
    Args:
        payload: Category creation data
        db: Database session (injected)
        
    Returns:
        ProductCategoryResponse: Created category with generated ID
        
    Example Request:
        # Root category
        POST /api/v1/products/categories
        {
          "name": "Electronics",
          "code": "ELEC",
          "parent_category_id": null,
          "description": "All electronic products"
        }
        
        # Subcategory
        {
          "name": "Computers",
          "code": "COMP",
          "parent_category_id": "uuid-of-electronics-category"
        }
    """
    new_category = ProductCategory(**payload.model_dump())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@product_gateway.get(
    "/categories",
    response_model=List[ProductCategoryResponse],
    summary="List product categories",
    description="Retrieve paginated list of product categories"
)
def list_categories(
    skip: int = 0,
    limit: int = 100,
    db: SQLSession = Depends(harvest_session)
):
    """
    List all product categories with pagination.
    
    Returns flat list. To build hierarchy, check parent_category_id.
    
    Args:
        skip: Number of records to skip - default 0
        limit: Maximum records to return - default 100
        db: Database session (injected)
        
    Returns:
        List[ProductCategoryResponse]: List of categories
    """
    stmt = select(ProductCategory).offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


# ============================================================================
# PRODUCT ENDPOINTS
# ============================================================================

@product_gateway.post(
    "/",
    response_model=ProductResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create product",
    description="Create a new product master record"
)
def create_product(
    payload: ProductCreate,
    db: SQLSession = Depends(harvest_session)
):
    """
    Create a new product.
    
    Products represent master data for inventory items. Each product must
    have a unique SKU and a base unit of measure.
    
    Args:
        payload: Product creation data
        db: Database session (injected)
        
    Returns:
        ProductResponse: Created product with generated ID
        
    Example Request:
        POST /api/v1/products/
        {
          "sku": "LAPTOP-001",
          "name": "Business Laptop",
          "description": "High-performance laptop for business use",
          "category_id": "uuid-of-category",
          "base_uom_id": "uuid-of-piece-uom",
          "track_by_lot": false,
          "track_by_serial": true,
          "is_active": true
        }
    """
    new_product = Product(**payload.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@product_gateway.get(
    "/",
    response_model=List[ProductResponse],
    summary="List products",
    description="Retrieve paginated list of products with optional active filter"
)
def list_products(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: SQLSession = Depends(harvest_session)
):
    """
    List products with optional filtering.
    
    Args:
        skip: Number of records to skip - default 0
        limit: Maximum records to return - default 100
        active_only: Only return active products - default True
        db: Database session (injected)
        
    Returns:
        List[ProductResponse]: List of products
        
    Example:
        # Active products only
        GET /api/v1/products/?active_only=true
        
        # All products including inactive
        GET /api/v1/products/?active_only=false&limit=50
    """
    # Start with base query
    stmt = select(Product)
    
    # Apply active filter if requested
    if active_only:
        stmt = stmt.where(Product.is_active)
    
    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)
    
    results = db.execute(stmt).scalars().all()
    return results


@product_gateway.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    description="Retrieve a single product by its unique identifier"
)
def get_product(
    product_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """
    Get a single product by ID.
    
    Args:
        product_id: UUID of the product
        db: Database session (injected)
        
    Returns:
        ProductResponse: Product details
        
    Raises:
        404: Product not found
        
    Example:
        GET /api/v1/products/123e4567-e89b-12d3-a456-426614174000
    """
    stmt = select(Product).where(Product.product_id == product_id)
    product = db.execute(stmt).scalar_one_or_none()
    
    # Return 404 if not found
    if not product:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
    
    return product


# ============================================================================
# PRODUCT VARIANT ENDPOINTS
# ============================================================================

@product_gateway.post(
    "/variants",
    response_model=ProductVariantResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create product variant",
    description="Create a new variant for an existing product"
)
def create_variant(
    payload: ProductVariantCreate,
    db: SQLSession = Depends(harvest_session)
):
    """
    Create a new product variant.
    
    Variants represent different configurations of a product (size, color, etc.).
    Each variant must reference an existing product and have a unique SKU.
    
    Args:
        payload: Variant creation data
        db: Database session (injected)
        
    Returns:
        ProductVariantResponse: Created variant
        
    Example Request:
        POST /api/v1/products/variants
        {
          "product_id": "uuid-of-parent-product",
          "sku": "SHIRT-001-M-BLU",
          "name": "T-Shirt - Medium - Blue",
          "attributes": "Size: M, Color: Blue",
          "is_active": true
        }
    """
    new_variant = ProductVariant(**payload.model_dump())
    db.add(new_variant)
    db.commit()
    db.refresh(new_variant)
    return new_variant


@product_gateway.get(
    "/{product_id}/variants",
    response_model=List[ProductVariantResponse],
    summary="List product variants",
    description="Get all variants for a specific product"
)
def list_product_variants(
    product_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """
    List all variants for a specific product.
    
    Args:
        product_id: UUID of the parent product
        db: Database session (injected)
        
    Returns:
        List[ProductVariantResponse]: All variants for the product
        
    Example:
        GET /api/v1/products/123e4567-e89b-12d3-a456-426614174000/variants
    """
    stmt = select(ProductVariant).where(ProductVariant.product_id == product_id)
    results = db.execute(stmt).scalars().all()
    return results
