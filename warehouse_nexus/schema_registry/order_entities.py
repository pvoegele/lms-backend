"""
Order Entities - Purchase and sales order management
Complete order lifecycle tracking with line items
"""
from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, Date, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from warehouse_nexus.cerebrum.psql_conductor import EntityFoundation
from warehouse_nexus.schema_registry.categorical_taxonomy import PurchaseOrderStateCode, SalesOrderStateCode
from datetime import datetime
from uuid import uuid4


class PurchaseOrder(EntityFoundation):
    """Purchase order header"""
    __tablename__ = "purchase_order"
    
    po_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    po_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_id = Column(PG_UUID(as_uuid=True), ForeignKey('supplier.supplier_id', ondelete='SET NULL'), nullable=True)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey('warehouse.warehouse_id', ondelete='SET NULL'), nullable=True)
    order_date = Column(Date, nullable=False)
    expected_date = Column(Date, nullable=True)
    status = Column(Enum(PurchaseOrderStateCode, name='order_status_purchase'), nullable=False, default=PurchaseOrderStateCode.DRAFT)
    total_amount = Column(Numeric(15, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    supplier = relationship("Supplier")
    warehouse = relationship("Warehouse")
    
    __table_args__ = (
        Index('ix_po_supplier', 'supplier_id'),
        Index('ix_po_status', 'status'),
    )


class PurchaseOrderLine(EntityFoundation):
    """Purchase order line item"""
    __tablename__ = "purchase_order_line"
    
    po_line_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    po_id = Column(PG_UUID(as_uuid=True), ForeignKey('purchase_order.po_id', ondelete='CASCADE'), nullable=False)
    line_number = Column(String(10), nullable=False)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey('product.product_id', ondelete='SET NULL'), nullable=True)
    variant_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_variant.variant_id', ondelete='SET NULL'), nullable=True)
    quantity_ordered = Column(Numeric(15, 3), nullable=False)
    quantity_received = Column(Numeric(15, 3), nullable=False, default=0)
    unit_price = Column(Numeric(15, 4), nullable=True)
    line_total = Column(Numeric(15, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    purchase_order = relationship("PurchaseOrder", backref="order_lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    
    __table_args__ = (
        Index('ix_po_line_po', 'po_id'),
    )


class SalesOrder(EntityFoundation):
    """Sales order header"""
    __tablename__ = "sales_order"
    
    so_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    so_number = Column(String(100), unique=True, nullable=False, index=True)
    customer_id = Column(PG_UUID(as_uuid=True), ForeignKey('customer.customer_id', ondelete='SET NULL'), nullable=True)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey('warehouse.warehouse_id', ondelete='SET NULL'), nullable=True)
    order_date = Column(Date, nullable=False)
    requested_date = Column(Date, nullable=True)
    status = Column(Enum(SalesOrderStateCode, name='order_status_sales'), nullable=False, default=SalesOrderStateCode.DRAFT)
    total_amount = Column(Numeric(15, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    customer = relationship("Customer")
    warehouse = relationship("Warehouse")
    
    __table_args__ = (
        Index('ix_so_customer', 'customer_id'),
        Index('ix_so_status', 'status'),
    )


class SalesOrderLine(EntityFoundation):
    """Sales order line item"""
    __tablename__ = "sales_order_line"
    
    so_line_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    so_id = Column(PG_UUID(as_uuid=True), ForeignKey('sales_order.so_id', ondelete='CASCADE'), nullable=False)
    line_number = Column(String(10), nullable=False)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey('product.product_id', ondelete='SET NULL'), nullable=True)
    variant_id = Column(PG_UUID(as_uuid=True), ForeignKey('product_variant.variant_id', ondelete='SET NULL'), nullable=True)
    quantity_ordered = Column(Numeric(15, 3), nullable=False)
    quantity_fulfilled = Column(Numeric(15, 3), nullable=False, default=0)
    unit_price = Column(Numeric(15, 4), nullable=True)
    line_total = Column(Numeric(15, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    sales_order = relationship("SalesOrder", backref="order_lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    
    __table_args__ = (
        Index('ix_so_line_so', 'so_id'),
    )
