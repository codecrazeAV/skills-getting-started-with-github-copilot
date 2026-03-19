"""Pytest configuration and shared fixtures"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Provide a TestClient instance for testing the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def fresh_app():
    """Create a fresh app instance with clean in-memory state
    
    This prevents test pollution by ensuring each test gets a fresh
    copy of the activities database
    """
    # Re-import app to get fresh instance with default activities
    import importlib
    import app as app_module
    importlib.reload(app_module)
    return TestClient(app_module.app)
