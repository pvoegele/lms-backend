"""
Basic system tests for Warehouse Nexus
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


def test_import_main_application():
    """Test that main application can be imported"""
    from launch_nexus import nexus_application
    assert nexus_application is not None
    assert nexus_application.title == "WarehouseNexus"


def test_import_core_entities():
    """Test that core entities can be imported"""
    from warehouse_nexus.schema_registry.core_entities import Product, UnitOfMeasure
    assert Product is not None
    assert UnitOfMeasure is not None


def test_import_business_logic():
    """Test that business conductors can be imported"""
    from warehouse_nexus.business_conductors.posting_conductor import PostingConductor
    assert PostingConductor is not None


def test_configuration_singleton():
    """Test configuration singleton pattern"""
    from warehouse_nexus.cerebrum.configuration_nucleus import extract_runtime_config
    
    config1 = extract_runtime_config()
    config2 = extract_runtime_config()
    
    assert config1 is config2  # Should be same instance


def test_api_heartbeat():
    """Test API root redirect to docs"""
    from launch_nexus import nexus_application
    import asyncio
    
    # Find the root route
    root_route = None
    for route in nexus_application.routes:
        if hasattr(route, 'path') and route.path == '/':
            root_route = route
            break
    
    assert root_route is not None, "Root route not found"
    assert root_route.endpoint.__name__ == "redirect_to_docs"
    
    # Test the endpoint directly
    response = asyncio.run(root_route.endpoint())
    assert response.status_code == 307
    assert response.headers.get("location") == "/api/v1/docs"


@patch('warehouse_nexus.cerebrum.psql_conductor.psql_conductor')
def test_health_endpoint(mock_engine):
    """Test health check endpoint"""
    from launch_nexus import nexus_application
    
    client = TestClient(nexus_application)
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_enum_imports():
    """Test that all enums can be imported"""
    from warehouse_nexus.schema_registry.categorical_taxonomy import (
        StockDocumentCategory,
        DocumentStateCode,
        SalesOrderStateCode,
        PurchaseOrderStateCode,
        ReservationStateCode,
        SerialStateCode,
        LocationCategory,
        PartnerTypeCode
    )
    
    assert len(StockDocumentCategory) == 6
    assert len(DocumentStateCode) == 3
    assert len(LocationCategory) == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
