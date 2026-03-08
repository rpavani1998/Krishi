"""
AWS-specific configuration for Krishi application.
This module contains all AWS cloud-native service configurations.
"""
import os
from typing import Optional
from pydantic import BaseSettings, validator

class AWSConfig(BaseSettings):
    """AWS-specific configuration settings."""
    
    # AWS Region and Account
    AWS_REGION: str = "ap-south-1"
    AWS_ACCOUNT_ID: Optional[str] = None
    
    # Lambda Configuration
    LAMBDA_TIMEOUT: int = 30  # seconds
    LAMBDA_MEMORY_SIZE: int = 1024  # MB
    LAMBDA_ARCHITECTURE: str = "arm64"
    
    # API Gateway Configuration
    API_GATEWAY_STAGE: str = "dev"
    API_GATEWAY_THROTTLE_RATE: int = 1000  # requests per second
    API_GATEWAY_BURST_LIMIT: int = 2000  # burst requests
    
    # RDS Configuration
    RDS_INSTANCE_TYPE: str = "db.t3.micro"
    RDS_MULTI_AZ: bool = True
    RDS_BACKUP_RETENTION: int = 7  # days
    RDS_STORAGE_ENCRYPTED: bool = True
    
    # S3 Configuration
    S3_BUCKET_NAME: str = "krishi-data-bucket"
    S3_ENCRYPTION: str = "AES256"
    S3_VERSIONING: bool = True
    S3_LIFECYCLE_DAYS: int = 90  # days to transition to cheaper storage
    
    # CloudWatch Configuration
    CLOUDWATCH_LOG_RETENTION: int = 14  # days
    CLOUDWATCH_METRICS_NAMESPACE: str = "KrishiApp"
    
    # Bedrock Configuration
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    BEDROCK_MAX_TOKENS: int = 1000
    BEDROCK_TEMPERATURE: float = 0.7
    
    # Transcribe Configuration
    TRANSCRIBE_MEDIA_SAMPLE_RATE: int = 16000
    TRANSCRIBE_LANGUAGE_CODE: str = "en-IN"
    
    # Polly Configuration
    POLLY_VOICE_ID: str = "Aditi"  # Indian English voice
    POLLY_ENGINE: str = "neural"  # or "standard"
    POLLY_LANGUAGE_CODE: str = "en-IN"
    
    # Security Configuration
    VPC_ID: Optional[str] = None
    SECURITY_GROUP_IDS: Optional[str] = None
    SUBNET_IDS: Optional[str] = None
    
    # Monitoring Configuration
    ENABLE_XRAY: bool = True
    ENABLE_CLOUDWATCH_INSIGHTS: bool = True
    
    @validator("AWS_ACCOUNT_ID", pre=True, always=True)
    def set_aws_account_id(cls, v):
        """Set AWS account ID from environment or STS."""
        if v is None:
            try:
                import boto3
                sts = boto3.client('sts')
                return sts.get_caller_identity()['Account']
            except Exception:
                return None
        return v
    
    @validator("S3_BUCKET_NAME")
    def validate_s3_bucket_name(cls, v):
        """Ensure S3 bucket name is globally unique."""
        if not v:
            raise ValueError("S3 bucket name cannot be empty")
        
        # Append account ID and region for uniqueness
        account_id = os.getenv("AWS_ACCOUNT_ID", "")
        region = os.getenv("AWS_REGION", "us-east-1")
        
        if account_id and account_id not in v:
            v = f"{v}-{account_id}-{region}"
        
        return v.lower().replace("_", "-")
    
    class Config:
        env_file = ".env.aws"
        case_sensitive = True
        env_file_encoding = "utf-8"

# Global AWS configuration instance
aws_config = AWSConfig()

