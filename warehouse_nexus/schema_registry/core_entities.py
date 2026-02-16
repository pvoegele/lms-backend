"""
Core Warehouse Entities - Foundational Domain Objects
=====================================================

This module defines the core product-related entities that form the foundation
of the warehouse management system:

1. **UnitOfMeasure**: How products are quantified (pieces, kg, liters)
2. **ProductCategory**: Hierarchical product classification
3. **Product**: Master product definition
4. **ProductVariant**: Product variations (size, color, etc.)

These entities follow the Product Information Management (PIM) pattern,
separating product master data from transactional data (orders, inventory).

Database Design Patterns:
- UUID primary keys for distributed systems
- Created/updated timestamps for audit trail
- Soft delete via is_active flags
- Self-referential relationships for hierarchies
- Optimistic locking via updated_at

All entities inherit from EntityFoundation (SQLAlchemy declarative base)
and use PostgreSQL-specific features (UUID type).

Usage:
    from warehouse_nexus.schema_registry.core_entities import Product, UnitOfMeasure
    
    # Query products
    products = session.query(Product).filter(Product.is_active == True).all()
    
    # Create new product
    product = Product(
        sku="LAPTOP-001",
        name="Business Laptop",
        base_uom_id=piece_uom.unit_id
    )
"""
from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, ForeignKey, Index, func as sql_func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from warehouse_nexus.cerebrum.psql_conductor import EntityFoundation
from datetime import datetime
from uuid import uuid4


def generate_uuid_v4():
    """
    UUID v4 generator for primary keys.
    
    UUIDs provide several advantages over auto-increment integers:
    - Globally unique (safe for distributed systems)
    - No coordination needed between instances
    - Non-sequential (security benefit)
    - Can be generated client-side
    
    Returns:
        UUID: Random UUID version 4
    """
    return uuid4()


class UnitOfMeasure(EntityFoundation):
    """
    Unit of measure registry for product quantification.
    
    Units of measure define how products are counted, weighed, or measured.
    The system supports:
    - Base units (fundamental units like kg, liter, piece)
    - Derived units with conversion factors (g = kg * 0.001)
    - Multiple unit categories (weight, volume, count, length)
    
    Conversion Logic:
    All conversions go through the base unit:
    - To convert A → B: (A * A.conversion_factor) / B.conversion_factor
    - Example: 1000g → kg: (1000 * 0.001) / 1.0 = 1 kg
    
    Attributes:
        unit_id: UUID primary key
        code: Short code (e.g., "KG", "PC", "L") - unique
        name: Full name (e.g., "Kilogram", "Piece", "Liter")
        category: Grouping (weight, volume, count, length, area, time)
        is_base_unit: True if this is the base unit for its category
        conversion_factor: Multiplier to convert to base unit
        created_at: Record creation timestamp
        updated_at: Last modification timestamp
    
    Examples:
        Weight category:
        - KG (Kilogram): is_base_unit=True, conversion_factor=1.0
        - G (Gram): is_base_unit=False, conversion_factor=0.001
        - LB (Pound): is_base_unit=False, conversion_factor=0.453592
        
        Count category:
        - PC (Piece): is_base_unit=True, conversion_factor=1.0
        - DZ (Dozen): is_base_unit=False, conversion_factor=12.0
        - CTN (Carton): is_base_unit=False, conversion_factor=24.0
    """
    __tablename__ = "unit_of_measure"
    
    # Primary key - UUID for distributed system compatibility
    unit_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid_v4)
    
    # Business key - short, unique code for display and input
    code = Column(String(20), unique=True, nullable=False, index=True)
    
    # Human-readable name
    name = Column(String(100), nullable=False)
    
    # Category for grouping related units (indexed for filtering)
    category = Column(String(50), nullable=False)
    
    # Flag indicating this is the base unit for its category
    # Each category should have exactly one base unit
    is_base_unit = Column(Boolean, default=False, nullable=False)
    
    # Conversion factor to base unit (1.0 for base units)
    # Precision of 20,6 supports: 99999999999999.999999
    conversion_factor = Column(Numeric(20, 6), nullable=False, default=1.0)
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_uom_category', 'category'),  # Fast filtering by category
    )


