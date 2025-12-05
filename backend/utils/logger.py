"""Logging configuration and setup."""
import os
import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from pathlib import Path

from backend.config.settings import (
    LOG_LEVEL,
    LOG_FILE_PATH,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT,
    ERROR_LOG_FILE,
    APP_LOG_FILE
)


def setup_logging():
    """
    Configure logging with file rotation and JSON formatting.
    Creates separate loggers for general app logs and error-only logs.
    """
    # Ensure log directory exists
    log_dir = Path(LOG_FILE_PATH)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert LOG_LEVEL string to logging level
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Create JSON formatter
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        timestamp=True
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # General app log handler (INFO and above)
    app_log_path = log_dir / APP_LOG_FILE
    app_handler = RotatingFileHandler(
        app_log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(json_formatter)
    root_logger.addHandler(app_handler)
    
    # Error-only log handler (ERROR and above)
    error_log_path = log_dir / ERROR_LOG_FILE
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)
    
    # Also add console handler for development
    if os.getenv("FLASK_ENV", "development") == "development":
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    return root_logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()

