"""Utility functions package."""
# Import validators (no Flask dependency)
from backend.utils.validators import (
    validate_uuid,
    sanitize_string,
    sanitize_float,
    sanitize_json,
    validate_status,
    validate_discount_percent
)

# Import errors (has Flask dependency - may fail if Flask not installed)
try:
    from backend.utils.errors import APIError, error_response, success_response
    __all__ = [
        "APIError",
        "error_response",
        "success_response",
        "validate_uuid",
        "sanitize_string",
        "sanitize_float",
        "sanitize_json",
        "validate_status",
        "validate_discount_percent"
    ]
except ImportError:
    # Flask not installed, only export validators
    __all__ = [
        "validate_uuid",
        "sanitize_string",
        "sanitize_float",
        "sanitize_json",
        "validate_status",
        "validate_discount_percent"
    ]
