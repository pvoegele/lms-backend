"""
Document Posting Conductor - Stock Document Finalization Business Logic
=======================================================================

This module implements the core business logic for stock document posting - the process
of finalizing inventory transactions and updating inventory balances.

Document Posting Workflow:
1. **Validation**: Verify document is in DRAFT state and has line items
2. **Movement Generation**: Create immutable StockMovement records for each line
3. **Balance Updates**: Adjust InventoryBalance records based on document type
4. **Status Update**: Mark document as POSTED with timestamp
5. **Audit Trail**: Log the posting operation for compliance

Document Types and Their Effects:
- **RECEIVING**: Inventory arrives at warehouse (increases destination balance)
- **SHIPPING**: Inventory leaves warehouse (decreases source balance)
- **TRANSFER**: Move between locations (decreases source, increases destination)
- **ADJUSTMENT**: Correct balances (signed adjustment: positive = increase, negative = decrease)
- **MANUFACTURING_CONSUMPTION**: Raw materials used in production (decreases balance)
- **MANUFACTURING_OUTPUT**: Finished goods from production (increases balance)

Key Design Decisions:
1. **Document-Driven**: All inventory changes flow through documents
2. **Immutable Movements**: Once posted, movements cannot be changed (audit compliance)
3. **Balance Denormalization**: InventoryBalance table stores computed quantities for performance
4. **Caller Commits**: The posting logic doesn't commit - caller controls transaction

Transaction Management:
The posting logic modifies multiple database records but does NOT commit the transaction.
This allows the caller to:
- Validate the results before committing
- Roll back on validation failure
- Combine posting with other operations in a single transaction

Usage Example:
    from warehouse_nexus.business_conductors.posting_conductor import PostingConductor
    from warehouse_nexus.cerebrum.psql_conductor import TransactionConductor
    
    with TransactionConductor.orchestrate_transaction() as db:
        conductor = PostingConductor(db)
        result = conductor.conduct_posting(document_id)
        # Transaction auto-commits if no exception raised
        print(f"Posted {result['movements_generated']} movements")
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
    """
    Orchestrates the stock document posting workflow.
    
    This class implements the business logic for finalizing stock documents,
    which involves:
    - Validating document state
    - Creating movement records
    - Updating inventory balances
    - Recording audit trail
    
    The class follows the Conductor pattern (also called Orchestrator or Service),
    which centralizes complex business workflows that span multiple entities.
    
    Attributes:
        db (SQLSession): Database session for all operations
    """
    
    def __init__(self, db_session: SQLSession):
        """
        Initialize the posting conductor with a database session.
        
        Args:
            db_session: SQLAlchemy session for database operations.
                       All operations use this session, allowing them to be
                       part of a larger transaction.
        """
        self.db = db_session
    
    def conduct_posting(self, document_id: str) -> Dict[str, Any]:
        """
        Conduct the complete document posting operation.
        
        This is the main entry point for posting a stock document. It orchestrates
        all the steps required to finalize a document and update inventory.
        
        Workflow:
        1. Retrieve document from database and validate it exists
        2. Verify document is in DRAFT state (only draft docs can be posted)
        3. Retrieve all line items for the document
        4. For each line:
           a. Generate a StockMovement record (immutable transaction log)
           b. Update InventoryBalance based on document type
        5. Update document status to POSTED and record timestamp
        6. Create audit log entry
        
        Args:
            document_id (str): UUID of the document to post
            
        Returns:
            Dict[str, Any]: Result dictionary containing:
                - success (bool): True if posting succeeded
                - document_id (str): The posted document's ID
                - movements_generated (int): Number of movement records created
                - posted_timestamp (str): ISO timestamp when posted
                
        Raises:
            ValueError: If document doesn't exist, wrong status, or has no lines
            
        Example:
            >>> conductor = PostingConductor(db_session)
            >>> result = conductor.conduct_posting("123e4567-e89b-12d3-a456-426614174000")
            >>> print(f"Created {result['movements_generated']} movements")
            Created 3 movements
            
        Note:
            This method does NOT commit the transaction. The caller must commit
            or the changes will be rolled back. This design allows for:
            - Additional validations before commit
            - Combining with other operations in same transaction
            - Explicit transaction control
        """
        
        # PHASE 1: VALIDATION
        # Retrieve document with explicit query for better error handling
        stmt = select(StockDocument).where(StockDocument.doc_id == document_id)
        document = self.db.execute(stmt).scalar_one_or_none()
        
        # Verify document exists
        if not document:
            raise ValueError(f"Document {document_id} not located")
        
        # Verify document is in correct state for posting
        # Only DRAFT documents can be posted - prevents double-posting
        if document.doc_status != DocumentStateCode.DRAFT:
            raise ValueError(
                f"Document posting blocked. Current state: {document.doc_status}"
            )
        
        # Retrieve all line items for this document
        lines_stmt = select(StockDocumentLine).where(
            StockDocumentLine.doc_id == document_id
        )
        document_lines = self.db.execute(lines_stmt).scalars().all()
        
        # Verify document has at least one line
        # Empty documents are invalid and cannot be posted
        if not document_lines:
            raise ValueError("Cannot post document without line items")
        
        # PHASE 2: MOVEMENT GENERATION
        # Create immutable movement records for audit trail
        movements_created = []
        for line in document_lines:
            # Generate movement record from document and line data
            movement = self._generate_movement(document, line)
            self.db.add(movement)  # Add to session (not committed yet)
            movements_created.append(movement)
            
            # PHASE 3: BALANCE UPDATE
            # Update inventory balances based on document type
            self._apply_balance_adjustment(document, line)
        
        # PHASE 4: STATUS UPDATE
        # Mark document as permanently posted
        document.doc_status = DocumentStateCode.POSTED
        document.posted_at = datetime.utcnow()  # Record when posted
        
        # PHASE 5: AUDIT TRAIL
        # Create audit log for compliance and troubleshooting
        self._create_audit_record(document, movements_created)
        
        # Note: Caller is responsible for committing the transaction
        # This allows for rollback if validation fails after posting
        
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
        """
        Generate an immutable movement record from a document line.
        
        StockMovement records serve as the permanent transaction log for all
        inventory movements. Once created, they are never modified or deleted,
        providing:
        - Complete audit trail of all inventory transactions
        - Source data for reporting and analytics
        - Traceability for regulatory compliance
        - Historical record even if documents are modified
        
        The movement copies relevant data from both the document header
        (warehouses) and line (product, quantity, locations) to create a
        denormalized record optimized for querying.
        
        Args:
            doc: The stock document header
            line: The document line being processed
            
        Returns:
            StockMovement: New movement record (not yet committed to database)
            
        Note:
            Movement records are denormalized - they copy data rather than
            just storing IDs. This improves query performance and ensures
            historical accuracy even if referenced entities are modified.
        """
        
        movement = StockMovement(
            doc_id=doc.doc_id,  # Link back to source document
            line_id=line.line_id,  # Link to specific line item
            product_id=line.product_id,  # What was moved
            variant_id=line.variant_id,  # Specific variant (if applicable)
            lot_id=line.lot_id,  # Batch/lot tracking (if applicable)
            source_warehouse_id=doc.source_warehouse_id,  # Where it came from
            source_location_id=line.source_location_id,  # Specific source location
            dest_warehouse_id=doc.dest_warehouse_id,  # Where it went to
            dest_location_id=line.dest_location_id,  # Specific destination location
            quantity=line.quantity,  # How much was moved
            movement_timestamp=datetime.utcnow()  # When it was moved (transaction time)
        )
        
        return movement
    
    def _apply_balance_adjustment(
        self,
        doc: StockDocument,
        line: StockDocumentLine
    ):
        """
        Apply inventory balance adjustments based on document type.
        
        This method routes to the appropriate balance update logic based on
        the document type. Each document type has different inventory effects:
        
        - RECEIVING: Product arrives → increase at destination
        - SHIPPING: Product leaves → decrease at source
        - TRANSFER: Product moves → decrease source, increase destination
        - ADJUSTMENT: Correction → apply signed adjustment
        - MANUFACTURING_*: Production flows → various effects
        
        The method uses Decimal type for quantities to avoid floating-point
        precision issues in financial/inventory calculations.
        
        Args:
            doc: The stock document header (contains type and warehouses)
            line: The document line (contains quantities and locations)
            
        Note:
            This method modifies InventoryBalance records but does not commit.
            Multiple adjustments can be batched in a single transaction.
            
        Design Decision:
            We use a routing pattern (if/elif) rather than polymorphism because:
            1. All logic is in one place (easier to understand)
            2. Document types are known and stable
            3. Avoids complex class hierarchies
        """
        
        doc_category = doc.doc_type
        qty = Decimal(str(line.quantity))  # Convert to Decimal for precision
        
        # Route to appropriate adjustment logic based on document type
        # Each branch handles the specific inventory impact of that document type
        
        if doc_category == StockDocumentCategory.RECEIVING:
            # Receiving: Products arrive at warehouse from supplier/vendor
            # Effect: Increase inventory at destination location
            # Example: Purchase order receipt, return from customer
            self._adjust_location_balance(
                line.product_id,
                line.variant_id,
                doc.dest_warehouse_id,  # Where products arrived
                line.dest_location_id,  # Specific storage location
                line.lot_id,  # Lot/batch tracking
                qty,
                increase=True  # Add to inventory
            )
        
        elif doc_category == StockDocumentCategory.SHIPPING:
            # Shipping: Products leave warehouse to customer/external party
            # Effect: Decrease inventory at source location
            # Example: Sales order shipment, transfer to vendor
            self._adjust_location_balance(
                line.product_id,
                line.variant_id,
                doc.source_warehouse_id,  # Where products left from
                line.source_location_id,  # Specific pickup location
                line.lot_id,
                qty,
                increase=False  # Subtract from inventory
            )
        
        elif doc_category == StockDocumentCategory.TRANSFER:
            # Transfer: Products move between locations within organization
            # Effect: Decrease at source AND increase at destination
            # Example: Inter-warehouse transfer, location relocation
            # This is atomic - both must succeed or both fail
            
            # Decrease at source location
            self._adjust_location_balance(
                line.product_id,
                line.variant_id,
                doc.source_warehouse_id,
                line.source_location_id,
                line.lot_id,
                qty,
                increase=False  # Remove from source
            )
            # Increase at destination location
            self._adjust_location_balance(
                line.product_id,
                line.variant_id,
                doc.dest_warehouse_id,
                line.dest_location_id,
                line.lot_id,
                qty,
                increase=True  # Add to destination
            )
        
        elif doc_category == StockDocumentCategory.ADJUSTMENT:
            # Adjustment: Correct inventory quantities (cycle count, damage, theft)
            # Effect: Apply signed adjustment (positive or negative)
            # Example: Physical count shows different quantity than system
            
            # Determine target location (adjustments use either source or dest)
            target_warehouse = doc.dest_warehouse_id or doc.source_warehouse_id
            target_location = line.dest_location_id or line.source_location_id
            
            # Apply adjustment with correct sign
            if qty >= 0:
                # Positive adjustment - inventory was undercounted
                self._adjust_location_balance(
                    line.product_id,
                    line.variant_id,
                    target_warehouse,
                    target_location,
                    line.lot_id,
                    abs(qty),
                    increase=True  # Add missing inventory
                )
            else:
                # Negative adjustment - inventory was overcounted
                self._adjust_location_balance(
                    line.product_id,
                    line.variant_id,
                    target_warehouse,
                    target_location,
                    line.lot_id,
                    abs(qty),
                    increase=False  # Remove excess inventory
                )
        
        # TODO: Implement manufacturing document types
        # MANUFACTURING_CONSUMPTION: Raw materials used in production
        # MANUFACTURING_OUTPUT: Finished goods from production
    
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
        """
        Adjust or create an inventory balance record for a specific location.
        
        This method implements the actual inventory balance updates. It handles
        two scenarios:
        1. Balance record exists → update quantities
        2. Balance record doesn't exist → create new record
        
        The balance record tracks three quantities:
        - quantity_on_hand: Physical inventory count
        - quantity_reserved: Allocated to orders but not shipped
        - quantity_available: on_hand - reserved (can be sold/allocated)
        
        Args:
            product_id: Product being adjusted
            variant_id: Variant being adjusted (optional)
            warehouse_id: Warehouse where inventory is located
            location_id: Specific storage location
            lot_id: Lot/batch identifier (optional)
            quantity: Amount to adjust (positive decimal)
            increase: True to add, False to subtract
            
        Note:
            This method allows negative inventory balances (no check constraint).
            Negative balances indicate over-shipment or errors and should be
            monitored and corrected through adjustment documents.
            
        Design Decision:
            We use a composite key (product + variant + warehouse + location + lot)
            to uniquely identify balance records. This allows:
            - Granular tracking per location and lot
            - Efficient queries for available inventory
            - Support for lot-tracked and non-lot-tracked products
        """
        
        # Find existing balance record using composite key
        # All five dimensions must match to identify the specific balance
        stmt = select(InventoryBalance).where(
            InventoryBalance.product_id == product_id,
            InventoryBalance.variant_id == variant_id,
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.location_id == location_id,
            InventoryBalance.lot_id == lot_id
        )
        balance = self.db.execute(stmt).scalar_one_or_none()
        
        if balance:
            # Balance record exists - update quantities
            if increase:
                balance.quantity_on_hand += quantity  # Add to inventory
            else:
                balance.quantity_on_hand -= quantity  # Subtract from inventory
            
            # Recalculate available quantity
            # Available = On Hand - Reserved
            # This represents the quantity that can be allocated to new orders
            balance.quantity_available = (
                balance.quantity_on_hand - balance.quantity_reserved
            )
            
            # Note: updated_at timestamp is automatically updated by SQLAlchemy
            # due to onupdate=datetime.utcnow in the column definition
            
        else:
            # Balance record doesn't exist - create new one
            # This happens when inventory first arrives at a location
            new_balance = InventoryBalance(
                product_id=product_id,
                variant_id=variant_id,
                warehouse_id=warehouse_id,
                location_id=location_id,
                lot_id=lot_id,
                quantity_on_hand=quantity if increase else -quantity,  # Initial quantity
                quantity_reserved=Decimal('0'),  # No reservations initially
                quantity_available=quantity if increase else -quantity  # Same as on_hand
            )
            self.db.add(new_balance)  # Add to session (not committed yet)
    
    def _create_audit_record(self, doc: StockDocument, movements: List[StockMovement]):
        """
        Create an audit log entry for the posting operation.
        
        Audit logs provide a complete history of all significant system operations
        for compliance, debugging, and analysis purposes. Each audit record captures:
        - What happened (category and action)
        - What was affected (entity type and ID)
        - Who did it (user ID)
        - When it happened (timestamp, automatic)
        - What changed (old and new values)
        
        Args:
            doc: The stock document that was posted
            movements: List of movement records created during posting
            
        Note:
            In production, user_id should be set to the actual authenticated user.
            Currently set to "system" as authentication is not yet implemented.
            
        Future Enhancements:
            - Add IP address tracking
            - Include request ID for tracing
            - Store additional context (browser, API client, etc.)
            - Implement retention policies for audit data
        """
        
        audit = AuditLog(
            category="STOCK_DOCUMENT_POSTING",  # Operation category for filtering
            action=f"Posted document {doc.doc_number}",  # Human-readable description
            entity_type="StockDocument",  # Type of entity affected
            entity_id=doc.doc_id,  # Specific entity identifier
            user_id="system",  # TODO: Replace with actual authenticated user
            old_values={"status": "DRAFT"},  # State before operation
            new_values={
                "status": "POSTED",
                "movements_count": len(movements)  # Additional context
            }
            # timestamp is automatically set by SQLAlchemy (default=datetime.utcnow)
        )
        self.db.add(audit)  # Add to session (committed with transaction)
