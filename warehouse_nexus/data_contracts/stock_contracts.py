"""
Stock Document Contracts - Pydantic models for stock movements
Request/Response validation for document operations
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from warehouse_nexus.schema_registry.categorical_taxonomy import StockDocumentCategory, DocumentStateCode


class StockDocumentLineCreate(BaseModel):
    line_number: str = Field(..., max_length=10)
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None
    lot_id: Optional[UUID] = None
    source_location_id: Optional[UUID] = None
    dest_location_id: Optional[UUID] = None
    quantity: float
    uom_id: Optional[UUID] = None


class StockDocumentLineResponse(StockDocumentLineCreate):
    line_id: UUID
    doc_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StockDocumentCreate(BaseModel):
    doc_number: str = Field(..., max_length=100)
    doc_type: StockDocumentCategory
    source_warehouse_id: Optional[UUID] = None
    dest_warehouse_id: Optional[UUID] = None
    doc_date: date
    reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class StockDocumentCreateWithLines(StockDocumentCreate):
    lines: List[StockDocumentLineCreate] = []


class StockDocumentResponse(StockDocumentCreate):
    doc_id: UUID
    doc_status: DocumentStateCode
    posted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StockDocumentWithLines(StockDocumentResponse):
    lines: List[StockDocumentLineResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class PostDocumentCommand(BaseModel):
    """Command to post a stock document"""
    doc_id: UUID
