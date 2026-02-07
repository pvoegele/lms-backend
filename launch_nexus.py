"""
Warehouse Nexus Application Bootstrap
Central initialization point with custom middleware and routing orchestration
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

# Extract operational configuration
operational_params = extract_runtime_config()

# Initialize FastAPI application with custom configuration
nexus_application = FastAPI(
    title=operational_params.nexus_designation,
    description="Advanced Warehouse Management Nexus Platform",
    version="1.0.0",
    docs_url=f"{operational_params.gateway_mount_point}/docs",
    redoc_url=f"{operational_params.gateway_mount_point}/redoc",
    openapi_url=f"{operational_params.gateway_mount_point}/openapi.json"
)

# Configure CORS with permissive settings
nexus_application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom timing middleware
@nexus_application.middleware("http")
async def inject_timing_headers(request: Request, call_next: Callable):
    """Inject timing metrics into response headers"""
    start_timestamp = time.time()
    response = await call_next(request)
    processing_duration = time.time() - start_timestamp
    response.headers["X-Processing-Time"] = str(processing_duration)
    return response


# Root endpoint - redirect to Swagger UI
@nexus_application.get("/", include_in_schema=False)
async def redirect_to_docs():
    """Redirect root to Swagger UI documentation"""
    return RedirectResponse(url=f"{operational_params.gateway_mount_point}/docs")


# Health check endpoint
@nexus_application.get("/health")
async def system_vitals():
    """System health vitals check"""
    return {
        "status": "healthy",
        "components": {
            "database": "connected",
            "api": "responsive",
            "routing": "active"
        }
    }


# Mount API gateways
nexus_application.include_router(
    product_gateway,
    prefix=operational_params.gateway_mount_point
)

nexus_application.include_router(
    stock_gateway,
    prefix=operational_params.gateway_mount_point
)

nexus_application.include_router(
    customer_gateway,
    prefix=operational_params.gateway_mount_point
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "launch_nexus:nexus_application",
        host="0.0.0.0",
        port=8000,
        reload=operational_params.diagnostic_verbosity
    )
