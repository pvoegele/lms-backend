# Warehouse Nexus - Complete Codebase Explanation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Directory Structure](#directory-structure)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Business Logic](#business-logic)
9. [Configuration](#configuration)
10. [Deployment](#deployment)

## Overview

Warehouse Nexus is an advanced warehouse management system (WMS) built with modern Python technologies. The system provides comprehensive inventory management capabilities including:

- **Product Management**: Hierarchical categorization, variants, and unit of measure tracking
- **Inventory Control**: Real-time balance tracking per location with lot and serial number support
- **Stock Movement**: Document-driven inventory transactions with automatic balance updates
- **Order Management**: Purchase and sales order processing with fulfillment tracking
- **Audit Trail**: Complete system activity logging for compliance and troubleshooting

### Technology Stack
- **Framework**: FastAPI (modern, high-performance web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Validation**: Pydantic for data validation and serialization
- **Migrations**: Alembic for database schema versioning
- **Deployment**: Vercel-compatible serverless architecture

## Architecture

The system follows a layered architecture pattern:

```
┌─────────────────────────────────────────────────────┐
│             API Gateway Layer (FastAPI)              │
│  - HTTP endpoints, request validation, routing      │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│        Data Contracts Layer (Pydantic)              │
│  - Request/response schemas, validation rules       │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│       Business Conductors Layer (Business Logic)     │
│  - Domain logic, workflow orchestration             │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│       Schema Registry Layer (SQLAlchemy ORM)        │
│  - Database models, relationships, constraints      │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│     Cerebrum Layer (Configuration & DB Connection)   │
│  - Environment config, connection pooling           │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│              PostgreSQL Database                     │
└─────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Each layer has a distinct responsibility
2. **Dependency Injection**: Database sessions injected into route handlers
3. **Type Safety**: Pydantic models ensure type correctness at runtime
4. **Document-Driven**: Stock movements follow a document-based workflow (draft → posted)
5. **Audit Trail**: All significant operations are logged for compliance

## Directory Structure

```
lms-backend/
├── launch_nexus.py              # Main application entry point
├── api/
│   └── index.py                 # Vercel deployment adapter
├── warehouse_nexus/             # Main application package
│   ├── cerebrum/                # Configuration and database layer
│   │   ├── configuration_nucleus.py    # Environment config management
│   │   └── psql_conductor.py           # Database connection pooling
│   ├── schema_registry/         # SQLAlchemy ORM models
│   │   ├── categorical_taxonomy.py     # Enums for state management
│   │   ├── core_entities.py            # Products, UOM, categories
│   │   ├── partner_entities.py         # Suppliers and customers
│   │   ├── facility_entities.py        # Warehouses and locations
│   │   ├── inventory_entities.py       # Balances, lots, serials
│   │   ├── stock_entities.py           # Stock documents and movements
│   │   ├── order_entities.py           # Purchase and sales orders
│   │   ├── pricing_entities.py         # Price lists and rules
│   │   └── audit_entities.py           # Audit logging
│   ├── data_contracts/          # Pydantic validation schemas
│   │   ├── core_contracts.py           # Product domain contracts
│   │   ├── stock_contracts.py          # Stock movement contracts
│   │   └── customer_contracts.py       # Customer domain contracts
│   ├── business_conductors/     # Business logic orchestrators
│   │   └── posting_conductor.py        # Stock document posting logic
│   └── api_gateways/            # FastAPI route handlers
│       ├── product_gateway.py          # Product management endpoints
│       ├── stock_gateway.py            # Stock movement endpoints
│       └── customer_gateway.py         # Customer management endpoints
├── alembic_nexus/               # Database migrations
│   ├── env.py                   # Alembic environment setup
│   └── versions/                # Migration scripts
├── tests/                       # Test suite
│   ├── test_basic_system.py
│   └── test_vercel_entrypoint.py
├── requirements.txt             # Python dependencies
├── alembic.ini                  # Alembic configuration
├── .env.example                 # Environment variable template
└── README.md                    # User documentation
```

## Core Components

### 1. Cerebrum (Brain) - Configuration & Database

**Purpose**: Centralized configuration management and database connection pooling

#### configuration_nucleus.py
- **CerebrumConfig**: Pydantic settings class that loads from environment variables
  - Database connection parameters (host, port, database name, credentials)
  - API configuration (mount point, application name)
  - Diagnostic settings (logging verbosity)
- **ConfigurationSingleton**: Thread-safe singleton pattern for config access
- **Environment Variable Prefix**: All config vars use `QW_` prefix (e.g., `QW_PSQL_NODE_HOSTNAME`)

#### psql_conductor.py
- **psql_conductor**: SQLAlchemy engine with connection pooling
  - QueuePool with 15 base connections, 30 overflow
  - Pre-ping for connection health checks
  - 30-minute connection recycling
  - UTC timezone enforcement
- **TransactionFactory**: Session factory with explicit transaction control
- **EntityFoundation**: Declarative base for all ORM models
- **TransactionConductor**: Helper class for transaction lifecycle management
- **harvest_session()**: Dependency injection function for FastAPI routes

### 2. Schema Registry - Database Models

All database tables are defined as SQLAlchemy ORM models inheriting from `EntityFoundation`.

#### categorical_taxonomy.py
Enumerations defining valid states and categories:
- **StockDocumentCategory**: receiving, shipping, transfer, adjustment, manufacturing
- **DocumentStateCode**: draft, posted, cancelled
- **SalesOrderStateCode**: draft → confirmed → fulfilled
- **PurchaseOrderStateCode**: draft → approved → received
- **ReservationStateCode**: active, fulfilled, expired, cancelled
- **SerialStateCode**: in_stock, reserved, sold, defective
- **LocationCategory**: Types of storage locations
- **PartnerTypeCode**: Business partner classifications

#### core_entities.py - Product Domain
1. **UnitOfMeasure**: Measurement units (kg, pieces, liters, etc.)
   - Conversion factors for unit conversions
   - Base unit identification
   - Category grouping (weight, volume, count)

2. **ProductCategory**: Hierarchical product categorization
   - Self-referential relationship for parent/child structure
   - Unlimited depth hierarchy support
   - Unique code and name constraints

3. **Product**: Master product definition
   - SKU (Stock Keeping Unit) as unique identifier
   - Category assignment
   - Base unit of measure
   - Tracking flags (lot tracking, serial tracking)
   - Active/inactive status

4. **ProductVariant**: Product variations (color, size, etc.)
   - References parent product
   - Own SKU for independent tracking
   - Attributes stored as text (flexible schema)

#### partner_entities.py - Business Partners
1. **Supplier**: Vendor management
   - Contact information
   - Payment terms
   - Active status

2. **Customer**: Client management
   - Contact details
   - Credit limit tracking
   - Customer type classification
   - Tax ID for compliance

#### facility_entities.py - Physical Infrastructure
1. **Warehouse**: Physical warehouse facilities
   - Unique name and code
   - Address and manager information
   - Active status flag
   - One-to-many relationship with storage locations

2. **StorageLocation**: Storage zones within warehouses
   - Warehouse-unique code (e.g., A-01-02)
   - Location type (rack, shelf, floor, dock, etc.)
   - Availability status
   - Composite unique index on warehouse + code

#### inventory_entities.py - Inventory State
1. **InventoryBalance**: Real-time inventory quantities
   - Quantity on hand (physical count)
   - Quantity reserved (allocated but not shipped)
   - Quantity available (on hand - reserved)
   - Tracked per: product, variant, warehouse, location, lot
   - Composite index for efficient lookups
   - Check constraints enforce positive quantities

2. **InventoryReservation**: Temporary allocations
   - References product, location
   - Quantity and status
   - Optional expiration timestamp
   - Reference field for order/document linking

3. **Lot**: Batch/lot tracking for traceability
   - Lot number (not globally unique, scoped to product)
   - Manufacturing and expiry dates
   - Supplier reference
   - Used for quality control and recall management

4. **SerialNumber**: Individual item tracking
   - Globally unique serial number
   - Current location tracking
   - Status (in stock, reserved, sold, defective)
   - Warranty expiry date
   - Used for high-value or regulated items

#### stock_entities.py - Stock Movement Documentation
1. **StockDocument**: Header for stock transaction
   - Unique document number (e.g., RCV-2024-001)
   - Document type (receiving, shipping, transfer, adjustment)
   - Status (draft, posted, cancelled)
   - Source and destination warehouses
   - Document date and posting timestamp
   - Reference field for external document numbers

2. **StockDocumentLine**: Line items on stock document
   - References parent document
   - Line number (1, 2, 3...)
   - Product and optional variant
   - Source and destination locations
   - Quantity and unit of measure
   - Optional lot tracking

3. **StockMovement**: Materialized transaction record
   - Created when document is posted
   - Immutable record of inventory movement
   - Denormalized for query performance
   - Includes all relevant IDs (product, locations, warehouses)
   - Movement timestamp for transaction time

#### order_entities.py - Order Management
1. **PurchaseOrder**: Purchase order header
   - Order number and supplier
   - Order and expected dates
   - Status tracking
   - Total amount

2. **PurchaseOrderLine**: Purchase order items
   - Product and quantity
   - Unit price
   - Received quantity tracking

3. **SalesOrder**: Sales order header
   - Order number and customer
   - Order and delivery dates
   - Status and total amount

4. **SalesOrderLine**: Sales order items
   - Product and quantity
   - Unit price
   - Fulfilled quantity tracking

#### pricing_entities.py - Price Management
1. **PriceList**: Price list definition
   - Name and currency
   - Validity dates
   - Active status

2. **PriceRule**: Individual pricing rules
   - Product or variant specific
   - Base and sale prices
   - Minimum quantity tiers
   - Effective date range

#### audit_entities.py - Audit Trail
**AuditLog**: Complete activity logging
- Category and action description
- Entity type and ID being modified
- User ID performing action
- Old and new values (JSON)
- Timestamp and IP address
- Used for compliance, debugging, and analytics

### 3. Data Contracts - Pydantic Schemas

Pydantic models define the structure and validation rules for API requests and responses.

#### core_contracts.py
Request/response pairs for product domain:
- **UnitOfMeasureCreate / UnitOfMeasureResponse**
- **ProductCategoryCreate / ProductCategoryResponse**
- **ProductCreate / ProductResponse**
- **ProductVariantCreate / ProductVariantResponse**

Pattern: Create schemas have input fields, Response schemas add generated fields (IDs, timestamps)

#### stock_contracts.py
Complex nested schemas for stock operations:
- **StockDocumentLineCreate**: Line item input
- **StockDocumentCreateWithLines**: Document with embedded lines array
- **StockDocumentResponse**: Document details
- **StockDocumentWithLines**: Document with lines (nested response)
- **PostDocumentCommand**: Command to finalize document

#### customer_contracts.py
Customer domain contracts:
- **CustomerCreate / CustomerResponse**
- **CustomerUpdate**: Partial update schema

### 4. Business Conductors - Domain Logic

#### posting_conductor.py
**PostingConductor**: Orchestrates stock document posting workflow

**Main Method: conduct_posting(document_id)**
1. **Validation Phase**:
   - Retrieves document from database
   - Verifies document exists
   - Checks status is DRAFT (only draft documents can be posted)
   - Ensures document has line items

2. **Movement Generation Phase**:
   - For each line item, creates a StockMovement record
   - Copies relevant data from document and line
   - Sets movement timestamp

3. **Balance Update Phase**:
   - Routes to appropriate logic based on document type:
     - **RECEIVING**: Increases inventory at destination
     - **SHIPPING**: Decreases inventory at source
     - **TRANSFER**: Decreases source, increases destination
     - **ADJUSTMENT**: Applies signed adjustment
     - **MANUFACTURING**: Handles material consumption and output
   - Updates InventoryBalance records
   - Creates new balance records if needed
   - Recalculates available quantity (on_hand - reserved)

4. **Status Update Phase**:
   - Sets document status to POSTED
   - Records posted_at timestamp

5. **Audit Phase**:
   - Creates AuditLog entry
   - Records old and new status
   - Documents movement count

**Helper Methods**:
- `_generate_movement()`: Creates movement from document line
- `_apply_balance_adjustment()`: Routes to correct adjustment logic
- `_adjust_location_balance()`: Updates or creates balance record
- `_create_audit_record()`: Logs the posting operation

**Transaction Management**: Caller is responsible for committing the database transaction, allowing for rollback if needed.

### 5. API Gateways - HTTP Endpoints

FastAPI routers defining RESTful HTTP endpoints.

#### product_gateway.py
**Routes**:
- `POST /products/uom` - Create unit of measure
- `GET /products/uom` - List units (paginated)
- `POST /products/categories` - Create category
- `GET /products/categories` - List categories (paginated)
- `POST /products/` - Create product
- `GET /products/` - List products (with active filter)
- `GET /products/{product_id}` - Get single product (404 if not found)
- `POST /products/variants` - Create variant
- `GET /products/{product_id}/variants` - List variants for product

**Pattern**: All routes use dependency injection for database sessions via `Depends(harvest_session)`

#### stock_gateway.py
**Routes**:
- `POST /stock-documents/` - Create document with lines (atomic operation)
- `GET /stock-documents/` - List documents with filters (type, status, date range)
- `GET /stock-documents/{doc_id}` - Get single document with lines
- `POST /stock-documents/post` - Post/finalize document (triggers posting workflow)

**Complex Operations**:
- Document creation is transactional (header + all lines)
- Posting operation calls PostingConductor
- Returns detailed results including movement count

#### customer_gateway.py
**Routes**:
- `POST /customers/` - Create customer
- `GET /customers/` - List customers (paginated)
- `GET /customers/{customer_id}` - Get single customer
- `PATCH /customers/{customer_id}` - Update customer (partial updates allowed)

### 6. Application Bootstrap - launch_nexus.py

Main application initialization and configuration.

**Components**:
1. **FastAPI Application**:
   - Title, description, version from config
   - Custom documentation URLs (docs, redoc, openapi)
   - Mounted at configured prefix (default: /api/v1)

2. **CORS Middleware**:
   - Permissive settings (all origins, all methods)
   - Supports credentials
   - Suitable for development and internal use

3. **Timing Middleware**:
   - Measures request processing time
   - Adds X-Processing-Time header to responses
   - Useful for performance monitoring

4. **Core Endpoints**:
   - `GET /` - Redirects to Swagger documentation
   - `GET /health` - Health check (always returns healthy)

5. **Router Mounting**:
   - Includes product_gateway at /api/v1/products
   - Includes stock_gateway at /api/v1/stock-documents
   - Includes customer_gateway at /api/v1/customers

6. **Development Server**:
   - `if __name__ == "__main__"` block runs uvicorn
   - Hot reload enabled if diagnostic_verbosity is True
   - Listens on 0.0.0.0:8000 (all interfaces)

## Data Flow

### Example: Receiving Inventory

1. **User creates stock document** (via API):
   ```
   POST /api/v1/stock-documents/
   {
     "doc_number": "RCV-2024-001",
     "doc_type": "receiving",
     "dest_warehouse_id": "...",
     "doc_date": "2024-01-15",
     "lines": [
       {
         "line_number": "1",
         "product_id": "...",
         "dest_location_id": "...",
         "quantity": 100,
         "uom_id": "..."
       }
     ]
   }
   ```

2. **API Gateway** (stock_gateway.py):
   - Validates request against StockDocumentCreateWithLines schema
   - Injects database session

3. **Route Handler**:
   - Creates StockDocument entity (status: DRAFT)
   - Creates StockDocumentLine entities
   - Commits transaction
   - Returns created document with IDs

4. **User posts document**:
   ```
   POST /api/v1/stock-documents/post
   {
     "doc_id": "..."
   }
   ```

5. **Posting Conductor**:
   - Validates document is in DRAFT state
   - For each line:
     - Creates StockMovement record
     - Updates InventoryBalance (increases quantity at destination)
   - Updates document status to POSTED
   - Creates audit log entry
   - Commits transaction

6. **Result**:
   - Inventory balance increased at destination location
   - Immutable movement record created
   - Document permanently posted (cannot be edited)
   - Audit trail recorded

### State Transitions

**Stock Document Lifecycle**:
```
DRAFT → POSTED
  ↓
CANCELLED
```
- DRAFT: Can be edited, lines can be modified
- POSTED: Immutable, inventory updated, movements created
- CANCELLED: Discarded, no inventory impact

**Purchase Order Lifecycle**:
```
DRAFT → APPROVED → PARTIALLY_RECEIVED → RECEIVED
  ↓
CANCELLED
```

**Sales Order Lifecycle**:
```
DRAFT → CONFIRMED → PARTIALLY_FULFILLED → FULFILLED
  ↓
CANCELLED
```

## Database Schema

### Relationships

**Product Hierarchy**:
```
ProductCategory (self-referential)
    ↓
Product
    ↓
ProductVariant
```

**Inventory Structure**:
```
Warehouse
    ↓
StorageLocation
    ↓
InventoryBalance (product, variant, lot)
```

**Stock Movement**:
```
StockDocument (header)
    ↓
StockDocumentLine (detail)
    ↓
StockMovement (materialized transaction)
    ↓
InventoryBalance (updated)
```

**Order Management**:
```
PurchaseOrder → PurchaseOrderLine → Product
SalesOrder → SalesOrderLine → Product
```

### Key Indexes

Performance-critical indexes:
- Product SKU (unique, indexed)
- Document number (unique, indexed)
- Stock document type and status (filtered queries)
- Inventory balance composite (product + variant + warehouse + location + lot)
- Movement timestamp (time-series queries)
- Serial number (unique, indexed)

### Constraints

Data integrity constraints:
- Quantity on hand must be >= 0 (check constraint)
- Quantity reserved must be >= 0 (check constraint)
- Unique SKUs per product and variant
- Unique document numbers
- Foreign key constraints with appropriate cascade rules

## API Endpoints

### Authentication
Current version: No authentication (suitable for internal use)
Future: JWT token-based authentication planned

### Pagination
Standard query parameters:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100, max: 100)

### Error Handling
- 400: Bad Request (validation errors)
- 404: Not Found (resource doesn't exist)
- 422: Unprocessable Entity (Pydantic validation)
- 500: Internal Server Error (unexpected errors)

### Response Format
Success responses follow REST conventions:
- 200 OK: Successful GET/PATCH
- 201 Created: Successful POST
- 204 No Content: Successful DELETE

Error responses include detail field:
```json
{
  "detail": "Error description"
}
```

## Business Logic

### Document Posting Rules

1. **Only DRAFT documents can be posted**
2. **Documents must have at least one line**
3. **Posting is atomic** (all or nothing)
4. **Inventory updates are immediate**
5. **Movements are immutable once created**

### Inventory Balance Updates

**RECEIVING**:
- Increases quantity at destination location
- Creates balance record if none exists

**SHIPPING**:
- Decreases quantity at source location
- Allows negative balances (over-shipping handled by business rules)

**TRANSFER**:
- Decreases source, increases destination
- Atomic operation (both or neither)

**ADJUSTMENT**:
- Applies signed quantity adjustment
- Positive values increase, negative decrease
- Used for cycle counts, damage, loss

### Lot Tracking

When `track_by_lot` is enabled for a product:
- All movements must specify a lot
- Balances are maintained per lot
- Enables expiry management
- Supports recalls and traceability

### Serial Tracking

When `track_by_serial` is enabled:
- Each unit has unique serial number
- Individual item location tracking
- Status transitions (in_stock → reserved → sold)
- Warranty tracking per serial

## Configuration

### Environment Variables

All variables use `QW_` prefix:

**Database Configuration**:
- `QW_PSQL_NODE_HOSTNAME`: PostgreSQL host (default: localhost)
- `QW_PSQL_NODE_TCP_PORT`: PostgreSQL port (default: 5432)
- `QW_PSQL_SCHEMA_VAULT`: Database name (default: nexus_warehouse)
- `QW_PSQL_AUTH_PRINCIPAL`: Database username
- `QW_PSQL_AUTH_TOKEN`: Database password
- `QW_PSQL_URI_OVERRIDE`: Full connection string (overrides above)

**API Configuration**:
- `QW_GATEWAY_MOUNT_POINT`: API prefix (default: /api/v1)
- `QW_NEXUS_DESIGNATION`: Application name (default: WarehouseNexus)
- `QW_DIAGNOSTIC_VERBOSITY`: Enable SQL logging (default: True)

### Database Connection Pooling

Tuned for production workloads:
- **Pool size**: 15 connections (steady-state)
- **Max overflow**: 30 additional connections (peak load)
- **Pre-ping**: Connection health check before use
- **Pool recycle**: Connections recycled every 30 minutes
- **Timezone**: UTC enforced for consistency

## Deployment

### Local Development

1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` file with database credentials
3. Run migrations: `alembic -c alembic.ini upgrade head`
4. Start server: `python launch_nexus.py`
5. Access docs: http://localhost:8000/api/v1/docs

### Vercel Deployment

The system is designed for serverless deployment:

1. **Entry Point**: `api/index.py`
   - Exports FastAPI app as `app` variable
   - Vercel's Python runtime expects this structure

2. **Environment Variables**:
   - Configure in Vercel dashboard
   - Use connection string format for managed PostgreSQL

3. **Database**:
   - Use Vercel Postgres or external managed PostgreSQL
   - Connection pooling handled by SQLAlchemy

4. **Migrations**:
   - Run manually or via Vercel build step
   - `alembic upgrade head` in build script

### Database Migrations

Alembic manages schema evolution:

**Create Migration**:
```bash
alembic -c alembic.ini revision --autogenerate -m "description"
```

**Apply Migrations**:
```bash
alembic -c alembic.ini upgrade head
```

**Rollback**:
```bash
alembic -c alembic.ini downgrade -1
```

**View History**:
```bash
alembic -c alembic.ini history
```

## Testing

### Test Structure

- `tests/test_basic_system.py`: Core functionality tests
- `tests/test_vercel_entrypoint.py`: Deployment verification

### Running Tests

```bash
pytest tests/ -v
```

### Test Coverage

Current tests verify:
- Module imports
- Configuration singleton
- API endpoints (health check, redirect)
- Enum definitions
- Vercel deployment structure

## Security Considerations

### Current State
- No authentication implemented
- CORS allows all origins
- Suitable for internal/trusted networks only

### Recommendations for Production
1. **Authentication**: Implement JWT token-based auth
2. **Authorization**: Role-based access control (RBAC)
3. **CORS**: Restrict to specific origins
4. **Rate Limiting**: Prevent abuse
5. **Input Validation**: Enhanced validation (already strong with Pydantic)
6. **SQL Injection**: Protected by SQLAlchemy ORM
7. **Audit Logging**: Already implemented, enhance with user tracking

## Performance Considerations

### Database
- Indexes on all frequently queried columns
- Composite indexes for multi-column queries
- Connection pooling for efficiency
- Explicit transaction boundaries

### API
- Pagination on list endpoints
- Selective field loading (can be enhanced with GraphQL)
- Async support (FastAPI native)
- Response compression (can be added)

### Scalability
- Stateless design (scales horizontally)
- Database connection pooling
- Serverless-compatible architecture
- Can add Redis for caching

## Future Enhancements

1. **Barcode/QR Code Integration**: Scanning for receiving and picking
2. **Advanced Reporting**: Analytics and dashboards
3. **Mobile App**: Warehouse operations on mobile devices
4. **Integration APIs**: EDI, ERP, e-commerce platforms
5. **Advanced Picking Strategies**: FIFO, LIFO, wave picking
6. **Quality Control**: Inspection workflows and holds
7. **Returns Management**: RMA and reverse logistics
8. **Multi-tenancy**: Support multiple companies in one instance
9. **Internationalization**: Multi-language and multi-currency
10. **Real-time Notifications**: WebSocket for live updates

## Troubleshooting

### Common Issues

**Database Connection Errors**:
- Verify PostgreSQL is running
- Check credentials in `.env`
- Ensure database exists
- Test connection: `psql -h localhost -U nexus_user -d nexus_warehouse`

**Migration Errors**:
- Check alembic.ini database URL
- Ensure migrations folder has __init__.py
- Run with verbose: `alembic -c alembic.ini upgrade head --verbose`

**Import Errors**:
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check Python version (3.8+)
- Ensure PYTHONPATH includes project root

**API Errors**:
- Check FastAPI logs for details
- Verify request payload matches schema
- Use Swagger UI to test: /api/v1/docs
- Check database constraints aren't violated

## Conclusion

Warehouse Nexus is a comprehensive, production-ready warehouse management system built with modern best practices. The codebase is structured for maintainability, scalability, and extensibility. The document-driven approach to inventory management ensures data integrity and provides a complete audit trail.

Key strengths:
- ✅ Type-safe with Pydantic validation
- ✅ Robust database schema with constraints
- ✅ Clean separation of concerns
- ✅ Comprehensive inventory tracking
- ✅ Transaction integrity
- ✅ Audit trail
- ✅ RESTful API design
- ✅ Production-ready connection pooling
- ✅ Migration support for schema evolution
- ✅ Serverless deployment compatible

The system is ready for production use in internal/trusted environments and can be enhanced with authentication and authorization for external deployment.
