"""
Unit tests for configuration management in deploy.py

Tests the setup_configuration() function that stores configuration
in Parameter Store and secrets in Secrets Manager.

Requirements: 4.1, 4.2
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path to import deploy module
sys.path.insert(0, str(Path(__file__).parent.parent))

from deploy import Deployer


class TestConfigurationSetup:
    """Test suite for configuration setup functionality"""
    
    @pytest.fixture
    def deployer(self):
        """Create a Deployer instance for testing"""
        return Deployer(environment="test", region="us-east-1")
    
    @pytest.fixture
    def mock_ssm_client(self):
        """Mock SSM client"""
        return Mock()
    
    @pytest.fixture
    def mock_secrets_client(self):
        """Mock Secrets Manager client"""
        return Mock()
    
    @patch('boto3.client')
    def test_setup_configuration_stores_parameters(
        self, mock_boto_client, deployer, mock_ssm_client, mock_secrets_client
    ):
        """Test that non-sensitive configuration is stored in Parameter Store"""
        # Setup mocks
        def get_client(service, **kwargs):
            if service == 'ssm':
                return mock_ssm_client
            elif service == 'secretsmanager':
                return mock_secrets_client
            return Mock()
        
        mock_boto_client.side_effect = get_client
        mock_ssm_client.put_parameter.return_value = {'Version': 1}
        
        # Test data
        config_values = {
            'app_name': 'Krishi Backend',
            'debug': 'false',
            'open_meteo_url': 'https://api.open-meteo.com/v1/forecast'
        }
        secret_values = {}
        
        # Execute
        result = deployer.setup_configuration(config_values, secret_values)
        
        # Verify SSM put_parameter was called for each config value
        assert mock_ssm_client.put_parameter.call_count == len(config_values)
        
        # Verify parameter names follow the correct pattern
        for key in config_values.keys():
            expected_name = f"/krishi/test/{key}"
            assert key in result['parameters']
            assert result['parameters'][key] == expected_name
        
        # Verify put_parameter was called with correct arguments
        calls = mock_ssm_client.put_parameter.call_args_list
        for call in calls:
            args, kwargs = call
            assert kwargs['Name'].startswith('/krishi/test/')
            assert kwargs['Type'] == 'String'
            assert kwargs['Overwrite'] is True
    
    @patch('boto3.client')
    def test_setup_configuration_stores_secrets(
        self, mock_boto_client, deployer, mock_ssm_client, mock_secrets_client
    ):
        """Test that sensitive credentials are stored in Secrets Manager"""
        # Setup mocks
        def get_client(service, **kwargs):
            if service == 'ssm':
                return mock_ssm_client
            elif service == 'secretsmanager':
                return mock_secrets_client
            return Mock()
        
        mock_boto_client.side_effect = get_client
        mock_secrets_client.create_secret.return_value = {
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret'
        }
        
        # Test data
        config_values = {}
        secret_values = {
            'ceda_api_key': 'test-ceda-key-12345',
            'news_api_key': 'test-news-key-67890'
        }
        
        # Execute
        result = deployer.setup_configuration(config_values, secret_values)
        
        # Verify create_secret was called for each secret
        assert mock_secrets_client.create_secret.call_count == len(secret_values)
        
        # Verify secret names follow the correct pattern
        for key in secret_values.keys():
            assert key in result['secrets']
            assert 'arn:aws:secretsmanager' in result['secrets'][key]
        
        # Verify create_secret was called with correct arguments
        calls = mock_secrets_client.create_secret.call_args_list
        for call in calls:
            args, kwargs = call
            assert kwargs['Name'].startswith('/krishi/test/')
            assert 'SecretString' in kwargs
    
    @patch('boto3.client')
    def test_setup_configuration_updates_existing_secrets(
        self, mock_boto_client, deployer, mock_ssm_client, mock_secrets_client
    ):
        """Test that existing secrets are updated instead of creating duplicates"""
        # Setup mocks
        def get_client(service, **kwargs):
            if service == 'ssm':
                return mock_ssm_client
            elif service == 'secretsmanager':
                return mock_secrets_client
            return Mock()
        
        mock_boto_client.side_effect = get_client
        
        # Simulate secret already exists
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'ResourceExistsException',
                'Message': 'Secret already exists'
            }
        }
        mock_secrets_client.create_secret.side_effect = ClientError(
            error_response, 'CreateSecret'
        )
        mock_secrets_client.update_secret.return_value = {
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret'
        }
        mock_secrets_client.describe_secret.return_value = {
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret'
        }
        
        # Test data
        config_values = {}
        secret_values = {
            'ceda_api_key': 'updated-ceda-key'
        }
        
        # Execute
        result = deployer.setup_configuration(config_values, secret_values)
        
        # Verify update_secret was called
        assert mock_secrets_client.update_secret.call_count == 1
        assert mock_secrets_client.describe_secret.call_count == 1
        
        # Verify result contains the ARN
        assert 'ceda_api_key' in result['secrets']
        assert 'arn:aws:secretsmanager' in result['secrets']['ceda_api_key']
    
    @patch('boto3.client')
    def test_setup_configuration_handles_both_parameters_and_secrets(
        self, mock_boto_client, deployer, mock_ssm_client, mock_secrets_client
    ):
        """Test that both parameters and secrets can be stored in one call"""
        # Setup mocks
        def get_client(service, **kwargs):
            if service == 'ssm':
                return mock_ssm_client
            elif service == 'secretsmanager':
                return mock_secrets_client
            return Mock()
        
        mock_boto_client.side_effect = get_client
        mock_ssm_client.put_parameter.return_value = {'Version': 1}
        mock_secrets_client.create_secret.return_value = {
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret'
        }
        
        # Test data
        config_values = {
            'app_name': 'Krishi Backend',
            'debug': 'false'
        }
        secret_values = {
            'ceda_api_key': 'test-key'
        }
        
        # Execute
        result = deployer.setup_configuration(config_values, secret_values)
        
        # Verify both parameters and secrets were stored
        assert len(result['parameters']) == 2
        assert len(result['secrets']) == 1
        assert mock_ssm_client.put_parameter.call_count == 2
        assert mock_secrets_client.create_secret.call_count == 1
    
    @patch('boto3.client')
    def test_setup_configuration_handles_empty_values(
        self, mock_boto_client, deployer, mock_ssm_client, mock_secrets_client
    ):
        """Test that empty config and secret dictionaries are handled gracefully"""
        # Setup mocks
        def get_client(service, **kwargs):
            if service == 'ssm':
                return mock_ssm_client
            elif service == 'secretsmanager':
                return mock_secrets_client
            return Mock()
        
        mock_boto_client.side_effect = get_client
        
        # Test data
        config_values = {}
        secret_values = {}
        
        # Execute
        result = deployer.setup_configuration(config_values, secret_values)
        
        # Verify no calls were made
        assert mock_ssm_client.put_parameter.call_count == 0
        assert mock_secrets_client.create_secret.call_count == 0
        
        # Verify result structure is correct
        assert 'parameters' in result
        assert 'secrets' in result
        assert len(result['parameters']) == 0
        assert len(result['secrets']) == 0
    
    @patch('boto3.client')
    def test_setup_configuration_uses_correct_environment_path(
        self, mock_boto_client, deployer, mock_ssm_client, mock_secrets_client
    ):
        """Test that configuration uses the correct environment in the path"""
        # Setup mocks
        def get_client(service, **kwargs):
            if service == 'ssm':
                return mock_ssm_client
            elif service == 'secretsmanager':
                return mock_secrets_client
            return Mock()
        
        mock_boto_client.side_effect = get_client
        mock_ssm_client.put_parameter.return_value = {'Version': 1}
        mock_secrets_client.create_secret.return_value = {
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret'
        }
        
        # Create deployer with specific environment
        deployer_prod = Deployer(environment="production", region="us-east-1")
        
        # Test data
        config_values = {'app_name': 'Krishi'}
        secret_values = {'api_key': 'secret'}
        
        # Execute
        result = deployer_prod.setup_configuration(config_values, secret_values)
        
        # Verify paths include the correct environment
        param_call = mock_ssm_client.put_parameter.call_args_list[0]
        assert '/krishi/production/' in param_call[1]['Name']
        
        secret_call = mock_secrets_client.create_secret.call_args_list[0]
        assert '/krishi/production/' in secret_call[1]['Name']
    
    @patch('boto3.client')
    def test_setup_configuration_handles_access_denied_error(
        self, mock_boto_client, deployer, mock_ssm_client, mock_secrets_client
    ):
        """Test that access denied errors are handled with helpful messages"""
        # Setup mocks
        def get_client(service, **kwargs):
            if service == 'ssm':
                return mock_ssm_client
            elif service == 'secretsmanager':
                return mock_secrets_client
            return Mock()
        
        mock_boto_client.side_effect = get_client
        
        # Simulate access denied error
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'AccessDeniedException',
                'Message': 'User is not authorized'
            }
        }
        mock_ssm_client.put_parameter.side_effect = ClientError(
            error_response, 'PutParameter'
        )
        
        # Test data
        config_values = {'app_name': 'Krishi'}
        secret_values = {}
        
        # Execute and verify exception is raised
        with pytest.raises(ClientError) as exc_info:
            deployer.setup_configuration(config_values, secret_values)
        
        assert exc_info.value.response['Error']['Code'] == 'AccessDeniedException'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
