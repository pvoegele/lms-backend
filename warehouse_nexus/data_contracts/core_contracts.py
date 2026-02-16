"""
Core Data Contracts - Pydantic Models for Product Domain
========================================================

This module defines Pydantic models for request validation and response
serialization in the product management domain.

Pydantic Models Provide:
1. **Request Validation**: Automatic validation of incoming API requests
2. **Type Safety**: Runtime type checking with detailed error messages
3. **Serialization**: Automatic conversion between JSON and Python objects
4. **Documentation**: Auto-generated OpenAPI schemas for Swagger UI
5. **Data Transformation**: ORM ↔ Pydantic conversion

Naming Convention:
- *Create: Request models for creating new records (POST)
- *Update: Request models for updating records (PATCH/PUT)
- *Response: Response models returning to client (GET/POST)

Design Pattern:
Each entity typically has a Create/Response pair:
- Create model: Fields required for creation (no IDs or timestamps)
- Response model: Inherits Create, adds generated fields (ID, timestamps)

The response models use `model_config = ConfigDict(from_attributes=True)`
to enable automatic conversion from SQLAlchemy ORM objects.

Usage in FastAPI:
    @app.post("/products", response_model=ProductResponse)
    def create_product(payload: ProductCreate, db: Session = Depends(...)):
        # Pydantic validates payload automatically
        product = Product(**payload.model_dump())  # Convert to ORM
        db.add(product)
        db.commit()
        db.refresh(product)
        return product  # Automatically converts ORM → Pydantic

Validation Features:
- Field types (str, int, UUID, datetime)
- Length constraints (max_length, min_length)
- Pattern matching (regex)
- Custom validators
- Required vs optional fields
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


# ============================================================================
# UNIT OF MEASURE CONTRACTS
# ============================================================================

class UnitOfMeasureCreate(BaseModel):
    """
    Request model for creating a unit of measure.
    
    Units of measure define how products are quantified. Each unit belongs
    to a category (weight, volume, count, etc.) and has a conversion factor.
    
    Attributes:
        code: Short unique code (e.g., "KG", "PC", "L")
        name: Full name (e.g., "Kilogram", "Piece", "Liter")
        category: Category grouping (weight, volume, count, length)
        is_base_unit: True if this is the base unit for its category
        conversion_factor: Multiplier to convert to base unit
    
    Validation:
        - code: Max 20 characters, required
        - name: Max 100 characters, required
        - category: Max 50 characters, required
        - is_base_unit: Boolean, defaults to False
        - conversion_factor: Float, defaults to 1.0
    
    Example:
        {
          "code": "KG",
          "name": "Kilogram",
          "category": "weight",
          "is_base_unit": true,
          "conversion_factor": 1.0
        }
    """
    code: str = Field(..., max_length=20, description="Unique code for the unit")
    name: str = Field(..., max_length=100, description="Full name of the unit")
    category: str = Field(..., max_length=50, description="Category (weight, volume, count, etc.)")
    is_base_unit: bool = Field(default=False, description="Whether this is the base unit for its category")
    conversion_factor: float = Field(default=1.0, description="Conversion factor to base unit")


class UnitOfMeasureResponse(UnitOfMeasureCreate):
    """
    Response model for unit of measure.
    
    Extends UnitOfMeasureCreate with generated fields (ID and timestamps).
    
    Additional Attributes:
        unit_id: UUID primary key (generated)
        created_at: Creation timestamp (generated)
        updated_at: Last update timestamp (generated)
    """
    unit_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Configuration to enable ORM mode (SQLAlchemy → Pydantic conversion)
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PRODUCT CATEGORY CONTRACTS
# ============================================================================

class ProductCategoryCreate(BaseModel):
    """
    Request model for creating a product category.
    
    Categories organize products hierarchically. Set parent_category_id to
    create a subcategory, or leave null for a root category.
    
    Attributes:
        name: Category display name
        code: Unique code for API/integration
        parent_category_id: Parent category UUID (null for root)
        description: Optional detailed description
    
    Hierarchy Example:
        Electronics (parent_category_id=null)
        └── Computers (parent_category_id=Electronics.id)
            ├── Laptops (parent_category_id=Computers.id)
            └── Desktops (parent_category_id=Computers.id)
    """
    name: str = Field(..., max_length=150, description="Category display name")
    code: str = Field(..., max_length=50, description="Unique category code")
    parent_category_id: Optional[UUID] = Field(None, description="Parent category UUID (null for root)")
    description: Optional[str] = Field(None, description="Optional detailed description")


class ProductCategoryResponse(ProductCategoryCreate):
    """
    Response model for product category.
    
    Additional Attributes:
        category_id: UUID primary key
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    category_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PRODUCT CONTRACTS
# ============================================================================

