"""
Unit tests for repository cloning functionality in deploy.py

Tests the clone_repository() method of the Deployer class to ensure
it correctly clones the repository while excluding specified patterns
and preserving git history.

Requirements: 1.1, 1.2, 1.5
"""

import pytest
import shutil
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to import deploy module
sys.path.insert(0, str(Path(__file__).parent.parent))

from deploy import Deployer


class TestCloneRepository:
    """Test suite for repository cloning functionality"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_repo(self, temp_workspace):
        """Create a mock repository structure for testing"""
        # Create basic structure
        (temp_workspace / "backend").mkdir()
        (temp_workspace / "frontend").mkdir()
        (temp_workspace / ".git").mkdir()
        
        # Create some files
        (temp_workspace / "backend" / "main.py").write_text("# Backend code")
        (temp_workspace / "frontend" / "index.html").write_text("<html></html>")
        (temp_workspace / ".git" / "config").write_text("[core]")
        (temp_workspace / "README.md").write_text("# Test Repo")
        
        # Create exclusion directories
        (temp_workspace / "node_modules").mkdir()
        (temp_workspace / "node_modules" / "package.json").write_text("{}")
        (temp_workspace / "venv").mkdir()
        (temp_workspace / "venv" / "lib").mkdir()
        (temp_workspace / "__pycache__").mkdir()
        (temp_workspace / "__pycache__" / "test.pyc").write_text("compiled")
        
        return temp_workspace
    
    def test_clone_repository_basic(self, mock_repo, monkeypatch):
        """Test basic repository cloning functionality"""
        # Change to mock repo directory
        monkeypatch.chdir(mock_repo)
        
        # Create deployer
        deployer = Deployer()
        
        # Execute clone
        deployer.clone_repository()
        
        # Verify deployment directory exists
        assert deployer.deployment_dir.exists()
        
        # Verify key files were copied
        assert (deployer.deployment_dir / "backend" / "main.py").exists()
        assert (deployer.deployment_dir / "frontend" / "index.html").exists()
        assert (deployer.deployment_dir / "README.md").exists()
    
    def test_clone_repository_excludes_node_modules(self, mock_repo, monkeypatch):
        """Test that node_modules is excluded from cloning"""
        monkeypatch.chdir(mock_repo)
        
        deployer = Deployer()
        deployer.clone_repository()
        
        # Verify node_modules was NOT copied
        assert not (deployer.deployment_dir / "node_modules").exists()
    
    def test_clone_repository_excludes_venv(self, mock_repo, monkeypatch):
        """Test that venv is excluded from cloning"""
        monkeypatch.chdir(mock_repo)
        
        deployer = Deployer()
        deployer.clone_repository()
        
        # Verify venv was NOT copied
        assert not (deployer.deployment_dir / "venv").exists()
    
    def test_clone_repository_excludes_pycache(self, mock_repo, monkeypatch):
        """Test that __pycache__ is excluded from cloning"""
        monkeypatch.chdir(mock_repo)
        
        deployer = Deployer()
        deployer.clone_repository()
        
        # Verify __pycache__ was NOT copied
        assert not (deployer.deployment_dir / "__pycache__").exists()
    
    def test_clone_repository_preserves_git_history(self, mock_repo, monkeypatch):
        """Test that .git directory is preserved"""
        monkeypatch.chdir(mock_repo)
        
        deployer = Deployer()
        deployer.clone_repository()
        
        # Verify .git directory was copied
        assert (deployer.deployment_dir / ".git").exists()
        assert (deployer.deployment_dir / ".git" / "config").exists()
    
    def test_clone_repository_removes_existing_deployment(self, mock_repo, monkeypatch):
        """Test that existing deployment directory is removed before cloning"""
        monkeypatch.chdir(mock_repo)
        
        deployer = Deployer()
        
        # Create existing deployment directory with a file
        deployer.deployment_dir.mkdir()
        (deployer.deployment_dir / "old_file.txt").write_text("old content")
        
        # Execute clone
        deployer.clone_repository()
        
        # Verify old file is gone
        assert not (deployer.deployment_dir / "old_file.txt").exists()
        
        # Verify new files are present
        assert (deployer.deployment_dir / "README.md").exists()
    
    def test_clone_repository_file_content_matches(self, mock_repo, monkeypatch):
        """Test that file contents are preserved during cloning"""
        monkeypatch.chdir(mock_repo)
        
        deployer = Deployer()
        deployer.clone_repository()
        
        # Verify file contents match
        original_content = (mock_repo / "backend" / "main.py").read_text()
        cloned_content = (deployer.deployment_dir / "backend" / "main.py").read_text()
        assert original_content == cloned_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
