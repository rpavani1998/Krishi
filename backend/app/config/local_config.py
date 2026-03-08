"""
Local-specific configuration for Krishi application.
This module contains all local self-contained service configurations.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, validator

class LocalConfig(BaseSettings):
    """Local-specific configuration settings."""
    
    # Application Configuration
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    APP_RELOAD: bool = True
    APP_WORKERS: int = 1
    
    # Database Configuration
    DATABASE_TYPE: str = "sqlite"  # sqlite or postgresql
    DATABASE_URL: Optional[str] = None
    DATABASE_NAME: str = "krishi_local.db"
    DATABASE_PATH: str = "./data"
    
    # File Storage Configuration
    STORAGE_TYPE: str = "local"  # local or minio
    STORAGE_BASE_PATH: str = "./uploads"
    STORAGE_MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    STORAGE_ALLOWED_EXTENSIONS: str = "mp3,wav,ogg,m4a"
    
    # AI Services Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"
    OLLAMA_TIMEOUT: int = 60  # seconds
    OLLAMA_MAX_RETRIES: int = 3
    
    # Whisper Configuration
    WHISPER_MODEL_SIZE: str = "base"  # tiny, base, small, medium, large
    WHISPER_DEVICE: str = "cpu"  # cpu or cuda
    WHISLMER_LANGUAGE: str = "en"
    
    # gTTS Configuration
    GTTS_LANG: str = "en"
    GTTS_TLD: str = "com"  # Top-level domain for accent
    GTTS_SLOW: bool = False
    
    # Vector Database Configuration
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "krishi_knowledge"
    CHROMA_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: str = "./logs/krishi.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Security Configuration
    JWT_SECRET_KEY: str = "local-development-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    
    # Development Configuration
    DEBUG: bool = True
    TESTING: bool = False
    MOCK_EXTERNAL_SERVICES: bool = True
    
    @validator("DATABASE_URL", pre=True, always=True)
    def set_database_url(cls, v, values):
        """Set database URL based on database type."""
        if v is not None:
            return v
        
        db_type = values.get("DATABASE_TYPE", "sqlite")
        
        if db_type == "sqlite":
            db_path = values.get("DATABASE_PATH", "./data")
            db_name = values.get("DATABASE_NAME", "krishi_local.db")
            
            # Ensure directory exists
            Path(db_path).mkdir(parents=True, exist_ok=True)
            
            return f"sqlite:///{os.path.join(db_path, db_name)}"
        
        elif db_type == "postgresql":
            return (
                f"postgresql://{os.getenv('POSTGRES_USER', 'krishi')}"
                f":{os.getenv('POSTGRES_PASSWORD', 'password')}"
                f"@{os.getenv('POSTGRES_HOST', 'localhost')}"
                f":{os.getenv('POSTGRES_PORT', '5432')}"
                f"/{os.getenv('POSTGRES_DB', 'krishi')}"
            )
        
        return v
    
    @validator("STORAGE_BASE_PATH")
    def validate_storage_path(cls, v):
        """Ensure storage path exists."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("CHROMA_PERSIST_DIRECTORY")
    def validate_chroma_path(cls, v):
        """Ensure ChromaDB path exists."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("LOG_FILE")
    def validate_log_path(cls, v):
        """Ensure log directory exists."""
        log_dir = os.path.dirname(v)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        return v
    
    class Config:
        env_file = ".env.local"
        case_sensitive = True
        env_file_encoding = "utf-8"

# Global local configuration instance
local_config = LocalConfig()

# Service-specific configuration classes
class LocalDatabaseConfig:
    """Local database-specific configuration."""
    
    @staticmethod
    def get_connection_params() -> dict:
        """Get database connection parameters."""
        if local_config.DATABASE_TYPE == "sqlite":
            return {
                "check_same_thread": False,
                "timeout": 30,
            }
        else:
            return {
                "sslmode": "disable",  # Local PostgreSQL
                "connect_timeout": 30,
                "application_name": "krishi-app-local",
            }
    
    @staticmethod
    def get_table_schemas() -> dict:
        """Get database table schemas."""
        return {
            "users": """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "profiles": """
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    location VARCHAR(200),
                    primary_crop VARCHAR(100),
                    farm_size_acres DECIMAL(10,2),
                    mobile_number VARCHAR(20),
                    pin VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """,
            "conversations": """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id VARCHAR(100) NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT,
                    message_type VARCHAR(50) DEFAULT 'text',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
        }

class LocalStorageConfig:
    """Local storage-specific configuration."""
    
    @staticmethod
    def get_storage_paths() -> dict:
        """Get local storage paths."""
        base_path = Path(local_config.STORAGE_BASE_PATH)
        
        paths = {
            "audio": base_path / "audio",
            "images": base_path / "images",
            "documents": base_path / "documents",
            "temp": base_path / "temp",
        }
        
        # Ensure all paths exist
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        
        return paths
    
    @staticmethod
    def get_file_cleanup_config() -> dict:
        """Get file cleanup configuration."""
        return {
            "temp_file_ttl_hours": 24,
            "max_storage_size_gb": 10,
            "cleanup_interval_hours": 6,
        }

class LocalAIServicesConfig:
    """Local AI services configuration."""
    
    @staticmethod
    def get_ollama_config() -> dict:
        """Get Ollama configuration."""
        return {
            "base_url": local_config.OLLAMA_BASE_URL,
            "model": local_config.OLLAMA_MODEL,
            "timeout": local_config.OLLAMA_TIMEOUT,
            "max_retries": local_config.OLLAMA_MAX_RETRIES,
            "system_prompt": """You are Krishi, an AI agricultural assistant designed to help farmers with crop management, weather information, pest control, and farming best practices.
            
            Key guidelines:
            - Provide accurate, practical advice for Indian agricultural conditions
            - Consider regional climate and soil conditions
            - Suggest cost-effective and sustainable farming practices
            - Be concise but comprehensive in your responses
            - Always prioritize farmer safety and crop health
            """,
        }
    
    @staticmethod
    def get_whisper_config() -> dict:
        """Get Whisper configuration."""
        return {
            "model_size": local_config.WHISPER_MODEL_SIZE,
            "device": local_config.WHISPER_DEVICE,
            "language": local_config.WHISPER_LANGUAGE,
            "download_root": "./models/whisper",
        }
    
    @staticmethod
    def get_gtts_config() -> dict:
        """Get gTTS configuration."""
        return {
            "lang": local_config.GTTS_LANG,
            "tld": local_config.GTTS_TLD,
            "slow": local_config.GTTS_SLOW,
        }

class LocalChromaConfig:
    """Local ChromaDB configuration."""
    
    @staticmethod
    def get_chroma_config() -> dict:
        """Get ChromaDB configuration."""
        return {
            "persist_directory": local_config.CHROMA_PERSIST_DIRECTORY,
            "collection_name": local_config.CHROMA_COLLECTION_NAME,
            "embedding_model": local_config.CHROMA_EMBEDDING_MODEL,
            "distance_metric": "cosine",
            "chunk_size": 1000,
            "chunk_overlap": 200,
        }

class LocalLoggingConfig:
    """Local logging configuration."""
    
    @staticmethod
    def get_logging_config() -> dict:
        """Get logging configuration."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
                },
                "text": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": local_config.LOG_LEVEL,
                    "formatter": local_config.LOG_FORMAT,
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": local_config.LOG_LEVEL,
                    "formatter": local_config.LOG_FORMAT,
                    "filename": local_config.LOG_FILE,
                    "maxBytes": local_config.LOG_MAX_SIZE,
                    "backupCount": local_config.LOG_BACKUP_COUNT
                }
            },
            "loggers": {
                "krishi": {
                    "level": local_config.LOG_LEVEL,
                    "handlers": ["console", "file"],
                    "propagate": False
                }
            },
            "root": {
                "level": local_config.LOG_LEVEL,
                "handlers": ["console"]
            }
        }

# Export configuration
__all__ = [
    'LocalConfig',
    'local_config',
    'LocalDatabaseConfig',
    'LocalStorageConfig',
    'LocalAIServicesConfig',
    'LocalChromaConfig',
    'LocalLoggingConfig'
]