class ProductCategory(EntityFoundation):
    """
    Hierarchical product categorization system.
    
    Product categories organize products into a tree structure for:
    - Navigation and browsing (e.g., Electronics > Computers > Laptops)
    - Reporting and analytics
    - Permission management (access control by category)
    - Pricing and discount rules
    - Warehouse location assignment
    
    The hierarchy is implemented through a self-referential foreign key,
    allowing unlimited nesting depth:
    
    Electronics (parent_category_id=NULL)
    ├── Computers (parent_category_id=Electronics.id)
    │   ├── Laptops (parent_category_id=Computers.id)
    │   └── Desktops (parent_category_id=Computers.id)
    └── Accessories (parent_category_id=Electronics.id)
    
    Attributes:
        category_id: UUID primary key
        name: Display name (e.g., "Electronics", "Laptops")
        code: Unique code for API/integration (e.g., "ELEC", "LAP")
        parent_category_id: Reference to parent category (NULL for root)
        description: Optional detailed description
        created_at: Record creation timestamp
        updated_at: Last modification timestamp
        
    Relationships:
        parent_category: Reference to parent (many-to-one)
        child_categories: All direct children (one-to-many)
        products: All products in this category (one-to-many)
    
    Query Examples:
        # Get all root categories (top level)
        >>> roots = session.query(ProductCategory).filter(
        >>>     ProductCategory.parent_category_id == None
        >>> ).all()
        
        # Get all descendants (requires recursive CTE)
        # See SQLAlchemy documentation for recursive queries
    """
    __tablename__ = "product_category"
    
    category_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid_v4)
    name = Column(String(150), nullable=False, index=True)  # Indexed for search
    code = Column(String(50), unique=True, nullable=False)  # Unique business key
    
    # Self-referential foreign key for hierarchy
    # ondelete='SET NULL' means if parent is deleted, this becomes a root category
    parent_category_id = Column(
        PG_UUID(as_uuid=True), 
        ForeignKey('product_category.category_id', ondelete='SET NULL'), 
        nullable=True
    )
    
    description = Column(Text, nullable=True)  # Optional detailed description
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Self-referential relationship - links parent and children
    # remote_side=[category_id] indicates which side is "remote" (the parent)
    parent_category = relationship(
        "ProductCategory", 
        remote_side=[category_id],  # Parent is remote
        backref="child_categories"  # Children accessible via parent.child_categories
    )
    
    __table_args__ = (
        Index('ix_category_parent', 'parent_category_id'),  # Fast parent lookups
    )


class Product(EntityFoundation):
    """
    Master product definition - the core entity representing a sellable/trackable item.
    
    Products represent the master data for items managed in the warehouse.
    Each product can have multiple variants (e.g., different sizes, colors)
    but shares common attributes like name, description, and category.
    
    The product entity follows the "Product Master" pattern from ERP systems,
    where one master record governs multiple variants and transactions.
    
    Tracking Modes:
    The system supports three levels of tracking granularity:
    
    1. **Simple Tracking** (default):
       - track_by_lot=False, track_by_serial=False
       - Track only at product level
       - Example: Bulk commodities (screws, nails, sand)
    
    2. **Lot/Batch Tracking**:
       - track_by_lot=True, track_by_serial=False
       - Track groups of items by production batch
       - Example: Food products, chemicals, pharmaceuticals
       - Use cases: Expiry management, recalls, quality control
    
    3. **Serial Number Tracking**:
       - track_by_serial=True (lot tracking optional)
       - Track individual items uniquely
       - Example: Electronics, vehicles, equipment
       - Use cases: Warranty, service history, theft prevention
    
    Attributes:
        product_id: UUID primary key
        sku: Stock Keeping Unit - unique identifier for ordering/inventory
        name: Display name (e.g., "Wireless Mouse", "Office Chair")
        description: Detailed product description (marketing copy, specs)
        category_id: Reference to product category (optional)
        base_uom_id: Default unit of measure (e.g., pieces, kg)
        track_by_lot: Enable lot/batch tracking
        track_by_serial: Enable serial number tracking
        is_active: Soft delete flag (inactive products hidden but not deleted)
        created_at: Record creation timestamp
        updated_at: Last modification timestamp
        
    Relationships:
        category: ProductCategory (many-to-one)
        base_uom: UnitOfMeasure (many-to-one)
        variants: List of ProductVariant (one-to-many, via backref)
    
    Business Rules:
    - SKU must be unique across all products
    - Cannot delete if referenced by transactions (use is_active=False)
    - base_uom determines default unit for all transactions
    - Category assignment affects reporting and permissions
    
    Example:
        >>> mouse = Product(
        >>>     sku="TECH-MOUSE-001",
        >>>     name="Wireless Optical Mouse",
        >>>     description="Ergonomic design, 2.4GHz wireless, 1600 DPI",
        >>>     category_id=computer_accessories.category_id,
        >>>     base_uom_id=piece_uom.unit_id,
        >>>     track_by_lot=False,
        >>>     track_by_serial=True,  # Each mouse has unique serial
        >>>     is_active=True
        >>> )
    """
    __tablename__ = "product"
    
    product_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid_v4)
    
    # SKU: Stock Keeping Unit - unique business identifier
    # Used in barcodes, purchase orders, inventory tracking
    sku = Column(String(100), unique=True, nullable=False, index=True)
    
    name = Column(String(250), nullable=False)
    description = Column(Text, nullable=True)  # Rich text or markdown supported
    
    # Category assignment (optional, SET NULL if category deleted)
    category_id = Column(
        PG_UUID(as_uuid=True), 
        ForeignKey('product_category.category_id', ondelete='SET NULL'), 
        nullable=True
    )
    
    # Base unit of measure (required, must always have a UOM)
    base_uom_id = Column(
        PG_UUID(as_uuid=True), 
        ForeignKey('unit_of_measure.unit_id'), 
        nullable=False
    )
    
    # Tracking flags - determine inventory tracking granularity
    track_by_lot = Column(Boolean, default=False, nullable=False)
    track_by_serial = Column(Boolean, default=False, nullable=False)
    
    # Soft delete flag - inactive products hidden but data preserved
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    category = relationship("ProductCategory", backref="products")  # Many products per category
    base_uom = relationship("UnitOfMeasure")  # Unit of measure reference
    # variants relationship defined via backref in ProductVariant
    
    __table_args__ = (
        Index('ix_product_category', 'category_id'),  # Fast category filtering
        Index('ix_product_active', 'is_active'),  # Fast active/inactive filtering
    )


