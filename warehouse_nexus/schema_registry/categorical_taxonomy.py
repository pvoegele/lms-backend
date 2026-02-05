"""
Categorical Taxonomy - Enumerated state spaces for warehouse operations
Domain-specific enumerations representing discrete states
"""
import enum


class StockDocumentCategory(str, enum.Enum):
    """Categories of stock documentation"""
    RECEIVING = "receiving"
    SHIPPING = "shipping"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    MANUFACTURING_CONSUMPTION = "manufacturing_consumption"
    MANUFACTURING_OUTPUT = "manufacturing_output"


class DocumentStateCode(str, enum.Enum):
    """Document lifecycle state codes"""
    DRAFT = "draft"
    POSTED = "posted"
    CANCELLED = "cancelled"


class SalesOrderStateCode(str, enum.Enum):
    """Sales order state progression"""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class PurchaseOrderStateCode(str, enum.Enum):
    """Purchase order state progression"""
    DRAFT = "draft"
    APPROVED = "approved"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class ReservationStateCode(str, enum.Enum):
    """Inventory reservation states"""
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SerialStateCode(str, enum.Enum):
    """Serial number lifecycle states"""
    IN_STOCK = "in_stock"
    RESERVED = "reserved"
    SOLD = "sold"
    DEFECTIVE = "defective"


class LocationCategory(str, enum.Enum):
    """Storage location categories"""
    STANDARD_RACK = "standard_rack"
    HIGH_SHELF = "high_shelf"
    FLOOR_SPACE = "floor_space"
    COLD_STORAGE = "cold_storage"
    QUARANTINE_ZONE = "quarantine_zone"
    RECEIVING_DOCK = "receiving_dock"
    SHIPPING_DOCK = "shipping_dock"


class PartnerTypeCode(str, enum.Enum):
    """Business partner type classification"""
    INDIVIDUAL = "individual"
    CORPORATION = "corporation"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
