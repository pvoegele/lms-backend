"""
Warehouse Nexus Application Bootstrap
=====================================

This is the main application entry point that initializes and configures the FastAPI application.
It sets up:
- FastAPI application with custom configuration
- CORS middleware for cross-origin requests
- Custom timing middleware for performance monitoring
- Core health check and documentation redirect endpoints
- All API gateways (product, stock, customer management)

The application follows a modular architecture where different functional areas
(products, stock movements, customers) are organized into separate API gateways,
each with their own routers that are mounted onto the main FastAPI application.

Usage:
    Direct execution: python launch_nexus.py
    Via uvicorn: uvicorn launch_nexus:nexus_application --reload
    
Environment:
    Configuration is loaded from environment variables (see .env.example)
    All variables use the QW_ prefix (e.g., QW_PSQL_NODE_HOSTNAME)
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import time
from typing import Callable

from warehouse_nexus.cerebrum.configuration_nucleus import extract_runtime_config
from warehouse_nexus.api_gateways.product_gateway import product_gateway
from warehouse_nexus.api_gateways.stock_gateway import stock_gateway
from warehouse_nexus.api_gateways.customer_gateway import customer_gateway

# Extract operational configuration from environment variables
# This singleton pattern ensures configuration is loaded once and reused
operational_params = extract_runtime_config()

# Initialize FastAPI application with custom configuration
# The application name, version, and API documentation paths are configurable
# Default mount point is /api/v1, making all endpoints available at /api/v1/*
nexus_application = FastAPI(
    title=operational_params.nexus_designation,  # Application name from config (default: WarehouseNexus)
    description="Advanced Warehouse Management Nexus Platform",
    version="1.0.0",
    docs_url=f"{operational_params.gateway_mount_point}/docs",  # Swagger UI location
    redoc_url=f"{operational_params.gateway_mount_point}/redoc",  # ReDoc location
    openapi_url=f"{operational_params.gateway_mount_point}/openapi.json"  # OpenAPI schema
)

# Configure CORS (Cross-Origin Resource Sharing) with permissive settings
# WARNING: These settings allow all origins and are suitable for development/internal use only
# For production, restrict allow_origins to specific domains:
#   allow_origins=["https://yourdomain.com", "https://app.yourdomain.com"]
nexus_application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Accept requests from any origin (consider restricting in production)
    allow_credentials=True,  # Allow cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all request headers
)


# Custom timing middleware for performance monitoring
# This middleware wraps every HTTP request and measures processing time
@nexus_application.middleware("http")
async def inject_timing_headers(request: Request, call_next: Callable):
    """
    Middleware to inject request processing time into response headers.
    
    This measures the time taken to process each request and adds it to the
    response headers as 'X-Processing-Time' in seconds. Useful for:
    - Performance monitoring and optimization
    - Identifying slow endpoints
    - API response time SLAs
    - Client-side performance tracking
    
    Args:
        request: The incoming HTTP request
        call_next: Function to call the next middleware/endpoint
        
    Returns:
        Response with added X-Processing-Time header
    """
    start_timestamp = time.time()  # Record start time
    response = await call_next(request)  # Process the request through the chain
    processing_duration = time.time() - start_timestamp  # Calculate duration
    response.headers["X-Processing-Time"] = str(processing_duration)  # Add to response headers
    return response


# Root endpoint - redirect to Swagger UI
# Accessing the root URL (/) redirects users to the interactive API documentation
@nexus_application.get("/", include_in_schema=False)  # Excluded from OpenAPI schema
async def redirect_to_docs():
    """
    Redirect root URL to Swagger UI documentation.
    
    When users access the application root (e.g., http://localhost:8000/),
    they are automatically redirected to the Swagger UI where they can:
    - Browse all available API endpoints
    - See request/response schemas
    - Test endpoints interactively
    - View API documentation
    
    Returns:
        RedirectResponse (307 Temporary Redirect) to the docs URL
    """
    return RedirectResponse(url=f"{operational_params.gateway_mount_point}/docs")


# Health check endpoint - used by monitoring systems and load balancers
@nexus_application.get("/health")
async def system_vitals():
    """
    System health check endpoint.
    
    Returns the health status of the application and its components.
    This endpoint is typically called by:
    - Load balancers to determine if instance is healthy
    - Monitoring systems (Prometheus, Datadog, etc.)
    - Kubernetes liveness/readiness probes
    - CI/CD health checks after deployment
    
    Returns:
        dict: Health status with component details
            - status: Overall health (healthy/unhealthy)
            - components: Status of individual subsystems
            
    TODO: Add actual database health check by attempting a simple query
    TODO: Add version information for deployment tracking
    """
    return {
        "status": "healthy",
        "components": {
            "database": "connected",  # TODO: Verify with actual DB ping
            "api": "responsive",
            "routing": "active"
        }
    }


# Mount API gateways
# Each gateway is a separate APIRouter handling a specific domain area
# All are mounted at the same prefix but with different route paths

# Product Management Gateway: /api/v1/products/*
# Handles: units of measure, categories, products, variants
nexus_application.include_router(
    product_gateway,
    prefix=operational_params.gateway_mount_point
)

# Stock Movement Gateway: /api/v1/stock-documents/*
# Handles: stock document creation, listing, posting (finalizing)
nexus_application.include_router(
    stock_gateway,
    prefix=operational_params.gateway_mount_point
)

# Customer Management Gateway: /api/v1/customers/*
# Handles: customer CRUD operations
nexus_application.include_router(
    customer_gateway,
    prefix=operational_params.gateway_mount_point
)


# Development server entry point
# This block only runs when the file is executed directly (not imported)
if __name__ == "__main__":
    import uvicorn
    
    # Run the application using Uvicorn ASGI server
    # Uvicorn is a lightning-fast ASGI server implementation
    uvicorn.run(
        "launch_nexus:nexus_application",  # Import path to the FastAPI app
        host="0.0.0.0",  # Listen on all network interfaces (accessible externally)
        port=8000,  # Default HTTP port for the application
        reload=operational_params.diagnostic_verbosity  # Hot reload on code changes if diagnostics enabled
        # Additional options available:
        # - workers: Number of worker processes (for production)
        # - log_level: Logging verbosity (debug, info, warning, error)
        # - access_log: Enable/disable access logging
    )
