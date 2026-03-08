"""
Unit tests for configuration setup from .env.example

Tests the setup_configuration_from_env_example() helper function.

Requirements: 4.1, 4.2
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import sys
import tempfile

# Add parent directory to path to import deploy module
sys.path.insert(0, str(Path(__file__).parent.parent))

from deploy import Deployer


class TestConfigurationFromEnv:
    """Test suite for configuration setup from .env.example"""
    
    @pytest.fixture
    def deployer(self):
        """Create a Deployer instance for testing"""
        return Deployer(environment="test", region="us-east-1")
    
    @pytest.fixture
    def sample_env_content(self):
        """Sample .env.example content"""
        return """# Application
APP_NAME="Krishi Backend"
DEBUG=False

# Weather Service
OPEN_METEO_URL="https://api.open-meteo.com/v1/forecast"

# Price Service
CEDA_API_KEY=""

# News Service
NEWS_API_URL="https://api.apitube.io/v1/news/everything"
NEWS_API_KEY=""
NEWS_API_ENABLED=True

# AI Service
USE_AWS_AI=False
OLLAMA_BASE_URL="http://localhost:11434/api/generate"
OLLAMA_MODEL="qwen2.5:1.5b"
"""
    
    @patch('deploy.Deployer.setup_configuration')
    def test_setup_configuration_from_env_example_parses_file(
        self, mock_setup_config, deployer, sample_env_content
    ):
        """Test that .env.example file is parsed correctly"""
        # Create temporary .env.example file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as f:
            f.write(sample_env_content)
            temp_path = f.name
        
        try:
            mock_setup_config.return_value = {'parameters': {}, 'secrets': {}}
            
            # Execute
            result = deployer.setup_configuration_from_env_example(env_example_path=temp_path)
            
            # Verify setup_configuration was called
            assert mock_setup_config.call_count == 1
            
            # Get the arguments passed to setup_configuration
            call_args = mock_setup_config.call_args
            config_values = call_args[0][0]
            secret_values = call_args[0][1]
            
            # Verify non-sensitive values are in config_values
            assert 'app_name' in config_values
            assert 'debug' in config_values
            assert 'open_meteo_url' in config_values
            assert 'use_aws_ai' in config_values
            
            # Verify sensitive values are in secret_values
            assert 'ceda_api_key' in secret_values
            assert 'news_api_key' in secret_values
            
        finally:
            # Cleanup
            Path(temp_path).unlink()
    
    @patch('deploy.Deployer.setup_configuration')
    def test_setup_configuration_from_env_example_categorizes_correctly(
        self, mock_setup_config, deployer, sample_env_content
    ):
        """Test that sensitive and non-sensitive values are categorized correctly"""
        # Create temporary .env.example file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as f:
            f.write(sample_env_content)
            temp_path = f.name
        
        try:
            mock_setup_config.return_value = {'parameters': {}, 'secrets': {}}
            
            # Execute
            result = deployer.setup_configuration_from_env_example(env_example_path=temp_path)
            
            # Get the arguments
            call_args = mock_setup_config.call_args
            config_values = call_args[0][0]
            secret_values = call_args[0][1]
            
            # Verify categorization
            # API keys should be secrets
            assert 'ceda_api_key' in secret_values
            assert 'news_api_key' in secret_values
            
            # URLs and flags should be parameters
            assert 'open_meteo_url' in config_values
            assert 'news_api_url' in config_values
            assert 'ollama_base_url' in config_values
            
        finally:
            Path(temp_path).unlink()
    
    @patch('deploy.Deployer.setup_configuration')
    def test_setup_configuration_from_env_example_applies_overrides(
        self, mock_setup_config, deployer, sample_env_content
    ):
        """Test that override values are applied correctly"""
        # Create temporary .env.example file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as f:
            f.write(sample_env_content)
            temp_path = f.name
        
        try:
            mock_setup_config.return_value = {'parameters': {}, 'secrets': {}}
            
            # Override values
            overrides = {
                'CEDA_API_KEY': 'my-actual-ceda-key',
                'NEWS_API_KEY': 'my-actual-news-key',
                'DEBUG': 'True'
            }
            
            # Execute
            result = deployer.setup_configuration_from_env_example(
                env_example_path=temp_path,
                override_values=overrides
            )
            
            # Get the arguments
            call_args = mock_setup_config.call_args
            config_values = call_args[0][0]
            secret_values = call_args[0][1]
            
            # Verify overrides were applied
            assert secret_values['ceda_api_key'] == 'my-actual-ceda-key'
            assert secret_values['news_api_key'] == 'my-actual-news-key'
            assert config_values['debug'] == 'True'
            
        finally:
            Path(temp_path).unlink()
    
    @patch('deploy.Deployer.setup_configuration')
    def test_setup_configuration_from_env_example_skips_comments(
        self, mock_setup_config, deployer
    ):
        """Test that comments and empty lines are skipped"""
        content = """# This is a comment
APP_NAME="Krishi"

# Another comment
DEBUG=False
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            mock_setup_config.return_value = {'parameters': {}, 'secrets': {}}
            
            # Execute
            result = deployer.setup_configuration_from_env_example(env_example_path=temp_path)
            
            # Get the arguments
            call_args = mock_setup_config.call_args
            config_values = call_args[0][0]
            secret_values = call_args[0][1]
            
            # Verify only actual values are present
            total_values = len(config_values) + len(secret_values)
            assert total_values == 2  # Only APP_NAME and DEBUG
            
        finally:
            Path(temp_path).unlink()
    
    def test_setup_configuration_from_env_example_raises_on_missing_file(self, deployer):
        """Test that FileNotFoundError is raised if .env.example doesn't exist"""
        with pytest.raises(FileNotFoundError):
            deployer.setup_configuration_from_env_example(
                env_example_path="/nonexistent/path/.env.example"
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
