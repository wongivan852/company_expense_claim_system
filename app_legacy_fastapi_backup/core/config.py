"""Enhanced application configuration for business requirements."""

import os
from typing import Optional


class Settings:
    """Enhanced application settings with business features."""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./expense_claims.db")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production-krystal-institute-2024")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours for business use

    # Email Configuration
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() == "true"
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@krystal-institute.com")
    EMAIL_FROM_NAME: str = "Krystal Institute Expense System"

    # File Upload Configuration
    MAX_FILE_SIZE: int = 20971520  # 20MB for business receipts
    UPLOAD_DIR: str = "uploads"
    ALLOWED_FILE_TYPES: list = ["image/jpeg", "image/png", "image/gif", "image/bmp", "image/tiff", "application/pdf"]
    
    # Image processing
    MAX_IMAGE_WIDTH: int = 2048
    MAX_IMAGE_HEIGHT: int = 2048
    THUMBNAIL_SIZE: tuple = (300, 300)
    COMPRESSION_QUALITY: int = 85

    # Currency Exchange API
    EXCHANGE_RATE_API_KEY: Optional[str] = os.getenv("EXCHANGE_RATE_API_KEY")
    EXCHANGE_RATE_CACHE_HOURS: int = 1
    DEFAULT_BASE_CURRENCY: str = "HKD"

    # OCR Configuration
    OCR_ENABLED: bool = True
    TESSERACT_CMD: Optional[str] = os.getenv("TESSERACT_CMD")
    OCR_LANGUAGES: str = "chi_sim+chi_tra+eng"
    OCR_CONFIDENCE_THRESHOLD: float = 30.0

    # Business Rules
    AUTO_APPROVE_THRESHOLD_HKD: float = 1000.0
    REQUIRE_RECEIPT_THRESHOLD_HKD: float = 100.0
    MAX_CLAIM_AMOUNT_HKD: float = 100000.0
    
    # Multi-language Support
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: list = ["en", "zh-CN", "zh-TW"]
    
    # Application URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8084")
    
    # Company-specific settings
    COMPANIES: dict = {
        "KIL": {
            "name": "Krystal Institute Limited",
            "email_domain": "krystal-institute.com",
            "default_currency": "HKD",
            "approval_levels": 2
        },
        "KTL": {
            "name": "Krystal Technology Limited", 
            "email_domain": "krystal-tech.com",
            "default_currency": "HKD",
            "approval_levels": 2
        },
        "CGEL": {
            "name": "CG Global Entertainment Limited",
            "email_domain": "cg-global.com", 
            "default_currency": "HKD",
            "approval_levels": 2
        },
        "SPGZ": {
            "name": "数谱环球(深圳)科技有限公司",
            "email_domain": "shuzhi-global.com",
            "default_currency": "RMB",
            "approval_levels": 2
        }
    }

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    @property
    def upload_path(self) -> str:
        """Get absolute upload path."""
        return os.path.abspath(self.UPLOAD_DIR)

    def get_company_settings(self, company_code: str) -> dict:
        """Get settings for specific company."""
        return self.COMPANIES.get(company_code, {})

    def is_email_enabled(self) -> bool:
        """Check if email is properly configured."""
        return (
            self.EMAIL_ENABLED and 
            self.SMTP_USER and 
            self.SMTP_PASSWORD
        )


# Create global settings instance
settings = Settings()

# Create upload directories
os.makedirs(settings.upload_path, exist_ok=True)
os.makedirs(os.path.join(settings.upload_path, "receipts"), exist_ok=True)
os.makedirs(os.path.join(settings.upload_path, "thumbnails"), exist_ok=True)
os.makedirs(os.path.join(settings.upload_path, "compressed"), exist_ok=True)