# Warehouse Nexus System

## Architecture Overview

This warehouse management system implements a unique architecture with the following components:

- **warehouse_nexus/cerebrum**: Configuration and database connection management
- **warehouse_nexus/schema_registry**: Complete database entity definitions (23 tables)
- **warehouse_nexus/data_contracts**: Pydantic validation schemas
- **warehouse_nexus/business_conductors**: Business logic orchestrators
- **warehouse_nexus/api_gateways**: FastAPI HTTP endpoints

## Database Schema

The system implements 24 interconnected tables:

1. **unit_of_measure** - Measurement units with conversion factors
2. **product_category** - Hierarchical product categorization
3. **product** - Master product records
4. **product_variant** - Product variants with attributes
5. **supplier** - Vendor/supplier management
6. **customer** - Customer/client management
7. **price_list** - Pricing strategies
8. **price_rule** - Individual pricing rules
9. **warehouse** - Physical warehouse facilities
10. **storage_location** - Storage zones within warehouses
11. **inventory_balance** - Real-time inventory balances
12. **inventory_reservation** - Inventory reservations
13. **lot** - Batch/lot tracking
14. **serial_number** - Serial number tracking
15. **purchase_order** - Purchase order headers
16. **purchase_order_line** - Purchase order line items
17. **sales_order** - Sales order headers
18. **sales_order_line** - Sales order line items
19. **stock_document** - Stock movement document headers
20. **stock_document_line** - Stock movement line items
21. **stock_movement** - Materialized movement transactions
22. **stocktake** - Physical inventory count sessions
23. **stocktake_line** - Physical count records
24. **audit_log** - System audit trail

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file with either DB_ (for Google Cloud SQL) or QW_ (legacy) prefixes:

#### Option A: Google Cloud SQL with DB_ Secrets (Recommended for Cloud)

```
DB_HOST=34.40.117.250
DB_PORT=5432
DB_NAME=nexus_warehouse
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_SSL_MODE=require

# Optional: Cloud SQL Connector instance name
# DB_CLOUD_SQL_INSTANCE=cogent-quarter-486519:13:europe-west3:lms-backend-db

QW_GATEWAY_MOUNT_POINT=/api/v1
QW_NEXUS_DESIGNATION=WarehouseNexus
QW_DIAGNOSTIC_VERBOSITY=True
```

#### Option B: Legacy QW_ Prefix (Backward Compatible)

```
QW_PSQL_NODE_HOSTNAME=localhost
QW_PSQL_NODE_TCP_PORT=5432
QW_PSQL_SCHEMA_VAULT=nexus_warehouse
QW_PSQL_AUTH_PRINCIPAL=nexus_user
QW_PSQL_AUTH_TOKEN=your_password
QW_GATEWAY_MOUNT_POINT=/api/v1
QW_NEXUS_DESIGNATION=WarehouseNexus
QW_DIAGNOSTIC_VERBOSITY=True
```

**Note:** DB_ variables take precedence over QW_ variables. This allows for seamless migration to Cloud SQL while maintaining backward compatibility.

**SSL Mode Options:**
- `disable`: No SSL connection
- `allow`: Try SSL, fallback to non-SSL
- `prefer`: Try SSL first (default)
- `require`: Require SSL connection
- `verify-ca`: Require SSL with CA verification
- `verify-full`: Require SSL with full verification

### 3. Initialize Database

```bash
# Create database
createdb nexus_warehouse

# Run migrations
alembic -c alembic.ini upgrade head
```

### 4. Launch Application

```bash
python launch_nexus.py
```

Or with uvicorn:

```bash
uvicorn launch_nexus:nexus_application --host 0.0.0.0 --port 8000 --reload
```

### 5. Access API Documentation

Navigate to: `http://localhost:8000/api/v1/docs`

## Key Features

### Stock Document Posting

The system implements sophisticated document posting logic:

