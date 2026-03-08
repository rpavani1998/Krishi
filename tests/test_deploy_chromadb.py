"""
Unit tests for ChromaDB upload functionality in deploy.py

Tests the deploy_chromadb() and upload_chromadb() methods of the Deployer class
to ensure ChromaDB files are correctly uploaded to S3 with preserved directory structure.

Requirements: 5.1, 5.2
"""

import pytest
import shutil
import tempfile
from pathlib import Path
import sys
from unittest.mock import Mock, patch, call
from botocore.exceptions import ClientError

# Add parent directory to path to import deploy module
sys.path.insert(0, str(Path(__file__).parent.parent))

from deploy import Deployer


class TestDeployChromaDB:
    """Test suite for ChromaDB upload functionality"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_chromadb(self, temp_workspace):
        """Create a mock ChromaDB directory structure"""
        chromadb_dir = temp_workspace / "chroma_db"
        chromadb_dir.mkdir()
        
        # Create chroma.sqlite3 file
        (chromadb_dir / "chroma.sqlite3").write_text("mock sqlite data")
        
        # Create subdirectory with files (mimicking real ChromaDB structure)
        uuid_dir = chromadb_dir / "99da9e58-c2f7-471b-a1be-3a5317c00d6d"
        uuid_dir.mkdir()
        
        (uuid_dir / "data_level0.bin").write_bytes(b"binary data")
        (uuid_dir / "header.bin").write_bytes(b"header data")
        (uuid_dir / "index_metadata.pickle").write_bytes(b"pickle data")
        (uuid_dir / "length.bin").write_bytes(b"length data")
        (uuid_dir / "link_lists.bin").write_bytes(b"link data")
        
        return chromadb_dir
    
    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client"""
        with patch('boto3.client') as mock_boto_client:
            mock_client = Mock()
            mock_boto_client.return_value = mock_client
            yield mock_client
    
    def test_deploy_chromadb_uploads_all_files(self, mock_chromadb, mock_s3_client):
        """Test that all ChromaDB files are uploaded to S3"""
        deployer = Deployer()
        
        # Execute upload
        deployer.deploy_chromadb(
            chromadb_path=str(mock_chromadb),
            s3_bucket="test-bucket",
            s3_prefix="chromadb/"
        )
        
        # Verify upload_file was called for each file
        assert mock_s3_client.upload_file.call_count == 6  # 1 sqlite + 5 bin files
    
    def test_deploy_chromadb_preserves_directory_structure(self, mock_chromadb, mock_s3_client):
        """Test that directory structure is preserved in S3 keys"""
        deployer = Deployer()
        
        # Execute upload
        deployer.deploy_chromadb(
            chromadb_path=str(mock_chromadb),
            s3_bucket="test-bucket",
            s3_prefix="chromadb/"
        )
        
        # Get all S3 keys that were uploaded
        uploaded_keys = [
            call_args[0][2]  # Third argument is the S3 key
            for call_args in mock_s3_client.upload_file.call_args_list
        ]
        
        # Verify keys preserve directory structure
        assert "chromadb/chroma.sqlite3" in uploaded_keys
        assert "chromadb/99da9e58-c2f7-471b-a1be-3a5317c00d6d/data_level0.bin" in uploaded_keys
        assert "chromadb/99da9e58-c2f7-471b-a1be-3a5317c00d6d/header.bin" in uploaded_keys
        assert "chromadb/99da9e58-c2f7-471b-a1be-3a5317c00d6d/index_metadata.pickle" in uploaded_keys
    
    def test_deploy_chromadb_uses_correct_bucket(self, mock_chromadb, mock_s3_client):
        """Test that files are uploaded to the correct S3 bucket"""
        deployer = Deployer()
        bucket_name = "my-chromadb-bucket"
        
        # Execute upload
        deployer.deploy_chromadb(
            chromadb_path=str(mock_chromadb),
            s3_bucket=bucket_name,
            s3_prefix="chromadb/"
        )
        
        # Verify all uploads use the correct bucket
        for call_args in mock_s3_client.upload_file.call_args_list:
            assert call_args[0][1] == bucket_name  # Second argument is bucket name
    
    def test_deploy_chromadb_uses_custom_prefix(self, mock_chromadb, mock_s3_client):
        """Test that custom S3 prefix is applied correctly"""
        deployer = Deployer()
        custom_prefix = "vector-db/production/"
        
        # Execute upload
        deployer.deploy_chromadb(
            chromadb_path=str(mock_chromadb),
            s3_bucket="test-bucket",
            s3_prefix=custom_prefix
        )
        
        # Verify all keys start with custom prefix
        uploaded_keys = [
            call_args[0][2]
            for call_args in mock_s3_client.upload_file.call_args_list
        ]
        
        for key in uploaded_keys:
            assert key.startswith(custom_prefix)
    
    def test_deploy_chromadb_raises_error_if_directory_not_found(self, temp_workspace, mock_s3_client):
        """Test that error is raised if ChromaDB directory doesn't exist"""
        deployer = Deployer()
        non_existent_path = temp_workspace / "non_existent_chroma_db"
        
        # Execute upload
        with pytest.raises(FileNotFoundError, match="ChromaDB directory not found"):
            deployer.deploy_chromadb(
                chromadb_path=str(non_existent_path),
                s3_bucket="test-bucket",
                s3_prefix="chromadb/"
            )
    
    def test_deploy_chromadb_raises_error_if_path_is_file(self, temp_workspace, mock_s3_client):
        """Test that error is raised if ChromaDB path is a file, not a directory"""
        deployer = Deployer()
        file_path = temp_workspace / "not_a_directory.txt"
        file_path.write_text("content")
        
        # Execute upload
        with pytest.raises(ValueError, match="ChromaDB path is not a directory"):
            deployer.deploy_chromadb(
                chromadb_path=str(file_path),
                s3_bucket="test-bucket",
                s3_prefix="chromadb/"
            )
    
    def test_deploy_chromadb_handles_empty_directory(self, temp_workspace, mock_s3_client):
        """Test that empty ChromaDB directory is handled gracefully"""
        deployer = Deployer()
        empty_dir = temp_workspace / "empty_chroma_db"
        empty_dir.mkdir()
        
        # Execute upload (should not raise error, just log warning)
        deployer.deploy_chromadb(
            chromadb_path=str(empty_dir),
            s3_bucket="test-bucket",
            s3_prefix="chromadb/"
        )
        
        # Verify no uploads were attempted
        assert mock_s3_client.upload_file.call_count == 0
    
    def test_deploy_chromadb_handles_s3_access_denied(self, mock_chromadb):
        """Test that S3 access denied error is handled properly"""
        with patch('boto3.client') as mock_boto_client:
            mock_client = Mock()
            mock_boto_client.return_value = mock_client
            
            # Simulate AccessDenied error
            error_response = {
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'Access Denied'
                }
            }
            mock_client.upload_file.side_effect = ClientError(error_response, 'PutObject')
            
            deployer = Deployer()
            
            # Execute upload and expect error
            with pytest.raises(ClientError):
                deployer.deploy_chromadb(
                    chromadb_path=str(mock_chromadb),
                    s3_bucket="test-bucket",
                    s3_prefix="chromadb/"
                )
    
    def test_deploy_chromadb_handles_no_such_bucket(self, mock_chromadb):
        """Test that NoSuchBucket error is handled properly"""
        with patch('boto3.client') as mock_boto_client:
            mock_client = Mock()
            mock_boto_client.return_value = mock_client
            
            # Simulate NoSuchBucket error
            error_response = {
                'Error': {
                    'Code': 'NoSuchBucket',
                    'Message': 'The specified bucket does not exist'
                }
            }
            mock_client.upload_file.side_effect = ClientError(error_response, 'PutObject')
            
            deployer = Deployer()
            
            # Execute upload and expect error
            with pytest.raises(ClientError):
                deployer.deploy_chromadb(
                    chromadb_path=str(mock_chromadb),
                    s3_bucket="non-existent-bucket",
                    s3_prefix="chromadb/"
                )
    
    def test_upload_chromadb_calls_deploy_chromadb(self, temp_workspace, mock_s3_client):
        """Test that upload_chromadb() correctly calls deploy_chromadb()"""
        # Create deployment structure
        deployment_dir = temp_workspace / "deployment"
        deployment_dir.mkdir()
        backend_dir = deployment_dir / "backend"
        backend_dir.mkdir()
        chromadb_dir = backend_dir / "chroma_db"
        chromadb_dir.mkdir()
        
        # Create a test file
        (chromadb_dir / "test.db").write_text("test data")
        
        deployer = Deployer()
        deployer.deployment_dir = deployment_dir
        
        # Execute upload
        deployer.upload_chromadb("test-bucket")
        
        # Verify upload was called
        assert mock_s3_client.upload_file.call_count == 1
        
        # Verify correct S3 key
        uploaded_key = mock_s3_client.upload_file.call_args[0][2]
        assert uploaded_key == "chromadb/test.db"
    
    def test_deploy_chromadb_handles_nested_directories(self, temp_workspace, mock_s3_client):
        """Test that deeply nested directory structures are handled correctly"""
        chromadb_dir = temp_workspace / "chroma_db"
        chromadb_dir.mkdir()
        
        # Create nested structure
        nested_dir = chromadb_dir / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)
        (nested_dir / "deep_file.bin").write_bytes(b"deep data")
        
        deployer = Deployer()
        
        # Execute upload
        deployer.deploy_chromadb(
            chromadb_path=str(chromadb_dir),
            s3_bucket="test-bucket",
            s3_prefix="chromadb/"
        )
        
        # Verify nested structure is preserved in S3 key
        uploaded_key = mock_s3_client.upload_file.call_args[0][2]
        assert uploaded_key == "chromadb/level1/level2/level3/deep_file.bin"
    
    def test_deploy_chromadb_handles_special_characters_in_filenames(self, temp_workspace, mock_s3_client):
        """Test that files with special characters are handled correctly"""
        chromadb_dir = temp_workspace / "chroma_db"
        chromadb_dir.mkdir()
        
        # Create files with special characters (that are valid in both filesystems and S3)
        (chromadb_dir / "file-with-dashes.bin").write_bytes(b"data")
        (chromadb_dir / "file_with_underscores.bin").write_bytes(b"data")
        (chromadb_dir / "file.with.dots.bin").write_bytes(b"data")
        
        deployer = Deployer()
        
        # Execute upload
        deployer.deploy_chromadb(
            chromadb_path=str(chromadb_dir),
            s3_bucket="test-bucket",
            s3_prefix="chromadb/"
        )
        
        # Verify all files were uploaded
        assert mock_s3_client.upload_file.call_count == 3
        
        # Verify keys are correct
        uploaded_keys = [
            call_args[0][2]
            for call_args in mock_s3_client.upload_file.call_args_list
        ]
        
        assert "chromadb/file-with-dashes.bin" in uploaded_keys
        assert "chromadb/file_with_underscores.bin" in uploaded_keys
        assert "chromadb/file.with.dots.bin" in uploaded_keys


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
