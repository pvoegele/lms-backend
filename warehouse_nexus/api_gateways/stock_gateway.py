"""
Stock Movement API Gateway - HTTP endpoints for stock document operations
RESTful routes for creating and posting stock documents
"""
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session as SQLSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from warehouse_nexus.cerebrum.psql_conductor import harvest_session
from warehouse_nexus.schema_registry.stock_entities import StockDocument, StockDocumentLine
from warehouse_nexus.data_contracts.stock_contracts import (
    StockDocumentCreateWithLines,
    StockDocumentResponse,
    StockDocumentWithLines,
    StockDocumentLineResponse,
    PostDocumentCommand
)
from warehouse_nexus.business_conductors.posting_conductor import PostingConductor
from warehouse_nexus.schema_registry.categorical_taxonomy import DocumentStateCode


stock_gateway = APIRouter(prefix="/stock-documents", tags=["Stock Movement"])


@stock_gateway.post(
    "/",
    response_model=StockDocumentWithLines,
    status_code=http_status.HTTP_201_CREATED
)
def create_stock_document(
    payload: StockDocumentCreateWithLines,
    db: SQLSession = Depends(harvest_session)
):
    """Create new stock document with lines"""
    
    # Create document header
    doc_data = payload.model_dump(exclude={'lines'})
    new_doc = StockDocument(
        **doc_data,
        doc_status=DocumentStateCode.DRAFT
    )
    db.add(new_doc)
    db.flush()
    
    # Create lines
    created_lines = []
    for line_payload in payload.lines:
        line = StockDocumentLine(
            doc_id=new_doc.doc_id,
            **line_payload.model_dump()
        )
        db.add(line)
        created_lines.append(line)
    
    db.commit()
    db.refresh(new_doc)
    
    # Build response with lines
    response = StockDocumentWithLines.model_validate(new_doc)
    response.lines = [
        StockDocumentLineResponse.model_validate(line) for line in created_lines
    ]
    
    return response


@stock_gateway.get(
    "/",
    response_model=List[StockDocumentResponse]
)
def list_stock_documents(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[DocumentStateCode] = None,
    db: SQLSession = Depends(harvest_session)
):
    """List stock documents"""
    stmt = select(StockDocument)
    
    if status_filter:
        stmt = stmt.where(StockDocument.doc_status == status_filter)
    
    stmt = stmt.offset(skip).limit(limit)
    results = db.execute(stmt).scalars().all()
    return results


@stock_gateway.get(
    "/{doc_id}",
    response_model=StockDocumentWithLines
)
def get_stock_document(
    doc_id: UUID,
    db: SQLSession = Depends(harvest_session)
):
    """Get stock document with lines"""
    doc_stmt = select(StockDocument).where(StockDocument.doc_id == doc_id)
    document = db.execute(doc_stmt).scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found"
        )
    
    # Fetch lines
    lines_stmt = select(StockDocumentLine).where(
        StockDocumentLine.doc_id == doc_id
    )
    lines = db.execute(lines_stmt).scalars().all()
    
    response = StockDocumentWithLines.model_validate(document)
    response.lines = [
        StockDocumentLineResponse.model_validate(line) for line in lines
    ]
    
    return response


@stock_gateway.post(
    "/post",
    status_code=http_status.HTTP_200_OK
)
def post_stock_document(
    command: PostDocumentCommand,
    db: SQLSession = Depends(harvest_session)
):
    """
    Post/finalize stock document
    Transitions from DRAFT to POSTED
    Creates movements and updates inventory
    """
    try:
        conductor = PostingConductor(db)
        result = conductor.conduct_posting(str(command.doc_id))
        db.commit()
        return result
    except ValueError as validation_err:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(validation_err)
        )
    except Exception as unexpected_err:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Posting failed: {str(unexpected_err)}"
        )