1. Create stock document in DRAFT state
2. Add line items with products, quantities, locations
3. POST the document via `/api/v1/stock-documents/post`
4. System automatically:
   - Creates stock_movement records
   - Updates inventory_balance tables
   - Records audit trail
   - Changes document status to POSTED

### Document Types

- **RECEIVING**: Increases inventory at destination
- **SHIPPING**: Decreases inventory at source
- **TRANSFER**: Moves between locations
- **ADJUSTMENT**: Corrects inventory quantities
- **MANUFACTURING_CONSUMPTION**: Material consumption
- **MANUFACTURING_OUTPUT**: Production output

### Inventory Tracking

- Real-time balance tracking per location
- Lot/batch tracking for traceability
- Serial number tracking for individual items
- Reservation management
- Available-to-promise calculations

## API Endpoints

### Products

- `POST /api/v1/products/uom` - Create unit of measure
- `GET /api/v1/products/uom` - List units
- `POST /api/v1/products/categories` - Create category
- `GET /api/v1/products/categories` - List categories
- `POST /api/v1/products/` - Create product
- `GET /api/v1/products/` - List products
- `GET /api/v1/products/{id}` - Get product details
- `POST /api/v1/products/variants` - Create variant
- `GET /api/v1/products/{id}/variants` - List variants

### Stock Movements

- `POST /api/v1/stock-documents/` - Create document with lines
- `GET /api/v1/stock-documents/` - List documents
- `GET /api/v1/stock-documents/{id}` - Get document details
- `POST /api/v1/stock-documents/post` - Post/finalize document

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

## Database Migrations

```bash
# Create new migration
alembic -c alembic.ini revision --autogenerate -m "description"

# Apply migrations
alembic -c alembic.ini upgrade head

# Rollback one revision
alembic -c alembic.ini downgrade -1

# View current revision
alembic -c alembic.ini current

# View migration history
alembic -c alembic.ini history
```

## Project Structure

```
warehouse_nexus/
├── cerebrum/              # Configuration & DB connection
│   ├── configuration_nucleus.py
│   └── psql_conductor.py
├── schema_registry/       # SQLAlchemy models
│   ├── categorical_taxonomy.py
│   ├── core_entities.py
│   ├── partner_entities.py
│   ├── pricing_entities.py
│   ├── facility_entities.py
│   ├── inventory_entities.py
│   ├── order_entities.py
│   ├── stock_entities.py
│   └── audit_entities.py
├── data_contracts/        # Pydantic schemas
│   ├── core_contracts.py
│   └── stock_contracts.py
├── business_conductors/   # Business logic
│   └── posting_conductor.py
└── api_gateways/          # FastAPI routes
    ├── product_gateway.py
    └── stock_gateway.py

alembic_nexus/             # Database migrations
├── versions/
│   └── 001_initial_schema_v1.py
└── env.py

launch_nexus.py            # Application entry point
requirements.txt           # Python dependencies
alembic.ini               # Alembic configuration
```

## Business Logic Example

### Creating and Posting a Receiving Document

```python
import requests
from datetime import date

# Create receiving document
doc_payload = {
    "doc_number": "RCV-2024-001",
    "doc_type": "receiving",
    "dest_warehouse_id": "warehouse-uuid",
    "doc_date": str(date.today()),
    "lines": [
        {
            "line_number": "1",
            "product_id": "product-uuid",
            "dest_location_id": "location-uuid",
            "quantity": 100.0,
            "uom_id": "uom-uuid"
        }
    ]
}

response = requests.post(
    "http://localhost:8000/api/v1/stock-documents/",
    json=doc_payload
)
doc_id = response.json()["doc_id"]

# Post the document
post_response = requests.post(
    "http://localhost:8000/api/v1/stock-documents/post",
    json={"doc_id": doc_id}
)

print(post_response.json())
# Output: {
#   "success": true,
#   "document_id": "...",
#   "movements_generated": 1,
#   "posted_timestamp": "2024-..."
# }
```

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.