class ProductVariant(EntityFoundation):
    """
    Product variant with specific distinguishing attributes.
    
    Variants represent different configurations or options of a product,
    sharing the parent product's core characteristics but differing in:
    - Size (Small, Medium, Large)
    - Color (Red, Blue, Green)
    - Material (Cotton, Polyester, Silk)
    - Configuration (RAM/Storage options for electronics)
    - Bundle composition
    
    The variant pattern allows:
    - Separate inventory tracking per variant
    - Different pricing per variant
    - Specific ordering (customers order variants, not base products)
    - Consistent master data (shared from parent product)
    
    Data Model:
    - Each variant has its own unique SKU
    - Variants inherit tracking flags from parent product
    - Attributes stored as text (flexible schema)
    - Variants can be independently activated/deactivated
    
    Attributes:
        variant_id: UUID primary key
        product_id: Reference to parent product (CASCADE delete)
        sku: Unique SKU for this variant
        name: Variant display name (e.g., "Wireless Mouse - Black")
        attributes: JSON-like text field for variant-specific attributes
        is_active: Soft delete flag for this variant
        created_at: Record creation timestamp
        updated_at: Last modification timestamp
        
    Relationships:
        product: Parent Product (many-to-one)
    
    Attributes Field Format:
    Stored as text, can be:
    - Simple key-value: "Color: Blue, Size: Large"
    - JSON string: {"color": "blue", "size": "large"}
    - Markdown: Rendered in UI
    
    Business Rules:
    - Variant SKU must be globally unique (not just within product)
    - Cannot delete if referenced by transactions
    - Inherits tracking mode from parent product
    - When parent product deactivated, variants typically deactivated too
    
    Example:
        >>> # Parent product: T-Shirt
        >>> product = Product(sku="SHIRT-001", name="Cotton T-Shirt")
        >>> 
        >>> # Variants for different sizes and colors
        >>> variant_s_blue = ProductVariant(
        >>>     product_id=product.product_id,
        >>>     sku="SHIRT-001-S-BLU",
        >>>     name="Cotton T-Shirt - Small - Blue",
        >>>     attributes="Size: Small, Color: Blue",
        >>>     is_active=True
        >>> )
        >>> 
        >>> variant_m_red = ProductVariant(
        >>>     product_id=product.product_id,
        >>>     sku="SHIRT-001-M-RED",
        >>>     name="Cotton T-Shirt - Medium - Red",
        >>>     attributes=json.dumps({"size": "M", "color": "red"}),
        >>>     is_active=True
        >>> )
    
    Querying:
        # Get all variants for a product
        >>> variants = session.query(ProductVariant).filter(
        >>>     ProductVariant.product_id == product.product_id,
        >>>     ProductVariant.is_active == True
        >>> ).all()
        
        # Or via relationship
        >>> variants = product.variants
    """
    __tablename__ = "product_variant"
    
    variant_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid_v4)
    
    # Parent product reference (CASCADE means if product deleted, variants are too)
    product_id = Column(
        PG_UUID(as_uuid=True), 
        ForeignKey('product.product_id', ondelete='CASCADE'), 
        nullable=False
    )
    
    # Variant-specific SKU (globally unique)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    
    # Variant display name (typically includes parent name + attributes)
    name = Column(String(250), nullable=False)
    
    # Flexible attributes field - format is application-specific
    # Could be: "Color: Blue, Size: Large" or JSON or any other format
    attributes = Column(Text, nullable=True)
    
    # Soft delete flag - independent of parent product status
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to parent product
    # backref="variants" creates product.variants accessor
    product = relationship("Product", backref="variants")
    
    __table_args__ = (
        Index('ix_variant_product', 'product_id'),  # Fast lookup of product's variants
        Index('ix_variant_active', 'is_active'),  # Fast active/inactive filtering
    )
