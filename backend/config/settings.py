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
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# Server configuration
SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT: int = int(os.getenv("SERVER_PORT", "5000"))

# CORS configuration
CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")

# Logging configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

