"""Error handling utilities."""
from typing import Dict, Any, Optional
from flask import jsonify


class APIError(Exception):
    """
    Custom exception for API errors.
    Can be raised in route handlers and will be caught by error handler.
    """
    def __init__(self, message: str, status_code: int = 400, code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.code = code or "API_ERROR"
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        error_dict = {
            "error": {
                "code": self.code,
                "message": self.message
            }
        }
        return error_dict


def error_response(code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None) -> tuple:
    """
    Create standardized error response.
    
    Args:
        code: Error code (e.g., "INVALID_CREDENTIALS")
        message: Human-readable error message
        status_code: HTTP status code
        details: Optional additional error details
    
    Returns:
        Tuple of (response, status_code) for Flask
    """
    response = {
        "error": {
            "code": code,
            "message": message
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return jsonify(response), status_code


def success_response(data: Any, status_code: int = 200, metadata: Optional[Dict[str, Any]] = None) -> tuple:
    """
    Create standardized success response.
    
    Args:
        data: Response data
        status_code: HTTP status code
        metadata: Optional metadata (pagination, cache info, etc.)
    
    Returns:
        Tuple of (response, status_code) for Flask
    """
    response = {"data": data}
    
    if metadata:
        response["metadata"] = metadata
    
    return jsonify(response), status_code

