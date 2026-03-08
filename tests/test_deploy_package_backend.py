"""
Unit tests for backend packaging functionality in deploy.py

Tests the package_backend() method of the Deployer class to ensure
it correctly installs dependencies, adds Mangum, and copies application code.

Requirements: 2.1, 2.2
"""

import pytest
import shutil
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to import deploy module
sys.path.insert(0, str(Path(__file__).parent.parent))

from deploy import Deployer


class TestPackageBackend:
    """Test suite for backend packaging functionality"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_deployment(self, temp_workspace):
        """Create a mock deployment structure for testing"""
        # Create deployment directory structure
        deployment_dir = temp_workspace / "deployment"
        deployment_dir.mkdir()
        
        # Create backend directory
        backend_dir = deployment_dir / "backend"
        backend_dir.mkdir()
        
        # Create app directory with some modules
        app_dir = backend_dir / "app"
        app_dir.mkdir()
        (app_dir / "__init__.py").write_text("")
        (app_dir / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")
        
        # Create a minimal requirements.txt
        requirements = backend_dir / "requirements.txt"
        requirements.write_text("fastapi\npydantic\n")
        
        return temp_workspace
    
    def test_package_backend_creates_package_directory(self, mock_deployment, monkeypatch):
        """Test that package directory is created"""
        monkeypatch.chdir(mock_deployment)
        
        deployer = Deployer()
        deployer.deployment_dir = mock_deployment / "deployment"
        
        # Execute packaging
        deployer.package_backend()
        
        # Verify package directory exists
        package_dir = deployer.deployment_dir / "backend_package"
        assert package_dir.exists()
        assert package_dir.is_dir()
    
    def test_package_backend_installs_dependencies(self, mock_deployment, monkeypatch):
        """Test that dependencies from requirements.txt are installed"""
        monkeypatch.chdir(mock_deployment)
        
        deployer = Deployer()
        deployer.deployment_dir = mock_deployment / "deployment"
        
        # Execute packaging
        deployer.package_backend()
        
        # Verify dependencies are installed (check for fastapi and pydantic)
        package_dir = deployer.deployment_dir / "backend_package"
        
        # Check for fastapi package
        fastapi_installed = any(
            p.name.startswith('fastapi') for p in package_dir.iterdir()
        )
        assert fastapi_installed, "fastapi should be installed in package"
        
        # Check for pydantic package
        pydantic_installed = any(
            p.name.startswith('pydantic') for p in package_dir.iterdir()
        )
        assert pydantic_installed, "pydantic should be installed in package"
    
    def test_package_backend_installs_mangum(self, mock_deployment, monkeypatch):
        """Test that Mangum adapter is installed"""
        monkeypatch.chdir(mock_deployment)
        
        deployer = Deployer()
        deployer.deployment_dir = mock_deployment / "deployment"
        
        # Execute packaging
        deployer.package_backend()
        
        # Verify Mangum is installed
        package_dir = deployer.deployment_dir / "backend_package"
        mangum_installed = any(
            p.name.startswith('mangum') for p in package_dir.iterdir()
        )
        assert mangum_installed, "mangum should be installed in package"
    
    def test_package_backend_copies_application_code(self, mock_deployment, monkeypatch):
        """Test that application code is copied to package"""
        monkeypatch.chdir(mock_deployment)
        
        deployer = Deployer()
        deployer.deployment_dir = mock_deployment / "deployment"
        
        # Execute packaging
        deployer.package_backend()
        
        # Verify app directory is copied
        package_dir = deployer.deployment_dir / "backend_package"
        app_dir = package_dir / "app"
        
        assert app_dir.exists(), "app directory should be copied"
        assert (app_dir / "__init__.py").exists(), "__init__.py should be copied"
        assert (app_dir / "main.py").exists(), "main.py should be copied"
    
    def test_package_backend_preserves_file_content(self, mock_deployment, monkeypatch):
        """Test that file contents are preserved during copying"""
        monkeypatch.chdir(mock_deployment)
        
        deployer = Deployer()
        deployer.deployment_dir = mock_deployment / "deployment"
        
        # Get original content
        original_content = (
            deployer.deployment_dir / "backend" / "app" / "main.py"
        ).read_text()
        
        # Execute packaging
        deployer.package_backend()
        
        # Verify content matches
        package_dir = deployer.deployment_dir / "backend_package"
        copied_content = (package_dir / "app" / "main.py").read_text()
        
        assert original_content == copied_content
    
    def test_package_backend_removes_existing_package(self, mock_deployment, monkeypatch):
        """Test that existing package directory is removed before packaging"""
        monkeypatch.chdir(mock_deployment)
        
        deployer = Deployer()
        deployer.deployment_dir = mock_deployment / "deployment"
        
        # Create existing package directory with a file
        package_dir = deployer.deployment_dir / "backend_package"
        package_dir.mkdir()
        (package_dir / "old_file.txt").write_text("old content")
        
        # Execute packaging
        deployer.package_backend()
        
        # Verify old file is gone
        assert not (package_dir / "old_file.txt").exists()
        
        # Verify new files are present
        assert (package_dir / "app").exists()
    
    def test_package_backend_raises_error_if_backend_missing(self, temp_workspace, monkeypatch):
        """Test that error is raised if backend directory doesn't exist"""
        monkeypatch.chdir(temp_workspace)
        
        deployer = Deployer()
        deployer.deployment_dir = temp_workspace / "deployment"
        deployer.deployment_dir.mkdir()
        
        # Execute packaging without backend directory
        with pytest.raises(FileNotFoundError, match="Backend directory not found"):
            deployer.package_backend()
    
    def test_package_backend_raises_error_if_requirements_missing(self, temp_workspace, monkeypatch):
        """Test that error is raised if requirements.txt doesn't exist"""
        monkeypatch.chdir(temp_workspace)
        
        deployer = Deployer()
        deployer.deployment_dir = temp_workspace / "deployment"
        deployer.deployment_dir.mkdir()
        
        # Create backend directory without requirements.txt
        backend_dir = deployer.deployment_dir / "backend"
        backend_dir.mkdir()
        
        # Execute packaging
        with pytest.raises(FileNotFoundError, match="Requirements file not found"):
            deployer.package_backend()
    
    def test_package_backend_excludes_pycache(self, mock_deployment, monkeypatch):
        """Test that __pycache__ directories are excluded from copying"""
        monkeypatch.chdir(mock_deployment)
        
        deployer = Deployer()
        deployer.deployment_dir = mock_deployment / "deployment"
        
        # Create __pycache__ in app directory
        app_dir = deployer.deployment_dir / "backend" / "app"
        pycache_dir = app_dir / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "main.cpython-311.pyc").write_text("compiled")
        
        # Execute packaging
        deployer.package_backend()
        
        # Verify __pycache__ was NOT copied
        package_dir = deployer.deployment_dir / "backend_package"
        assert not (package_dir / "app" / "__pycache__").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
