import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Image Upload Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Upload Service"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    STAGING_DATABASE_URL: Optional[str] = None
    PRODUCTION_DATABASE_URL: Optional[str] = None
    
    # Redis (for Celery)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Storage (Google Cloud Storage)
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_STORAGE_BUCKET: str = os.getenv("GOOGLE_STORAGE_BUCKET", "")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Worker
    WORKER_CONCURRENCY: int = 4
    WORKER_MAX_TASKS_PER_CHILD: int = 100
    
    # Image Processing
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    THUMBNAIL_SIZE: tuple = (150, 150)
    RESIZED_SIZE: tuple = (1200, 1200)
    JPEG_QUALITY: int = 85
    WEBP_QUALITY: int = 80
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()