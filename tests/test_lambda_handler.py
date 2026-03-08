"""
Unit tests for Lambda handler wrapper.

Tests verify that the Lambda handler is correctly structured and
can be imported and invoked as expected by AWS Lambda.

Requirements: 2.1, 2.5
"""

import pytest
from pathlib import Path
import sys

# Add backend directory to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


def test_lambda_handler_exists():
    """Test that lambda_handler.py exists in backend directory."""
    handler_path = backend_path / "lambda_handler.py"
    assert handler_path.exists(), "lambda_handler.py should exist in backend directory"


def test_lambda_handler_imports():
    """Test that lambda_handler module can be imported."""
    try:
        import lambda_handler
        assert hasattr(lambda_handler, 'handler'), "lambda_handler module should have 'handler' attribute"
    except ImportError as e:
        # If mangum is not installed, this is expected in local dev environment
        if "mangum" in str(e):
            pytest.skip("Mangum not installed - expected in local dev environment")
        else:
            raise


def test_lambda_handler_is_callable():
    """Test that the handler is callable (required by Lambda)."""
    try:
        import lambda_handler
        assert callable(lambda_handler.handler), "handler should be callable"
    except ImportError as e:
        if "mangum" in str(e):
            pytest.skip("Mangum not installed - expected in local dev environment")
        else:
            raise


def test_lambda_handler_structure():
    """Test that lambda_handler.py has the correct structure."""
    handler_path = backend_path / "lambda_handler.py"
    content = handler_path.read_text()
    
    # Verify key components are present
    assert "from mangum import Mangum" in content, "Should import Mangum"
    assert "from app.main import app" in content, "Should import FastAPI app"
    assert "handler = Mangum" in content, "Should create handler with Mangum"
    assert 'lifespan="off"' in content, "Should set lifespan='off' for Lambda compatibility"


def test_lambda_handler_documentation():
    """Test that lambda_handler.py has proper documentation."""
    handler_path = backend_path / "lambda_handler.py"
    content = handler_path.read_text()
    
    # Verify documentation is present
    assert '"""' in content, "Should have docstring"
    assert "Requirements:" in content, "Should reference requirements"
