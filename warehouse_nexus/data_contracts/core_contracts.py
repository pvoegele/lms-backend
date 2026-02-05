"""
Core Data Contracts - Pydantic models for product domain
Request/Response validation schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class UnitOfMeasureCreate(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    is_base_unit: bool = False
    conversion_factor: float = 1.0


class UnitOfMeasureResponse(UnitOfMeasureCreate):
    unit_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProductCategoryCreate(BaseModel):
    name: str = Field(..., max_length=150)
    code: str = Field(..., max_length=50)
    parent_category_id: Optional[UUID] = None
    description: Optional[str] = None


class ProductCategoryResponse(ProductCategoryCreate):
    category_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    sku: str = Field(..., max_length=100)
    name: str = Field(..., max_length=250)
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    base_uom_id: UUID
    track_by_lot: bool = False
    track_by_serial: bool = False
    is_active: bool = True


class ProductResponse(ProductCreate):
    product_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProductVariantCreate(BaseModel):
    product_id: UUID
    sku: str = Field(..., max_length=100)
    name: str = Field(..., max_length=250)
    attributes: Optional[str] = None
    is_active: bool = True


class ProductVariantResponse(ProductVariantCreate):
    variant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