class ProductCreate(BaseModel):
    """
    Request model for creating a product.
    
    Products represent master data for inventory items. Each product requires
    a unique SKU and a base unit of measure.
    
    Attributes:
        sku: Stock Keeping Unit - unique identifier
        name: Product display name
        description: Detailed description (optional)
        category_id: Product category UUID (optional)
        base_uom_id: Base unit of measure UUID (required)
        track_by_lot: Enable lot/batch tracking
        track_by_serial: Enable serial number tracking
        is_active: Active status (soft delete flag)
    
    Tracking Modes:
        - Simple: track_by_lot=False, track_by_serial=False
        - Lot: track_by_lot=True, track_by_serial=False
        - Serial: track_by_serial=True
    
    Example:
        {
          "sku": "LAPTOP-001",
          "name": "Business Laptop",
          "description": "High-performance laptop",
          "category_id": "uuid-of-category",
          "base_uom_id": "uuid-of-piece-uom",
          "track_by_lot": false,
          "track_by_serial": true,
          "is_active": true
        }
    """
    sku: str = Field(..., max_length=100, description="Unique SKU")
    name: str = Field(..., max_length=250, description="Product name")
    description: Optional[str] = Field(None, description="Detailed description")
    category_id: Optional[UUID] = Field(None, description="Product category UUID")
    base_uom_id: UUID = Field(..., description="Base unit of measure UUID")
    track_by_lot: bool = Field(default=False, description="Enable lot tracking")
    track_by_serial: bool = Field(default=False, description="Enable serial tracking")
    is_active: bool = Field(default=True, description="Active status")


class ProductResponse(ProductCreate):
    """
    Response model for product.
    
    Additional Attributes:
        product_id: UUID primary key
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    product_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PRODUCT VARIANT CONTRACTS
# ============================================================================

class ProductVariantCreate(BaseModel):
    """
    Request model for creating a product variant.
    
    Variants represent different configurations of a product (size, color, etc.).
    Each variant must reference an existing product and have a unique SKU.
    
    Attributes:
        product_id: Parent product UUID
        sku: Unique SKU for this variant
        name: Variant display name
        attributes: Flexible text field for variant attributes
        is_active: Active status
    
    Attributes Field Format:
        Can be any text format:
        - Simple: "Color: Blue, Size: Large"
        - JSON: {"color": "blue", "size": "large"}
        - Markdown: For rendering in UI
    
    Example:
        {
          "product_id": "uuid-of-parent-product",
          "sku": "SHIRT-001-M-BLU",
          "name": "T-Shirt - Medium - Blue",
          "attributes": "Size: M, Color: Blue",
          "is_active": true
        }
    """
    product_id: UUID = Field(..., description="Parent product UUID")
    sku: str = Field(..., max_length=100, description="Unique variant SKU")
    name: str = Field(..., max_length=250, description="Variant display name")
    attributes: Optional[str] = Field(None, description="Variant-specific attributes")
    is_active: bool = Field(default=True, description="Active status")


class ProductVariantResponse(ProductVariantCreate):
    """
    Response model for product variant.
    
    Additional Attributes:
        variant_id: UUID primary key
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    variant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
