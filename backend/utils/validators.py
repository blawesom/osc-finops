"""Data validation utilities for database operations."""
import uuid
import json
import math
from typing import Any, Optional, Dict


def validate_uuid(uuid_string: Optional[str]) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_string: UUID string to validate
    
    Returns:
        True if valid UUID, False otherwise
    """
    if not uuid_string:
        return False
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False


def sanitize_string(value: Any, max_length: int, default: str = "") -> str:
    """
    Sanitize string value for database storage.
    
    Args:
        value: Value to sanitize
        max_length: Maximum allowed length
        default: Default value if value is invalid
    
    Returns:
        Sanitized string
    """
    if value is None:
        return default
    
    # Convert to string
    str_value = str(value).strip()
    
    # Truncate if too long
    if len(str_value) > max_length:
        str_value = str_value[:max_length]
    
    # Return default if empty
    if not str_value:
        return default
    
    return str_value


def sanitize_float(value: Any, default: float = 0.0, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    """
    Sanitize float value for database storage.
    
    Args:
        value: Value to sanitize
        default: Default value if value is invalid
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
    
    Returns:
        Sanitized float
    """
    if value is None:
        return default
    
    try:
        float_value = float(value)
        
        # Check for NaN or Infinity
        if math.isnan(float_value) or math.isinf(float_value):
            return default
        
        # Check bounds
        if min_value is not None and float_value < min_value:
            return default if default >= min_value else min_value
        
        if max_value is not None and float_value > max_value:
            return default if default <= max_value else max_value
        
        return float_value
    except (ValueError, TypeError):
        return default


def sanitize_json(value: Any, default: str = "{}") -> str:
    """
    Sanitize value for JSON storage.
    
    Args:
        value: Value to serialize to JSON
        default: Default JSON string if serialization fails
    
    Returns:
        JSON string
    """
    if value is None:
        return default
    
    try:
        # Test serialization
        json.dumps(value)
        return json.dumps(value)
    except (TypeError, ValueError) as e:
        # Log warning (can be added later)
        # For now, return default
        return default


def validate_status(status: str) -> bool:
    """
    Validate quote status.
    
    Args:
        status: Status to validate
    
    Returns:
        True if valid, False otherwise
    """
    return status in ("active", "saved")


def validate_discount_percent(value: float) -> bool:
    """
    Validate discount percentage.
    
    Args:
        value: Discount percentage to validate
    
    Returns:
        True if valid (0-100), False otherwise
    """
    return 0.0 <= value <= 100.0

