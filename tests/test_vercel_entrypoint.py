"""
Test the Vercel deployment entrypoint
"""
import pytest


def test_api_index_imports():
    """Test that api/index.py can be imported"""
    from api.index import app
    assert app is not None


def test_api_index_app_is_fastapi():
    """Test that api/index.py exports a FastAPI instance"""
    from api.index import app
    from fastapi import FastAPI
    assert isinstance(app, FastAPI)


def test_api_index_app_has_expected_attributes():
    """Test that the app has expected attributes from launch_nexus"""
    from api.index import app
    assert app.title == "WarehouseNexus"
    assert app.version == "1.0.0"
    assert app.docs_url == "/api/v1/docs"
    assert app.openapi_url == "/api/v1/openapi.json"


def test_api_index_app_same_as_launch_nexus():
    """Test that api/index.py exports the same app as launch_nexus"""
    from api.index import app
    from launch_nexus import nexus_application
    assert app is nexus_application
