"""API call logging utilities for osc_sdk_python Gateway."""
import json
import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

from osc_sdk_python import Gateway

from backend.config.settings import (
    ENABLE_API_CALL_LOGGING,
    LOG_FILE_PATH,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT,
    API_CALLS_LOG_FILE
)

# Try to import log constants from osc_sdk_python
# Constants may be in different locations depending on SDK version
try:
    from osc_sdk_python.log import LOG_MEMORY, LOG_STDIO, LOG_STDERR, LOG_ALL, LOG_KEEP_ONLY_LAST_REQ
except ImportError:
    try:
        # Try importing from Gateway class attributes
        from osc_sdk_python import Gateway as GatewayClass
        LOG_MEMORY = getattr(GatewayClass, 'LOG_MEMORY', 1)
        LOG_STDIO = getattr(GatewayClass, 'LOG_STDIO', 2)
        LOG_STDERR = getattr(GatewayClass, 'LOG_STDERR', 4)
        LOG_ALL = getattr(GatewayClass, 'LOG_ALL', 1)
        LOG_KEEP_ONLY_LAST_REQ = getattr(GatewayClass, 'LOG_KEEP_ONLY_LAST_REQ', 0)
    except (AttributeError, ImportError):
        # Fallback: define constants if not available in this version
        # These are typically bit flags
        LOG_MEMORY = 1
        LOG_STDIO = 2
        LOG_STDERR = 4
        LOG_ALL = 1
        LOG_KEEP_ONLY_LAST_REQ = 0

# Global logger instance for API calls
_api_call_logger = None


