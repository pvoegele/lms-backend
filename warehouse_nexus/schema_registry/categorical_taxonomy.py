"""
Categorical Taxonomy - System-Wide Enumerations and State Codes
===============================================================

This module defines all enumerated types (enums) used throughout the system.
Enums provide type-safe, validated sets of allowed values for various categorical
fields in the database and API.

Why Use Enums?
1. **Type Safety**: Catch invalid values at compile/validation time
2. **Documentation**: Valid values are self-documenting
3. **Database Integrity**: PostgreSQL ENUM types enforce constraints
4. **API Validation**: Pydantic automatically validates enum fields
5. **IDE Support**: Auto-completion for valid values

Design Pattern:
All enums inherit from both str and enum.Enum to ensure:
- JSON serialization works automatically (string values)
- Database storage as strings (portable, human-readable)
- Type checking and validation

Usage Example:
    from warehouse_nexus.schema_registry.categorical_taxonomy import DocumentStateCode
    
    # In ORM model
    status = Column(Enum(DocumentStateCode), nullable=False)
    
    # In Pydantic model
    status: DocumentStateCode
    
    # In code
    if document.status == DocumentStateCode.DRAFT:
        # Can be posted
        
Note on Naming:
Enum names use descriptive suffixes:
- *Category: Types or classifications (StockDocumentCategory)
- *StateCode: Lifecycle states (DocumentStateCode)
- *Code: General codes (PartnerTypeCode)
"""
import enum


class StockDocumentCategory(str, enum.Enum):
    """
    Categories of stock documents defining their inventory impact.
    
    Each document type has specific business rules and inventory effects:
    
    - RECEIVING: Inventory arrives at facility (increases stock)
      Examples: Purchase order receipts, returns from customers
      
    - SHIPPING: Inventory leaves facility (decreases stock)
      Examples: Sales order shipments, transfers to vendors
      
    - TRANSFER: Move between internal locations (balanced movement)
      Examples: Warehouse-to-warehouse transfers, location changes
      
    - ADJUSTMENT: Correct inventory quantities (can increase or decrease)
      Examples: Physical count adjustments, damage, shrinkage
      
    - MANUFACTURING_CONSUMPTION: Raw materials used in production (decreases stock)
      Examples: Materials issued to production orders
      
    - MANUFACTURING_OUTPUT: Finished goods from production (increases stock)
      Examples: Completed production orders
    
    Workflow:
    1. Document created in DRAFT status
    2. Lines added/edited while in DRAFT
    3. Document posted (status → POSTED)
    4. Inventory balances updated based on category
    """
    RECEIVING = "receiving"
    SHIPPING = "shipping"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    MANUFACTURING_CONSUMPTION = "manufacturing_consumption"
    MANUFACTURING_OUTPUT = "manufacturing_output"


class DocumentStateCode(str, enum.Enum):
    """
    Stock document lifecycle state codes.
    
    State Transitions:
    DRAFT → POSTED (normal flow)
    DRAFT → CANCELLED (aborted)
    
    DRAFT: Initial state, editable
        - Lines can be added/removed/modified
        - Document can be deleted
        - No inventory impact
        
    POSTED: Finalized state, immutable
        - Lines locked (no modifications)
        - Inventory balances updated
        - Stock movements created
        - Audit trail recorded
        - Cannot be deleted (only cancelled)
        
    CANCELLED: Voided state
        - Document marked as invalid
        - No inventory impact (or reversed if was posted)
        - Used for error correction
    
    Note: Once POSTED, documents cannot transition back to DRAFT.
    This ensures audit integrity and prevents tampering.
    """
    DRAFT = "draft"
    POSTED = "posted"
    CANCELLED = "cancelled"


