"""Error logging utilities for capturing exceptions with request context."""
import traceback
from typing import Optional, Dict, Any
from flask import request, has_request_context

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def get_request_context() -> Dict[str, Any]:
    """
    Extract request context information safely.
    
    Returns:
        Dictionary with request context (method, path, endpoint, query params, etc.)
    """
    context = {}
    
    if not has_request_context():
        return context
    
    try:
        context = {
            "method": request.method,
            "path": request.path,
            "endpoint": request.endpoint or "unknown",
            "url": request.url,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
        }
        
        # Add query parameters (excluding sensitive data)
        if request.args:
            query_params = dict(request.args)
            # Remove sensitive parameters
            sensitive_keys = ["access_key", "secret_key", "password", "token"]
            for key in sensitive_keys:
                query_params.pop(key, None)
            context["query_params"] = query_params
        
        # Add request data for POST/PUT requests (excluding sensitive data)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                if request.is_json:
                    data = request.get_json(silent=True) or {}
                    # Remove sensitive fields
                    sensitive_fields = ["access_key", "secret_key", "password", "token"]
                    safe_data = {
                        k: v for k, v in data.items()
                        if k not in sensitive_fields
                    }
                    if safe_data:
                        context["request_data"] = safe_data
            except Exception:
                pass  # Ignore errors when extracting request data
        
        # Try to get user/session info if available
        try:
            session = getattr(request, 'session', None)
            if session:
                session_info = {}
                if hasattr(session, 'user_id'):
                    session_info["user_id"] = session.user_id
                if hasattr(session, 'account_id'):
                    session_info["account_id"] = session.account_id
                if hasattr(session, 'region'):
                    session_info["region"] = session.region
                if session_info:
                    context["session"] = session_info
        except Exception:
            pass  # Ignore errors when extracting session info
            
    except Exception as e:
        # If we can't extract context, log that fact
        context["context_extraction_error"] = str(e)
    
    return context


def log_exception(
    exception: Exception,
    status_code: Optional[int] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an exception with full context including stack trace and request information.
    
    Args:
        exception: The exception to log
        status_code: Optional HTTP status code (for APIError)
        additional_context: Optional additional context to include in log
    """
    try:
        # Get request context
        request_context = get_request_context()
        
        # Build log data
        log_data = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "status_code": status_code,
        }
        
        # Add stack trace (use exception's traceback if available)
        if hasattr(exception, '__traceback__') and exception.__traceback__:
            log_data["stack_trace"] = ''.join(
                traceback.format_exception(
                    type(exception),
                    exception,
                    exception.__traceback__
                )
            )
        else:
            # Fallback if traceback is not available
            log_data["stack_trace"] = traceback.format_exc()
        
        # Add request context
        if request_context:
            log_data["request"] = request_context
        
        # Add any additional context
        if additional_context:
            log_data.update(additional_context)
        
        # Log at ERROR level (will go to both app.log and errors.log)
        logger.error(
            f"Exception occurred: {type(exception).__name__}: {str(exception)}",
            extra=log_data
        )
        
    except Exception as log_error:
        # If logging itself fails, try to log to stderr as fallback
        try:
            import sys
            print(
                f"CRITICAL: Failed to log exception: {log_error}",
                f"Original exception: {exception}",
                file=sys.stderr
            )
        except Exception:
            pass  # If even stderr fails, give up silently


def log_error_message(
    message: str,
    status_code: Optional[int] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error message (not an exception) with request context.
    
    Args:
        message: Error message to log
        status_code: Optional HTTP status code
        additional_context: Optional additional context to include in log
    """
    try:
        request_context = get_request_context()
        
        log_data = {
            "error_message": message,
            "status_code": status_code,
        }
        
        if request_context:
            log_data["request"] = request_context
        
        if additional_context:
            log_data.update(additional_context)
        
        logger.error(message, extra=log_data)
        
    except Exception as log_error:
        try:
            import sys
            print(
                f"CRITICAL: Failed to log error message: {log_error}",
                f"Original message: {message}",
                file=sys.stderr
            )
        except Exception:
            pass

