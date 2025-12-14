"""Application configuration settings."""
import os
from typing import List

# Supported regions
SUPPORTED_REGIONS: List[str] = [
    "cloudgouv-eu-west-1",
    "eu-west-2",
    "us-west-1",
    "us-east-2"
]

# Session configuration
SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "1800"))  # 30 minutes in seconds
SESSION_COOKIE_NAME: str = "osc_finops_session"
SESSION_COOKIE_HTTPONLY: bool = True
SESSION_COOKIE_SECURE: bool = os.getenv("FLASK_ENV") == "production"
SESSION_COOKIE_SAMESITE: str = "Lax"

# Flask configuration
FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "1") == "1"

# SECRET_KEY: In production, this MUST be set via environment variable
# Generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
if FLASK_ENV == "production":
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY environment variable is required in production. "
            "Generate one with: python3 -c \"import secrets; print(secrets.token_hex(32))\""
        )
else:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# Server configuration
SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

# CORS configuration
CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")

# Cache configuration
CATALOG_CACHE_TTL: int = int(os.getenv("CATALOG_CACHE_TTL", "86400"))  # 24 hours in seconds
CONSUMPTION_CACHE_TTL: int = int(os.getenv("CONSUMPTION_CACHE_TTL", "3600"))  # 1 hour in seconds

# Logging configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/")
LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB default
LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
ERROR_LOG_FILE: str = os.getenv("ERROR_LOG_FILE", "errors.log")
APP_LOG_FILE: str = os.getenv("APP_LOG_FILE", "app.log")
API_CALLS_LOG_FILE: str = os.getenv("API_CALLS_LOG_FILE", "api_calls.log")
ENABLE_API_CALL_LOGGING: bool = (
    os.getenv("ENABLE_API_CALL_LOGGING", "1" if FLASK_ENV == "development" else "0") == "1"
)

# Database configuration
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///osc_finops.db")
DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "0") == "1"

