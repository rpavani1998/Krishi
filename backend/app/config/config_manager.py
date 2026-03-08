"""
Unified configuration manager for Krishi application.
This module provides a single interface for environment-specific configurations.
"""
import os
from typing import Any, Dict, Optional
from enum import Enum

# Import environment-specific configurations
try:
    from .aws_config import aws_config, AWSRDSConfig, AWSS3Config, AWSBedrockConfig, AWSCloudWatchConfig
except ImportError:
    aws_config = None
    AWSRDSConfig = None
    AWSS3Config = None
    AWSBedrockConfig = None
    AWSCloudWatchConfig = None

try:
    from .local_config import local_config, LocalDatabaseConfig, LocalStorageConfig, LocalAIServicesConfig, LocalChromaConfig, LocalLoggingConfig
except ImportError:
    local_config = None
    LocalDatabaseConfig = None
    LocalStorageConfig = None
    LocalAIServicesConfig = None
    LocalChromaConfig = None
    LocalLoggingConfig = None

class DeploymentEnvironment(Enum):
    """Supported deployment environments."""
    AWS = "aws"
    LOCAL = "local"
    DOCKER = "docker"

class ConfigManager:
    """Unified configuration manager that switches between environments."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self._environment = self._detect_environment()
        self._config_cache = {}
    
    def _detect_environment(self) -> DeploymentEnvironment:
        """Automatically detect the deployment environment."""
        # Force local environment for debugging
        return DeploymentEnvironment.LOCAL
    
    @property
    def environment(self) -> DeploymentEnvironment:
        """Get current deployment environment."""
        return self._environment
    
    @property
    def is_aws(self) -> bool:
        """Check if running in AWS environment."""
        return self._environment == DeploymentEnvironment.AWS
    
    @property
    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self._environment == DeploymentEnvironment.LOCAL
    
    @property
    def is_docker(self) -> bool:
        """Check if running in Docker environment."""
        return self._environment == DeploymentEnvironment.DOCKER
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for current environment."""
        if self.is_aws:
            if AWSRDSConfig is None:
                raise RuntimeError("AWS configuration not available")
            return {
                "connection_string": AWSRDSConfig.get_connection_string(),
                "connection_params": AWSRDSConfig.get_connection_params(),
                "multi_az": aws_config.RDS_MULTI_AZ,
                "backup_retention": aws_config.RDS_BACKUP_RETENTION,
                "encrypted": aws_config.RDS_STORAGE_ENCRYPTED,
            }
        else:
            if LocalDatabaseConfig is None:
                raise RuntimeError("Local configuration not available")
            return {
                "connection_string": local_config.DATABASE_URL,
                "connection_params": LocalDatabaseConfig.get_connection_params(),
                "type": local_config.DATABASE_TYPE,
                "schemas": LocalDatabaseConfig.get_table_schemas(),
            }
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration for current environment."""
        if self.is_aws:
            if AWSS3Config is None:
                raise RuntimeError("AWS configuration not available")
            return {
                "type": "s3",
                "bucket_name": aws_config.S3_BUCKET_NAME,
                "encryption": aws_config.S3_ENCRYPTION,
                "versioning": aws_config.S3_VERSIONING,
                "bucket_policy": AWSS3Config.get_bucket_policy(),
                "lifecycle_policy": AWSS3Config.get_lifecycle_policy(),
            }
        else:
            if LocalStorageConfig is None:
                raise RuntimeError("Local configuration not available")
            return {
                "type": "local",
                "base_path": local_config.STORAGE_BASE_PATH,
                "paths": LocalStorageConfig.get_storage_paths(),
                "max_file_size": local_config.STORAGE_MAX_FILE_SIZE,
                "allowed_extensions": local_config.STORAGE_ALLOWED_EXTENSIONS.split(","),
                "cleanup_config": LocalStorageConfig.get_file_cleanup_config(),
            }
    
    def get_ai_services_config(self) -> Dict[str, Any]:
        """Get AI services configuration for current environment."""
        if self.is_aws:
            if AWSBedrockConfig is None:
                raise RuntimeError("AWS configuration not available")
            return {
                "transcribe": {
                    "region": aws_config.AWS_REGION,
                    "sample_rate": aws_config.TRANSCRIBE_MEDIA_SAMPLE_RATE,
                    "language_code": aws_config.TRANSCRIBE_LANGUAGE_CODE,
                },
                "bedrock": {
                    "model_id": aws_config.BEDROCK_MODEL_ID,
                    "max_tokens": aws_config.BEDROCK_MAX_TOKENS,
                    "temperature": aws_config.BEDROCK_TEMPERATURE,
                    "model_config": AWSBedrockConfig.get_model_config(),
                    "system_prompt": AWSBedrockConfig.get_system_prompt(),
                },
                "polly": {
                    "voice_id": aws_config.POLLY_VOICE_ID,
                    "engine": aws_config.POLLY_ENGINE,
                    "language_code": aws_config.POLLY_LANGUAGE_CODE,
                },
            }
        else:
            if LocalAIServicesConfig is None:
                raise RuntimeError("Local configuration not available")
            return {
                "ollama": LocalAIServicesConfig.get_ollama_config(),
                "whisper": LocalAIServicesConfig.get_whisper_config(),
                "gtts": LocalAIServicesConfig.get_gtts_config(),
            }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration for current environment."""
        if self.is_aws:
            if AWSCloudWatchConfig is None:
                raise RuntimeError("AWS configuration not available")
            return {
                "type": "cloudwatch",
                "log_retention": aws_config.CLOUDWATCH_LOG_RETENTION,
                "metrics_namespace": aws_config.CLOUDWATCH_METRICS_NAMESPACE,
                "enable_xray": aws_config.ENABLE_XRAY,
                "enable_insights": aws_config.ENABLE_CLOUDWATCH_INSIGHTS,
            }
        else:
            if LocalLoggingConfig is None:
                raise RuntimeError("Local configuration not available")
            return {
                "type": "local",
                "level": local_config.LOG_LEVEL,
                "format": local_config.LOG_FORMAT,
                "file": local_config.LOG_FILE,
                "config": LocalLoggingConfig.get_logging_config(),
            }
    
    def get_vector_db_config(self) -> Dict[str, Any]:
        """Get vector database configuration."""
        if self.is_aws:
            # AWS version can use ChromaDB with S3 persistence or Amazon OpenSearch
            return {
                "type": "chromadb",
                "persist_directory": "/tmp/chroma_db",  # Lambda temporary storage
                "collection_name": "krishi_knowledge",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            }
        else:
            if LocalChromaConfig is None:
                raise RuntimeError("Local configuration not available")
            return LocalChromaConfig.get_chroma_config()
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration for current environment."""
        if self.is_aws:
            return {
                "type": "aws",
                "vpc_id": aws_config.VPC_ID,
                "security_group_ids": aws_config.SECURITY_GROUP_IDS,
                "subnet_ids": aws_config.SUBNET_IDS,
                "encryption": True,
            }
        else:
            return {
                "type": "local",
                "jwt_secret": local_config.JWT_SECRET_KEY,
                "jwt_algorithm": local_config.JWT_ALGORITHM,
                "jwt_expiration_minutes": local_config.JWT_EXPIRATION_MINUTES,
                "debug": local_config.DEBUG,
            }
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration for current environment."""
        if self.is_aws:
            return {
                "timeout": aws_config.LAMBDA_TIMEOUT,
                "memory_size": aws_config.LAMBDA_MEMORY_SIZE,
                "architecture": aws_config.LAMBDA_ARCHITECTURE,
                "region": aws_config.AWS_REGION,
            }
        else:
            return {
                "host": local_config.APP_HOST,
                "port": local_config.APP_PORT,
                "reload": local_config.APP_RELOAD,
                "workers": local_config.APP_WORKERS,
                "debug": local_config.DEBUG,
                "testing": local_config.TESTING,
            }
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration for current environment."""
        return {
            "environment": self._environment.value,
            "database": self.get_database_config(),
            "storage": self.get_storage_config(),
            "ai_services": self.get_ai_services_config(),
            "monitoring": self.get_monitoring_config(),
            "vector_db": self.get_vector_db_config(),
            "security": self.get_security_config(),
            "app": self.get_app_config(),
        }

# Global configuration manager instance
config_manager = ConfigManager()

# Convenience functions for quick access
def get_database_config() -> Dict[str, Any]:
    """Get database configuration."""
    return config_manager.get_database_config()

def get_storage_config() -> Dict[str, Any]:
    """Get storage configuration."""
    return config_manager.get_storage_config()

def get_ai_services_config() -> Dict[str, Any]:
    """Get AI services configuration."""
    return config_manager.get_ai_services_config()

def get_monitoring_config() -> Dict[str, Any]:
    """Get monitoring configuration."""
    return config_manager.get_monitoring_config()

def get_vector_db_config() -> Dict[str, Any]:
    """Get vector database configuration."""
    return config_manager.get_vector_db_config()

def get_security_config() -> Dict[str, Any]:
    """Get security configuration."""
    return config_manager.get_security_config()

def get_app_config() -> Dict[str, Any]:
    """Get application configuration."""
    return config_manager.get_app_config()

def get_all_config() -> Dict[str, Any]:
    """Get all configuration."""
    return config_manager.get_all_config()

# Export main components
__all__ = [
    'DeploymentEnvironment',
    'ConfigManager',
    'config_manager',
    'get_database_config',
    'get_storage_config',
    'get_ai_services_config',
    'get_monitoring_config',
    'get_vector_db_config',
    'get_security_config',
    'get_app_config',
    'get_all_config',
]