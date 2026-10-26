"""Application configuration management using Pydantic Settings.

Reads settings from environment variables with strong type validation.
No secrets are hardcoded.
"""

from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Core
    APP_NAME: str = "Shikhor AI Backend"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_BACKEND: str = "sqlite"  # 'sqlite' or 'mongodb'
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/shikhor_ai"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Security
    JWT_SECRET_KEY: str = "insecure_dev_secret_please_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Integration Providers
    AI_PROVIDER: str = "mock"
    AI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    BASE_THRESHOLD: float = 0.70
    BASE_MODEL_REPO: str = "jitu25/bcdd-mobilenetv2"
    SECONDARY_MODEL_REPO: str = "jitu25/plant-disease-mobilenetv2"
    WEATHER_PROVIDER: str = "mock"
    WEATHER_API_KEY: str = ""
    SMS_PROVIDER: str = "mock"
    SMS_API_KEY: str = ""
    STORAGE_PROVIDER: str = "local"
    STORAGE_BUCKET_NAME: str = "shikhor-ai-storage"
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_UPLOAD_PRESET: str = ""

    # Firebase Authentication
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_API_KEY: str = ""

    # Email / SMTP Configuration
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "শিখড় এআই (Shikhor AI)"
    SMTP_TLS: bool = True

    # MongoDB Atlas Database Configuration
    MONGODB_URL: str = ""
    MONGODB_DB_NAME: str = "Shikhor"


settings = Settings()
