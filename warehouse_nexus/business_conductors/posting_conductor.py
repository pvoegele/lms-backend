"""
Document Posting Conductor - Business logic for stock document finalization
Orchestrates DRAFT -> POSTED transition with inventory impacts
"""
from sqlalchemy.orm import Session as SQLSession
from sqlalchemy import select
from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal

from warehouse_nexus.schema_registry.stock_entities import (
    StockDocument,
    StockDocumentLine,
    StockMovement
)
from warehouse_nexus.schema_registry.inventory_entities import InventoryBalance
from warehouse_nexus.schema_registry.categorical_taxonomy import (
    DocumentStateCode,
    StockDocumentCategory
)
from warehouse_nexus.schema_registry.audit_entities import AuditLog


class PostingConductor:
    """Conducts stock document posting operations"""
    
    def __init__(self, db_session: SQLSession):
        self.db = db_session
    
    def conduct_posting(self, document_id: str) -> Dict[str, Any]:
        """
        Conduct document posting operation
        - Validate document state
        - Generate movements
        - Update inventory balances
        - Record audit trail
        """
        
        # Retrieve document with validation
        stmt = select(StockDocument).where(StockDocument.doc_id == document_id)
        document = self.db.execute(stmt).scalar_one_or_none()
        
        if not document:
            raise ValueError(f"Document {document_id} not located")
        
        if document.doc_status != DocumentStateCode.DRAFT:
            raise ValueError(
                f"Document posting blocked. Current state: {document.doc_status}"
            )
        
        # Retrieve document lines
        lines_stmt = select(StockDocumentLine).where(
            StockDocumentLine.doc_id == document_id
        )
        document_lines = self.db.execute(lines_stmt).scalars().all()
        
        if not document_lines:
            raise ValueError("Cannot post document without line items")
        
        # Generate movements for each line
        movements_created = []
        for line in document_lines:
            movement = self._generate_movement(document, line)
            self.db.add(movement)
            movements_created.append(movement)
            
            # Apply inventory balance adjustments
            self._apply_balance_adjustment(document, line)
        
        # Update document state
        document.doc_status = DocumentStateCode.POSTED
        document.posted_at = datetime.utcnow()
        
        # Create audit record
        self._create_audit_record(document, movements_created)
        
        self.db.commit()
        
        return {
            "success": True,
            "document_id": str(document.doc_id),
            "movements_generated": len(movements_created),
            "posted_timestamp": document.posted_at.isoformat()
        }
    
    def _generate_movement(
        self,
        doc: StockDocument,
        line: StockDocumentLine
    ) -> StockMovement:
        """Generate movement record from document line"""
        
        movement = StockMovement(
            doc_id=doc.doc_id,
            line_id=line.line_id,
            product_id=line.product_id,
            variant_id=line.variant_id,
            lot_id=line.lot_id,
            source_warehouse_id=doc.source_warehouse_id,
            source_location_id=line.source_location_id,
            dest_warehouse_id=doc.dest_warehouse_id,
            dest_location_id=line.dest_location_id,
            quantity=line.quantity,
            movement_timestamp=datetime.utcnow()
        )
        
        return movement
    
    def _apply_balance_adjustment(
        self,
        doc: StockDocument,
        line: StockDocumentLine
    ):
        """Apply inventory balance adjustments based on document type"""
        
        doc_category = doc.doc_type
        qty = Decimal(str(line.quantity))
        
        # Route to appropriate adjustment logic
        if doc_category == StockDocumentCategory.RECEIVING:
            # Increase at destination
            self._adjust_location_balance(
                line.product_id,
                line.variant_id,
                doc.dest_warehouse_id,
                line.dest_location_id,
                line.lot_id,
                qty,
                increase=True
            )
        
        elif doc_category == StockDocumentCategory.SHIPPING:
            # Decrease at source
            self._adjust_location_balance(
                line.product_id,
                line.variant_id,
                doc.source_warehouse_id,
                line.source_location_id,
                line.lot_id,
                qty,
                increase=False
            )
        
        elif doc_category == StockDocumentCategory.TRANSFER:
            # Decrease source, increase destination
            self._adjust_location_balance(
                line.product_id,
                line.variant_id,
                doc.source_warehouse_id,
                line.source_location_id,
                line.lot_id,
                qty,
                increase=False
            )
            self._adjust_location_balance(
                line.product_id,
                line.variant_id,
                doc.dest_warehouse_id,
                line.dest_location_id,
                line.lot_id,
                qty,
                increase=True
            )
        
        elif doc_category == StockDocumentCategory.ADJUSTMENT:
            # Apply adjustment with sign
            target_warehouse = doc.dest_warehouse_id or doc.source_warehouse_id
            target_location = line.dest_location_id or line.source_location_id
            
            if qty >= 0:
                self._adjust_location_balance(
                    line.product_id,
                    line.variant_id,
                    target_warehouse,
                    target_location,
                    line.lot_id,
                    abs(qty),
                    increase=True
                )
            else:
                self._adjust_location_balance(
                    line.product_id,
                    line.variant_id,
                    target_warehouse,
                    target_location,
                    line.lot_id,
                    abs(qty),
                    increase=False
                )
    
    def _adjust_location_balance(
        self,
        product_id,
        variant_id,
        warehouse_id,
        location_id,
        lot_id,
        quantity: Decimal,
        increase: bool
    ):
        """Adjust or create balance record at location"""
        
        # Find existing balance
        stmt = select(InventoryBalance).where(
            InventoryBalance.product_id == product_id,
            InventoryBalance.variant_id == variant_id,
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.location_id == location_id,
            InventoryBalance.lot_id == lot_id
        )
        balance = self.db.execute(stmt).scalar_one_or_none()
        
        if balance:
            # Modify existing
            if increase:
                balance.quantity_on_hand += quantity
            else:
                balance.quantity_on_hand -= quantity
            
            # Recalculate available
            balance.quantity_available = (
                balance.quantity_on_hand - balance.quantity_reserved
            )
        else:
            # Create new balance
            new_balance = InventoryBalance(
                product_id=product_id,
                variant_id=variant_id,
                warehouse_id=warehouse_id,
                location_id=location_id,
                lot_id=lot_id,
                quantity_on_hand=quantity if increase else -quantity,
                quantity_reserved=Decimal('0'),
                quantity_available=quantity if increase else -quantity
            )
            self.db.add(new_balance)
    
    def _create_audit_record(self, doc: StockDocument, movements: List[StockMovement]):
        """Create audit log entry for posting"""
        
        audit = AuditLog(
            category="STOCK_DOCUMENT_POSTING",
            action=f"Posted document {doc.doc_number}",
            entity_type="StockDocument",
            entity_id=doc.doc_id,
            user_id="system",
            old_values={"status": "DRAFT"},
            new_values={
                "status": "POSTED",
                "movements_count": len(movements)
            }
        )
        self.db.add(audit)