def _get_api_call_logger():
    """Get or create the API call logger."""
    global _api_call_logger
    
    if _api_call_logger is not None:
        return _api_call_logger
    
    if not ENABLE_API_CALL_LOGGING:
        return None
    
    # Ensure log directory exists
    log_dir = Path(LOG_FILE_PATH)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("osc_finops.api_calls")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create JSON formatter
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        timestamp=True
    )
    
    # Create rotating file handler for API calls
    api_log_path = log_dir / API_CALLS_LOG_FILE
    api_handler = RotatingFileHandler(
        api_log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(json_formatter)
    logger.addHandler(api_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    _api_call_logger = logger
    return logger


def _sanitize_sensitive_data(data: Any) -> Any:
    """
    Recursively sanitize sensitive data from dictionaries/lists.
    
    Args:
        data: Data structure to sanitize
    
    Returns:
        Sanitized data structure
    """
    if isinstance(data, dict):
        sanitized = {}
        sensitive_keys = ['access_key', 'secret_key', 'AccessKey', 'SecretKey', 
                         'X-Osc-Access-Key', 'X-Osc-Secret-Key', 'Authorization']
        for key, value in data.items():
            if any(sensitive in key for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = _sanitize_sensitive_data(value)
        return sanitized
    elif isinstance(data, list):
        return [_sanitize_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        # Check if string contains sensitive patterns
        if 'access_key' in data.lower() or 'secret_key' in data.lower():
            # Try to redact JSON-like structures
            try:
                parsed = json.loads(data)
                return json.dumps(_sanitize_sensitive_data(parsed))
            except (json.JSONDecodeError, TypeError):
                return "***REDACTED***"
    return data


def _parse_sdk_log(log_content: str) -> Optional[Dict[str, Any]]:
    """
    Parse SDK log content to extract request/response details.
    
    The SDK log format may vary, but typically contains:
    - Request: method, URL, headers, body
    - Response: status code, headers, body
    
    Args:
        log_content: Raw log content from gw.log.str()
    
    Returns:
        Parsed log data dictionary or None if parsing fails
    """
    if not log_content or not log_content.strip():
        return None
    
    parsed = {
        "request": {},
        "response": {}
    }
    
    # Try to extract HTTP method and URL
    method_match = re.search(r'(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)', log_content)
    if method_match:
        parsed["request"]["method"] = method_match.group(1)
        parsed["request"]["url"] = method_match.group(2)
    
    # Try to extract request headers
    request_headers_match = re.search(r'Request Headers:?\s*\n((?:[^\n]+\n?)+)', log_content, re.IGNORECASE)
    if request_headers_match:
        headers_text = request_headers_match.group(1)
        headers = {}
        for line in headers_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        parsed["request"]["headers"] = _sanitize_sensitive_data(headers)
    
    # Try to extract request body/payload
    request_body_match = re.search(r'Request Body:?\s*\n((?:[^\n]+\n?)+)', log_content, re.IGNORECASE | re.DOTALL)
    if request_body_match:
        body_text = request_body_match.group(1).strip()
        try:
            parsed_body = json.loads(body_text)
            parsed["request"]["payload"] = _sanitize_sensitive_data(parsed_body)
        except json.JSONDecodeError:
            parsed["request"]["payload"] = body_text
    
    # Try to extract response status code
    status_match = re.search(r'HTTP/\d\.\d\s+(\d{3})', log_content)
    if status_match:
        parsed["response"]["status_code"] = int(status_match.group(1))
    
    # Try to extract response headers
    response_headers_match = re.search(r'Response Headers:?\s*\n((?:[^\n]+\n?)+)', log_content, re.IGNORECASE)
    if response_headers_match:
        headers_text = response_headers_match.group(1)
        headers = {}
        for line in headers_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        parsed["response"]["headers"] = headers
    
    # Try to extract response body
    response_body_match = re.search(r'Response Body:?\s*\n((?:[^\n]+\n?)+)', log_content, re.IGNORECASE | re.DOTALL)
    if response_body_match:
        body_text = response_body_match.group(1).strip()
        try:
            parsed_body = json.loads(body_text)
            parsed["response"]["json"] = parsed_body
        except json.JSONDecodeError:
            parsed["response"]["body"] = body_text
    
    # If we couldn't parse much, store raw content
    if not parsed["request"] and not parsed["response"]:
        parsed["raw_log"] = log_content[:1000]  # Limit raw log size
    
    return parsed


def create_logged_gateway(access_key: str, secret_key: str, region: str) -> Gateway:
    """
    Create a Gateway instance with logging enabled.
    
    Args:
        access_key: Outscale access key
        secret_key: Outscale secret key
        region: Region name
    
    Returns:
        Configured Gateway instance with logging enabled
    """
    gateway = Gateway(
        access_key=access_key,
        secret_key=secret_key,
        region=region
    )
    
    if ENABLE_API_CALL_LOGGING:
        # Configure logging to capture all requests/responses in memory
        try:
            gateway.log.config(type=LOG_MEMORY, what=LOG_ALL)
        except (AttributeError, TypeError) as e:
            # If log.config doesn't exist or constants are wrong, log warning but continue
            logger = _get_api_call_logger()
            if logger:
                logger.warning(f"Failed to configure Gateway logging: {e}")
    
    return gateway


def log_api_call(gateway: Gateway, api_method: str, **kwargs) -> None:
    """
    Extract and log API call details from Gateway log.
    
    Args:
        gateway: Gateway instance that made the API call
        api_method: Name of the API method called (e.g., "ReadConsumptionAccount")
        **kwargs: Additional context to include in log
    """
    if not ENABLE_API_CALL_LOGGING:
        return
    
    logger = _get_api_call_logger()
    if not logger:
        return
    
    try:
        # Get log content from Gateway
        log_content = gateway.log.str()
        
        if not log_content:
            return
        
        # Parse log content
        parsed_log = _parse_sdk_log(log_content)
        
        # Build log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "api_method": api_method,
            "region": kwargs.get("region", "unknown"),
        }
        
        if parsed_log:
            log_entry.update(parsed_log)
        else:
            # If parsing failed, include raw log (truncated)
            log_entry["raw_log"] = log_content[:2000]  # Limit size
        
        # Add any additional context
        for key, value in kwargs.items():
            if key not in ["region"]:  # Already included
                log_entry[key] = value
        
        # Log the entry
        logger.info(
            f"API call: {api_method}",
            extra={"api_call": log_entry}
        )
        
    except Exception as e:
        # Don't let logging errors break the application
        if logger:
            logger.warning(f"Failed to log API call: {e}")


def process_and_log_api_call(gateway: Gateway, api_method: str, call_func, *args, **kwargs) -> Any:
    """
    Execute an API call and log the request/response details.
    
    This is a wrapper that:
    1. Makes the API call
    2. Extracts log content
    3. Logs the details
    4. Returns the response
    
    Args:
        gateway: Gateway instance
        api_method: Name of the API method (e.g., "ReadConsumptionAccount")
        call_func: Function to call (e.g., gateway.ReadConsumptionAccount)
        *args: Arguments to pass to call_func
        **kwargs: Additional context for logging
    
    Returns:
        Response from the API call
    """
    # Make the API call
    response = call_func(*args)
    
    # Extract region from gateway if available
    region = getattr(gateway, 'region', kwargs.get('region', 'unknown'))
    
    # Log the API call
    log_api_call(gateway, api_method, region=region, **kwargs)
    
    return response

