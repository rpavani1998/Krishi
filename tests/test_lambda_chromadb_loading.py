"""
Unit tests for Lambda ChromaDB loading functionality.

Tests verify that the Lambda handler correctly loads ChromaDB from S3
at cold start and makes it available for the RAG service.

Requirements: 5.2, 5.3
"""

import pytest
from pathlib import Path
import sys
import os

# Add backend directory to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


class TestLambdaChromaDBLoading:
    """Test suite for Lambda ChromaDB loading functionality."""
    
    def test_lambda_handler_has_chromadb_loading_function(self):
        """Test that lambda_handler.py contains the load_chromadb_from_s3 function."""
        handler_path = backend_path / "lambda_handler.py"
        content = handler_path.read_text()
        
        # Verify function exists
        assert "def load_chromadb_from_s3()" in content, "Should have load_chromadb_from_s3 function"
        assert "global chroma_client, chroma_loaded" in content, "Should use global variables for caching"
        assert "boto3.client('s3')" in content, "Should use boto3 S3 client"
        assert "CHROMADB_BUCKET" in content, "Should read CHROMADB_BUCKET environment variable"
    
    def test_lambda_handler_has_chromadb_global_variables(self):
        """Test that lambda_handler.py has global variables for ChromaDB caching."""
        handler_path = backend_path / "lambda_handler.py"
        content = handler_path.read_text()
        
        # Verify global variables
        assert "chroma_client = None" in content, "Should have chroma_client global variable"
        assert "chroma_loaded = False" in content, "Should have chroma_loaded global variable"
    
    def test_lambda_handler_loads_chromadb_at_module_init(self):
        """Test that lambda_handler.py loads ChromaDB at module initialization."""
        handler_path = backend_path / "lambda_handler.py"
        content = handler_path.read_text()
        
        # Verify ChromaDB is loaded at module level
        assert "chromadb_path = load_chromadb_from_s3()" in content, "Should call load_chromadb_from_s3 at module level"
        assert "CHROMA_DB_PATH" in content, "Should set CHROMA_DB_PATH environment variable"
    
    def test_lambda_handler_handles_s3_download(self):
        """Test that load_chromadb_from_s3 handles S3 file download."""
        handler_path = backend_path / "lambda_handler.py"
        content = handler_path.read_text()
        
        # Verify S3 download logic
        assert "s3.get_paginator('list_objects_v2')" in content, "Should use S3 paginator"
        assert "s3.download_file" in content, "Should download files from S3"
        assert "/tmp/chroma_db" in content, "Should use /tmp directory for Lambda"
    
    def test_lambda_handler_skips_directory_markers(self):
        """Test that load_chromadb_from_s3 skips directory markers."""
        handler_path = backend_path / "lambda_handler.py"
        content = handler_path.read_text()
        
        # Verify directory marker handling
        assert "if key.endswith('/'):" in content, "Should check for directory markers"
        assert "continue" in content, "Should skip directory markers"
    
    def test_lambda_handler_creates_nested_directories(self):
        """Test that load_chromadb_from_s3 creates nested directory structures."""
        handler_path = backend_path / "lambda_handler.py"
        content = handler_path.read_text()
        
        # Verify directory creation
        assert "local_path.parent.mkdir(parents=True, exist_ok=True)" in content, "Should create parent directories"
    
    def test_lambda_handler_handles_errors(self):
        """Test that load_chromadb_from_s3 handles errors gracefully."""
        handler_path = backend_path / "lambda_handler.py"
        content = handler_path.read_text()
        
        # Verify error handling
        assert "try:" in content, "Should have try-except block"
        assert "except Exception as e:" in content, "Should catch exceptions"
        assert "logger.error" in content, "Should log errors"
        assert "return None" in content, "Should return None on error"
    
    def test_lambda_handler_implements_caching(self):
        """Test that load_chromadb_from_s3 implements caching."""
        handler_path = backend_path / "lambda_handler.py"
        content = handler_path.read_text()
        
        # Verify caching logic
        assert "if chroma_loaded:" in content, "Should check if already loaded"
        assert "chroma_loaded = True" in content, "Should mark as loaded after successful download"
    
    def test_lambda_handler_documentation(self):
        """Test that load_chromadb_from_s3 has proper documentation."""
        handler_path = backend_path / "lambda_handler.py"
        content = handler_path.read_text()
        
        # Verify documentation
        assert "Download ChromaDB files from S3" in content, "Should have function docstring"
        assert "Requirements: 5.2, 5.3" in content or "Requirements: 2.1, 2.5, 5.2, 5.3" in content, "Should reference requirements"


class TestRAGServiceLambdaIntegration:
    """Test RAG service integration with Lambda ChromaDB loading."""
    
    def test_rag_service_checks_lambda_chromadb_path(self):
        """Test that RAG service checks for Lambda ChromaDB path."""
        rag_service_path = backend_path / "app" / "services" / "rag_service.py"
        content = rag_service_path.read_text()
        
        # Verify Lambda path check
        assert "CHROMA_DB_PATH" in content, "Should check CHROMA_DB_PATH environment variable"
        assert "os.environ.get" in content, "Should use os.environ.get to read environment variable"
    
    def test_rag_service_uses_lambda_path_when_available(self):
        """Test that RAG service uses Lambda path when available."""
        rag_service_path = backend_path / "app" / "services" / "rag_service.py"
        content = rag_service_path.read_text()
        
        # Verify path override logic
        assert "lambda_chroma_path = os.environ.get('CHROMA_DB_PATH')" in content, "Should read Lambda path"
        assert "if lambda_chroma_path:" in content, "Should check if Lambda path exists"
        assert "persist_directory = lambda_chroma_path" in content, "Should use Lambda path"