# Service-specific configuration classes
class AWSRDSConfig:
    """AWS RDS-specific configuration."""
    
    @staticmethod
    def get_connection_string() -> str:
        """Generate RDS connection string."""
        return (
            f"postgresql://{os.getenv('RDS_USERNAME', 'krishi')}"
            f":{os.getenv('RDS_PASSWORD', '')}"
            f"@{os.getenv('RDS_ENDPOINT', 'localhost')}"
            f":{os.getenv('RDS_PORT', '5432')}"
            f"/{os.getenv('RDS_DATABASE', 'krishi')}"
        )
    
    @staticmethod
    def get_connection_params() -> dict:
        """Get RDS connection parameters."""
        return {
            "sslmode": "require",
            "connect_timeout": 30,
            "application_name": "krishi-app",
        }

class AWSS3Config:
    """AWS S3-specific configuration."""
    
    @staticmethod
    def get_bucket_policy() -> dict:
        """Generate S3 bucket policy."""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DenyInsecureConnections",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:*",
                    "Resource": f"arn:aws:s3:::{aws_config.S3_BUCKET_NAME}/*",
                    "Condition": {
                        "Bool": {
                            "aws:SecureTransport": "false"
                        }
                    }
                }
            ]
        }
    
    @staticmethod
    def get_lifecycle_policy() -> dict:
        """Generate S3 lifecycle policy."""
        return {
            "Rules": [
                {
                    "ID": "TransitionToIA",
                    "Status": "Enabled",
                    "Transitions": [
                        {
                            "Days": aws_config.S3_LIFECYCLE_DAYS,
                            "StorageClass": "STANDARD_IA"
                        }
                    ]
                }
            ]
        }

class AWSBedrockConfig:
    """AWS Bedrock-specific configuration."""
    
    @staticmethod
    def get_model_config() -> dict:
        """Get Bedrock model configuration."""
        return {
            "modelId": aws_config.BEDROCK_MODEL_ID,
            "contentType": "application/json",
            "accept": "application/json",
            "body": {
                "max_tokens": aws_config.BEDROCK_MAX_TOKENS,
                "temperature": aws_config.BEDROCK_TEMPERATURE,
            }
        }
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get system prompt for agricultural assistant."""
        return """You are Krishi, an AI agricultural assistant designed to help farmers with crop management, weather information, pest control, and farming best practices. 
        
        Key guidelines:
        - Provide accurate, practical advice for Indian agricultural conditions
        - Consider regional climate and soil conditions
        - Suggest cost-effective and sustainable farming practices
        - Be concise but comprehensive in your responses
        - Always prioritize farmer safety and crop health
        """

class AWSCloudWatchConfig:
    """AWS CloudWatch-specific configuration."""
    
    @staticmethod
    def get_log_group_name(function_name: str) -> str:
        """Generate CloudWatch log group name."""
        return f"/aws/lambda/{function_name}"
    
    @staticmethod
    def get_metric_filters() -> list:
        """Get CloudWatch metric filters."""
        return [
            {
                "FilterName": "ErrorCount",
                "FilterPattern": "[timestamp, request_id, level=ERROR, ...]",
                "MetricTransformations": [
                    {
                        "MetricNamespace": aws_config.CLOUDWATCH_METRICS_NAMESPACE,
                        "MetricName": "ErrorCount",
                        "MetricValue": "1",
                        "Unit": "Count"
                    }
                ]
            },
            {
                "FilterName": "ResponseTime",
                "FilterPattern": "[timestamp, request_id, level=INFO, message, response_time, ...]",
                "MetricTransformations": [
                    {
                        "MetricNamespace": aws_config.CLOUDWATCH_METRICS_NAMESPACE,
                        "MetricName": "ResponseTime",
                        "MetricValue": "$response_time",
                        "Unit": "Milliseconds"
                    }
                ]
            }
        ]

# Export configuration
__all__ = [
    'AWSConfig',
    'aws_config',
    'AWSRDSConfig',
    'AWSS3Config',
    'AWSBedrockConfig',
    'AWSCloudWatchConfig'
]