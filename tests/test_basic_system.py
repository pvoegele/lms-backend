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


@patch('warehouse_nexus.cerebrum.psql_conductor.psql_conductor')
def test_api_heartbeat(mock_engine):
    """Test API heartbeat endpoint"""
    from launch_nexus import nexus_application
    
    client = TestClient(nexus_application)
    response = client.get("/")
    
    assert response.status_code == 200
    assert "platform" in response.json()
    assert response.json()["status"] == "operational"


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
