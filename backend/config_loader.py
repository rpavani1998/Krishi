"""
Configuration loader for AWS Lambda.

This module provides functionality to load configuration from AWS Parameter Store
and Secrets Manager, setting environment variables for the application to use.

Requirements: 4.3, 4.5
"""

import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Global variable for Lambda container reuse
config_loaded = False


def load_config() -> Dict[str, str]:
    """
    Load configuration from AWS Parameter Store and Secrets Manager.
    
    This function retrieves non-sensitive configuration from AWS Systems Manager
    Parameter Store and sensitive credentials from AWS Secrets Manager. All values
    are set as environment variables for the application to use.
    
    The function uses a global variable to cache configuration across Lambda
    invocations within the same container, avoiding redundant AWS API calls.
    
    Returns:
        Dictionary containing all loaded configuration values
        
    Requirements: 4.3, 4.5
    """
    global config_loaded
    
    # Return early if configuration already loaded in this container
    if config_loaded:
        logger.info("Configuration already loaded in this Lambda container")
        return {}
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Get environment name from Lambda environment variable
        environment = os.environ.get('ENVIRONMENT', 'prototype')
        
        logger.info(f"Loading configuration for environment: {environment}")
        
        config_values = {}
        
        # Initialize AWS clients
        ssm_client = boto3.client('ssm')
        secrets_client = boto3.client('secretsmanager')
        
        # Load parameters from Parameter Store
        try:
            logger.debug(f"Retrieving parameters from path: /krishi/{environment}/")
            
            # Get all parameters under the environment path
            paginator = ssm_client.get_paginator('get_parameters_by_path')
            page_iterator = paginator.paginate(
                Path=f'/krishi/{environment}/',
                Recursive=True,
                WithDecryption=False
            )
            
            param_count = 0
            for page in page_iterator:
                for param in page.get('Parameters', []):
                    # Extract parameter name (remove path prefix)
                    param_name = param['Name'].split('/')[-1]
                    param_value = param['Value']
                    
                    # Set as environment variable (uppercase)
                    env_var_name = param_name.upper()
                    os.environ[env_var_name] = param_value
                    config_values[env_var_name] = param_value
                    
                    logger.debug(f"Loaded parameter: {param_name} -> {env_var_name}")
                    param_count += 1
            
            logger.info(f"✓ Loaded {param_count} parameters from Parameter Store")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'AccessDeniedException':
                logger.warning("Access denied to Parameter Store - check IAM permissions")
            else:
                logger.warning(f"Failed to load parameters from Parameter Store: {e}")
        
        # Load secrets from Secrets Manager
        # Define expected secret names
        secret_names = [
            f'/krishi/{environment}/ceda_api_key',
            f'/krishi/{environment}/news_api_key'
        ]
        
        secret_count = 0
        for secret_name in secret_names:
            try:
                logger.debug(f"Retrieving secret: {secret_name}")
                
                response = secrets_client.get_secret_value(SecretId=secret_name)
                secret_value = response['SecretString']
                
                # Extract secret key name (remove path prefix)
                key_name = secret_name.split('/')[-1]
                
                # Set as environment variable (uppercase)
                env_var_name = key_name.upper()
                os.environ[env_var_name] = secret_value
                config_values[env_var_name] = '***'  # Don't log actual secret value
                
                logger.debug(f"Loaded secret: {key_name} -> {env_var_name}")
                secret_count += 1
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                if error_code == 'ResourceNotFoundException':
                    logger.warning(f"Secret not found: {secret_name}")
                elif error_code == 'AccessDeniedException':
                    logger.warning(f"Access denied to secret: {secret_name}")
                else:
                    logger.warning(f"Failed to load secret {secret_name}: {e}")
        
        logger.info(f"✓ Loaded {secret_count} secrets from Secrets Manager")
        
        # Mark configuration as loaded
        config_loaded = True
        
        logger.info(f"✓ Configuration loading complete: {param_count} parameters, {secret_count} secrets")
        
        return config_values
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}", exc_info=True)
        # Don't fail Lambda initialization - allow it to start with default config
        return {}
