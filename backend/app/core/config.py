from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Krishi Backend"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Weather Service (Open-Meteo)
    OPEN_METEO_URL: str = "https://api.open-meteo.com/v1/forecast"
    
    # Price Service (CEDA / Agmarknet)
    CEDA_API_KEY: Optional[str] = None
    
    # News Service (APITube)
    NEWS_API_URL: str = "https://api.apitube.io/v1/news/everything"
    NEWS_API_KEY: Optional[str] = None  # APITube API key
    NEWS_API_ENABLED: bool = True  
    

    # AWS (Future)
    # AWS_ACCESS_KEY_ID: Optional[str] = None
    # AWS_SECRET_ACCESS_KEY: Optional[str] = None
    # AWS_REGION: str = "ap-south-1"

    # AI Service Configuration
    USE_AWS_AI: bool = False  # Set to True to use AWS Bedrock/Polly/Transcribe
    OLLAMA_BASE_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"


    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
