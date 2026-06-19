"""
Core configuration - loads from .env file
"""
from pydantic_settings import BaseSettings
from typing import List
import json
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "PDF Intelligence"
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    # Database — MySQL (aiomysql driver)
    DATABASE_URL: str = "mysql+aiomysql://root:@localhost:3306/pdf_intelligence"
    SYNC_DATABASE_URL: str = "mysql+pymysql://root:@localhost:3306/pdf_intelligence"

    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # AI Providers
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # AI Models
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GROQ_MODEL: str = "llama3-70b-8192"

    # Quota
    FREE_QUOTA_DAILY: int = 5
    PRO_QUOTA_DAILY: int = 50
    ENTERPRISE_QUOTA_DAILY: int = 500

    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"

    @property
    def cors_origins_list(self) -> List[str]:
        try:
            return json.loads(self.CORS_ORIGINS)
        except Exception:
            return [self.FRONTEND_URL]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)