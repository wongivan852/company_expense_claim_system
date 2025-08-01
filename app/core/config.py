"""Application configuration."""

import os
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "postgresql://username:password@localhost:5432/expense_claim_db"

    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Email
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from: Optional[str] = None
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_from_name: str = "Company Expense System"

    # File Upload
    max_file_size: int = 10485760  # 10MB
    upload_directory: str = "uploads"

    # Environment
    environment: str = "development"
    debug: bool = True

    model_config = ConfigDict(env_file=".env")


settings = Settings()
