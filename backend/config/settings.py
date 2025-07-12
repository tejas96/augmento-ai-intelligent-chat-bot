from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # API Configuration
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    
    # S3 Configuration
    S3_BUCKET_NAME: str = "your-multimodal-chatbot-bucket"
    S3_PRESIGNED_URL_EXPIRY: int = 3600  # 1 hour
    
    # Bedrock Configuration
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_CLAUDE_MODEL: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    BEDROCK_TITAN_IMAGE_MODEL: str = "amazon.titan-image-generator-v1"
    BEDROCK_STABILITY_MODEL: str = "stability.stable-diffusion-xl-base-v1-0"
    
    # LangChain Configuration
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Ensure required AWS credentials are available
def validate_aws_credentials():
    """Validate AWS credentials are configured"""
    if not any([
        settings.AWS_ACCESS_KEY_ID,
        os.environ.get("AWS_PROFILE"),
        os.environ.get("AWS_ROLE_ARN")
    ]):
        raise ValueError(
            "AWS credentials not configured. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
            "or configure AWS_PROFILE or AWS_ROLE_ARN in environment variables."
        )

# AWS Bedrock model configurations
BEDROCK_MODELS = {
    "claude": {
        "model_id": settings.BEDROCK_CLAUDE_MODEL,
        "model_kwargs": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 4000,
        }
    },
    "titan_image": {
        "model_id": settings.BEDROCK_TITAN_IMAGE_MODEL,
        "model_kwargs": {
            "numberOfImages": 1,
            "quality": "premium",
            "height": 1024,
            "width": 1024,
        }
    },
    "stability": {
        "model_id": settings.BEDROCK_STABILITY_MODEL,
        "model_kwargs": {
            "cfg_scale": 7,
            "steps": 30,
            "height": 1024,
            "width": 1024,
        }
    }
} 