class SalesOrderStateCode(str, enum.Enum):
    """
    Sales order lifecycle state codes.
    
    State Progression:
    DRAFT → CONFIRMED → PARTIALLY_FULFILLED → FULFILLED
      ↓         ↓
    CANCELLED  CANCELLED
    
    DRAFT: Initial entry, not yet confirmed
        - Customer quote or preliminary order
        - Can be freely modified
        - No inventory reservations
        
    CONFIRMED: Order accepted and locked
        - Customer has committed
        - Inventory may be reserved
        - Ready for fulfillment processing
        
    PARTIALLY_FULFILLED: Some items shipped, some pending
        - One or more shipments completed
        - Remaining items still to ship
        - Useful for partial deliveries and backorders
        
    FULFILLED: All items shipped
        - Order complete
        - No further action needed
        - Ready for archival
        
    CANCELLED: Order voided
        - Customer cancellation
        - Unable to fulfill
        - Inventory reservations released
    """
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class PurchaseOrderStateCode(str, enum.Enum):
    """
    Purchase order lifecycle state codes.
    
    State Progression:
    DRAFT → APPROVED → PARTIALLY_RECEIVED → RECEIVED
      ↓         ↓
    CANCELLED  CANCELLED
    
    DRAFT: Initial entry, not yet submitted
        - Internal requisition or quote
        - Can be modified freely
        - Not sent to supplier
        
    APPROVED: Order approved and sent to supplier
        - Purchase authorized
        - Communicated to vendor
        - Awaiting delivery
        
    PARTIALLY_RECEIVED: Some items received, some pending
        - One or more receipts processed
        - Outstanding quantity still expected
        - Common for split shipments
        
    RECEIVED: All items received
        - Order complete
        - All quantities accounted for
        - Ready for invoice matching
        
    CANCELLED: Order voided
        - Supplier unable to fulfill
        - Business requirement changed
        - Duplicated order
    """
    DRAFT = "draft"
    APPROVED = "approved"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class ReservationStateCode(str, enum.Enum):
    """
    Inventory reservation state codes.
    
    Reservations temporarily allocate inventory to specific orders or purposes,
    reducing the available quantity without physically moving the goods.
    
    ACTIVE: Reservation currently in effect
        - Inventory allocated to order/purpose
        - Reduces available quantity
        - Prevents double-allocation
        
    FULFILLED: Reservation consumed by shipment
        - Goods physically shipped
        - Reservation no longer needed
        - Historical record of allocation
        
    EXPIRED: Reservation time limit exceeded
        - Automatic expiration based on expires_at timestamp
        - Inventory released back to available pool
        - May indicate order cancellation or delay
        
    CANCELLED: Reservation manually voided
        - Order cancelled before fulfillment
        - Priority changed
        - Allocation error corrected
    """
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SerialStateCode(str, enum.Enum):
    """
    Serial number lifecycle state codes.
    
    Serial tracking is used for high-value items, regulated products,
    or goods requiring warranty management. Each serial number represents
    a unique physical item.
    
    State Transitions:
    IN_STOCK → RESERVED → SOLD
                ↓
             DEFECTIVE
    
    IN_STOCK: Available for sale/allocation
        - Physical item present in warehouse
        - Can be reserved for orders
        - Location tracked in serial_number.location_id
        
    RESERVED: Allocated to specific order
        - Held for customer
        - Not available for other orders
        - Awaiting shipment
        
    SOLD: Shipped to customer
        - No longer in warehouse
        - Warranty tracking active
        - Historical record for service/returns
        
    DEFECTIVE: Item damaged or non-functional
        - Segregated from saleable inventory
        - May be returned to supplier
        - May be scrapped or repaired
    
    Use Cases:
    - Electronics (laptops, phones, appliances)
    - Medical devices (regulatory compliance)
    - Luxury goods (authenticity tracking)
    - Tools/equipment (calibration, maintenance)
    """
    IN_STOCK = "in_stock"
    RESERVED = "reserved"
    SOLD = "sold"
    DEFECTIVE = "defective"


class LocationCategory(str, enum.Enum):
    """
    Storage location type classifications.
    
    Different location types have different characteristics:
    - Physical layout (rack vs floor)
    - Environmental controls (cold storage)
    - Access restrictions (quarantine)
    - Operational purpose (receiving vs shipping)
    
    STANDARD_RACK: Traditional pallet racking
        - Most common storage type
        - Multi-level vertical storage
        - Forklift accessible
        
    HIGH_SHELF: Upper rack positions
        - Requires specialized equipment
        - Less frequently accessed items
        - May have weight restrictions
        
    FLOOR_SPACE: Ground-level storage
        - No racking required
        - Bulk items or oversized goods
        - High weight capacity
        
    COLD_STORAGE: Temperature-controlled area
        - Refrigerated or frozen
        - Food, pharmaceuticals, chemicals
        - Special handling requirements
        
    QUARANTINE_ZONE: Restricted access area
        - Items pending quality inspection
        - Damaged/defective goods
        - Recalled products
        - Controlled release
        
    RECEIVING_DOCK: Inbound staging area
        - Temporary holding for arriving goods
        - Inspection and counting area
        - Before putaway to storage
        
    SHIPPING_DOCK: Outbound staging area
        - Picked items awaiting shipment
        - Packing and loading area
        - Carrier pickup zone
    
    Usage in Picking Strategy:
    Location types help optimize picking routes and storage allocation.
    """
    STANDARD_RACK = "standard_rack"
    HIGH_SHELF = "high_shelf"
    FLOOR_SPACE = "floor_space"
    COLD_STORAGE = "cold_storage"
    QUARANTINE_ZONE = "quarantine_zone"
    RECEIVING_DOCK = "receiving_dock"
    SHIPPING_DOCK = "shipping_dock"


class PartnerTypeCode(str, enum.Enum):
    """
    Business partner type classifications.
    
    Used for both suppliers and customers to determine:
    - Applicable regulations (tax, reporting)
    - Contract terms and conditions
    - Payment terms and credit limits
    - Communication protocols
    
    INDIVIDUAL: Natural person/sole proprietor
        - Consumer purchases or small vendors
        - Simplified invoicing
        - Personal guarantees
        
    CORPORATION: Registered business entity
        - Most common business type
        - Corporate tax ID required
        - Purchase orders and contracts
        
    GOVERNMENT: Government agency or entity
        - Special procurement rules
        - Extended payment terms
        - Compliance requirements
        - Tax-exempt status possible
        
    NON_PROFIT: Non-profit organization
        - Tax-exempt status
        - Grant-funded purchases
        - Special pricing considerations
    
    Future Extensions:
    - PARTNERSHIP: Business partnerships
    - LLC: Limited liability company
    - INTERNATIONAL: Cross-border entities
    """
    INDIVIDUAL = "individual"
    CORPORATION = "corporation"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
