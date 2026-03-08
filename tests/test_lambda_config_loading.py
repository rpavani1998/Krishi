"""
Unit tests for Lambda configuration loading functionality.

Tests the load_config() function that retrieves configuration from
AWS Parameter Store and Secrets Manager.

Requirements: 4.3, 4.5
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


@pytest.fixture
def mock_boto3_clients():
    """Mock boto3 clients for SSM and Secrets Manager."""
    # Mock mangum and app.main imports first
    with patch.dict('sys.modules', {
        'mangum': MagicMock(),
        'app': MagicMock(),
        'app.main': MagicMock()
    }):
        with patch('boto3.client') as mock_client:
            # Create mock clients
            mock_ssm = MagicMock()
            mock_secrets = MagicMock()
            
            # Configure boto3.client to return appropriate mock based on service name
            def client_factory(service_name, **kwargs):
                if service_name == 'ssm':
                    return mock_ssm
                elif service_name == 'secretsmanager':
                    return mock_secrets
                else:
                    raise ValueError(f"Unexpected service: {service_name}")
            
            mock_client.side_effect = client_factory
            
            yield {
                'ssm': mock_ssm,
                'secrets': mock_secrets
            }


@pytest.fixture
def reset_config_state():
    """Reset global config_loaded state before each test."""
    # Import the module to reset its state
    import sys
    
    # Remove the module from cache
    modules_to_remove = [k for k in sys.modules.keys() if 'config_loader' in k or 'lambda_handler' in k]
    for mod in modules_to_remove:
        del sys.modules[mod]
    
    yield
    
    # Clean up after test
    modules_to_remove = [k for k in sys.modules.keys() if 'config_loader' in k or 'lambda_handler' in k]
    for mod in modules_to_remove:
        del sys.modules[mod]


def test_load_config_retrieves_parameters_from_parameter_store(mock_boto3_clients, reset_config_state):
    """
    Test that load_config retrieves parameters from Parameter Store.
    
    Validates: Requirements 4.3
    """
    from botocore.exceptions import ClientError
    
    # Setup mock SSM response
    mock_ssm = mock_boto3_clients['ssm']
    mock_paginator = MagicMock()
    mock_ssm.get_paginator.return_value = mock_paginator
    
    # Mock parameter store response
    mock_paginator.paginate.return_value = [
        {
            'Parameters': [
                {'Name': '/krishi/prototype/app_name', 'Value': 'Krishi Backend'},
                {'Name': '/krishi/prototype/debug', 'Value': 'false'},
                {'Name': '/krishi/prototype/open_meteo_url', 'Value': 'https://api.open-meteo.com/v1/forecast'}
            ]
        }
    ]
    
    # Mock secrets manager (no secrets for this test)
    mock_secrets = mock_boto3_clients['secrets']
    
    def raise_not_found(*args, **kwargs):
        raise ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )
    
    mock_secrets.get_secret_value.side_effect = raise_not_found
    
    # Set environment
    os.environ['ENVIRONMENT'] = 'prototype'
    
    # Import and call load_config
    from backend.config_loader import load_config
    
    result = load_config()
    
    # Verify parameters were loaded
    assert 'APP_NAME' in result
    assert result['APP_NAME'] == 'Krishi Backend'
    assert 'DEBUG' in result
    assert result['DEBUG'] == 'false'
    assert 'OPEN_METEO_URL' in result
    
    # Verify environment variables were set
    assert os.environ.get('APP_NAME') == 'Krishi Backend'
    assert os.environ.get('DEBUG') == 'false'
    assert os.environ.get('OPEN_METEO_URL') == 'https://api.open-meteo.com/v1/forecast'
    
    # Verify SSM was called correctly
    mock_ssm.get_paginator.assert_called_once_with('get_parameters_by_path')
    mock_paginator.paginate.assert_called_once_with(
        Path='/krishi/prototype/',
        Recursive=True,
        WithDecryption=False
    )


def test_load_config_retrieves_secrets_from_secrets_manager(mock_boto3_clients, reset_config_state):
    """
    Test that load_config retrieves secrets from Secrets Manager.
    
    Validates: Requirements 4.3
    """
    # Setup mock SSM (no parameters for this test)
    mock_ssm = mock_boto3_clients['ssm']
    mock_paginator = MagicMock()
    mock_ssm.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{'Parameters': []}]
    
    # Mock secrets manager response
    mock_secrets = mock_boto3_clients['secrets']
    
    def get_secret_value(SecretId):
        if 'ceda_api_key' in SecretId:
            return {'SecretString': 'test-ceda-key-123'}
        elif 'news_api_key' in SecretId:
            return {'SecretString': 'test-news-key-456'}
        else:
            raise Exception("ResourceNotFoundException")
    
    mock_secrets.get_secret_value.side_effect = get_secret_value
    
    # Set environment
    os.environ['ENVIRONMENT'] = 'prototype'
    
    # Import and call load_config
    from backend.config_loader import load_config
    
    result = load_config()
    
    # Verify secrets were loaded (but values are masked in result)
    assert 'CEDA_API_KEY' in result
    assert result['CEDA_API_KEY'] == '***'  # Masked in result
    assert 'NEWS_API_KEY' in result
    assert result['NEWS_API_KEY'] == '***'  # Masked in result
    
    # Verify environment variables were set with actual values
    assert os.environ.get('CEDA_API_KEY') == 'test-ceda-key-123'
    assert os.environ.get('NEWS_API_KEY') == 'test-news-key-456'
    
    # Verify Secrets Manager was called correctly
    assert mock_secrets.get_secret_value.call_count == 2


def test_load_config_sets_environment_variables(mock_boto3_clients, reset_config_state):
    """
    Test that load_config sets environment variables for application use.
    
    Validates: Requirements 4.5
    """
    # Setup mock responses
    mock_ssm = mock_boto3_clients['ssm']
    mock_paginator = MagicMock()
    mock_ssm.get_paginator.return_value = mock_paginator
    
    mock_paginator.paginate.return_value = [
        {
            'Parameters': [
                {'Name': '/krishi/prototype/use_aws_ai', 'Value': 'false'},
                {'Name': '/krishi/prototype/ollama_base_url', 'Value': 'http://ollama:11434/api/generate'}
            ]
        }
    ]
    
    mock_secrets = mock_boto3_clients['secrets']
    from botocore.exceptions import ClientError
    def raise_not_found(*args, **kwargs):
        raise ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )
    mock_secrets.get_secret_value.side_effect = raise_not_found
    
    # Set environment
    os.environ['ENVIRONMENT'] = 'prototype'
    
    # Clear any existing env vars
    os.environ.pop('USE_AWS_AI', None)
    os.environ.pop('OLLAMA_BASE_URL', None)
    
    # Import and call load_config
    from backend.config_loader import load_config
    
    load_config()
    
    # Verify environment variables were set
    assert os.environ.get('USE_AWS_AI') == 'false'
    assert os.environ.get('OLLAMA_BASE_URL') == 'http://ollama:11434/api/generate'


def test_load_config_caches_configuration_across_invocations(mock_boto3_clients, reset_config_state):
    """
    Test that load_config caches configuration and doesn't reload on subsequent calls.
    
    This simulates Lambda container reuse where the same container handles
    multiple invocations.
    
    Validates: Requirements 4.5
    """
    # Setup mock responses
    mock_ssm = mock_boto3_clients['ssm']
    mock_paginator = MagicMock()
    mock_ssm.get_paginator.return_value = mock_paginator
    
    mock_paginator.paginate.return_value = [
        {
            'Parameters': [
                {'Name': '/krishi/prototype/app_name', 'Value': 'Krishi Backend'}
            ]
        }
    ]
    
    mock_secrets = mock_boto3_clients['secrets']
    from botocore.exceptions import ClientError
    def raise_not_found(*args, **kwargs):
        raise ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )
    mock_secrets.get_secret_value.side_effect = raise_not_found
    
    # Set environment
    os.environ['ENVIRONMENT'] = 'prototype'
    
    # Import and call load_config
    from backend.config_loader import load_config
    
    # First call should load configuration
    result1 = load_config()
    assert 'APP_NAME' in result1
    
    # Second call should return cached (empty dict)
    result2 = load_config()
    assert result2 == {}
    
    # Verify AWS APIs were only called once
    assert mock_ssm.get_paginator.call_count == 1
    assert mock_secrets.get_secret_value.call_count == 2  # Tries both secrets


def test_load_config_handles_missing_parameters_gracefully(mock_boto3_clients, reset_config_state):
    """
    Test that load_config handles missing parameters gracefully without failing.
    
    Validates: Requirements 4.3
    """
    # Setup mock SSM to return no parameters
    mock_ssm = mock_boto3_clients['ssm']
    mock_paginator = MagicMock()
    mock_ssm.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{'Parameters': []}]
    
    # Mock secrets manager to return not found
    mock_secrets = mock_boto3_clients['secrets']
    from botocore.exceptions import ClientError
    
    def raise_not_found(*args, **kwargs):
        raise ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )
    
    mock_secrets.get_secret_value.side_effect = raise_not_found
    
    # Set environment
    os.environ['ENVIRONMENT'] = 'prototype'
    
    # Import and call load_config
    from backend.config_loader import load_config
    
    # Should not raise exception
    result = load_config()
    
    # Result should be empty but function should succeed
    assert isinstance(result, dict)


def test_load_config_handles_access_denied_gracefully(mock_boto3_clients, reset_config_state):
    """
    Test that load_config handles access denied errors gracefully.
    
    Validates: Requirements 4.3
    """
    # Setup mock SSM to return access denied
    mock_ssm = mock_boto3_clients['ssm']
    mock_paginator = MagicMock()
    mock_ssm.get_paginator.return_value = mock_paginator
    
    from botocore.exceptions import ClientError
    
    def raise_access_denied(*args, **kwargs):
        raise ClientError(
            {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}},
            'GetParametersByPath'
        )
    
    mock_paginator.paginate.side_effect = raise_access_denied
    
    # Mock secrets manager
    mock_secrets = mock_boto3_clients['secrets']
    mock_secrets.get_secret_value.side_effect = raise_access_denied
    
    # Set environment
    os.environ['ENVIRONMENT'] = 'prototype'
    
    # Import and call load_config
    from backend.config_loader import load_config
    
    # Should not raise exception
    result = load_config()
    
    # Result should be empty but function should succeed
    assert isinstance(result, dict)


def test_load_config_uses_correct_environment_path(mock_boto3_clients, reset_config_state):
    """
    Test that load_config uses the correct environment path from ENVIRONMENT variable.
    
    Validates: Requirements 4.3
    """
    # Setup mock responses
    mock_ssm = mock_boto3_clients['ssm']
    mock_paginator = MagicMock()
    mock_ssm.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{'Parameters': []}]
    
    mock_secrets = mock_boto3_clients['secrets']
    from botocore.exceptions import ClientError
    def raise_not_found(*args, **kwargs):
        raise ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )
    mock_secrets.get_secret_value.side_effect = raise_not_found
    
    # Set environment to staging
    os.environ['ENVIRONMENT'] = 'staging'
    
    # Import and call load_config
    from backend.config_loader import load_config
    
    load_config()
    
    # Verify correct path was used
    mock_paginator.paginate.assert_called_once_with(
        Path='/krishi/staging/',
        Recursive=True,
        WithDecryption=False
    )
    
    # Verify secrets used correct environment
    calls = mock_secrets.get_secret_value.call_args_list
    assert any('/krishi/staging/ceda_api_key' in str(call) for call in calls)
    assert any('/krishi/staging/news_api_key' in str(call) for call in calls)


def test_load_config_converts_parameter_names_to_uppercase(mock_boto3_clients, reset_config_state):
    """
    Test that load_config converts parameter names to uppercase for environment variables.
    
    Validates: Requirements 4.5
    """
    # Setup mock SSM response with lowercase parameter names
    mock_ssm = mock_boto3_clients['ssm']
    mock_paginator = MagicMock()
    mock_ssm.get_paginator.return_value = mock_paginator
    
    mock_paginator.paginate.return_value = [
        {
            'Parameters': [
                {'Name': '/krishi/prototype/app_name', 'Value': 'Test App'},
                {'Name': '/krishi/prototype/debug', 'Value': 'true'}
            ]
        }
    ]
    
    mock_secrets = mock_boto3_clients['secrets']
    from botocore.exceptions import ClientError
    def raise_not_found(*args, **kwargs):
        raise ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )
    mock_secrets.get_secret_value.side_effect = raise_not_found
    
    # Set environment
    os.environ['ENVIRONMENT'] = 'prototype'
    
    # Import and call load_config
    from backend.config_loader import load_config
    
    result = load_config()
    
    # Verify parameter names are uppercase in result
    assert 'APP_NAME' in result
    assert 'DEBUG' in result
    
    # Verify environment variables are uppercase
    assert os.environ.get('APP_NAME') == 'Test App'
    assert os.environ.get('DEBUG') == 'true'
