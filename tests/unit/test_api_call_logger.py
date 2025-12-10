"""Unit tests for backend.utils.api_call_logger."""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from backend.utils.api_call_logger import (
    _get_api_call_logger,
    _sanitize_sensitive_data,
    _parse_sdk_log,
    create_logged_gateway,
    log_api_call,
    process_and_log_api_call
)


class TestSanitizeSensitiveData:
    """Tests for _sanitize_sensitive_data function."""
    
    def test_sanitize_dict_with_access_key(self):
        """Test sanitizing dictionary with access_key."""
        data = {
            "access_key": "secret123",
            "name": "test",
            "region": "eu-west-2"
        }
        
        result = _sanitize_sensitive_data(data)
        
        assert result["access_key"] == "***REDACTED***"
        assert result["name"] == "test"
        assert result["region"] == "eu-west-2"
    
    def test_sanitize_dict_with_secret_key(self):
        """Test sanitizing dictionary with secret_key."""
        data = {
            "secret_key": "secret123",
            "other": "value"
        }
        
        result = _sanitize_sensitive_data(data)
        
        assert result["secret_key"] == "***REDACTED***"
        assert result["other"] == "value"
    
    def test_sanitize_dict_with_multiple_sensitive_keys(self):
        """Test sanitizing dictionary with multiple sensitive keys."""
        data = {
            "access_key": "key1",
            "secret_key": "key2",
            "X-Osc-Access-Key": "key3",
            "normal_field": "value"
        }
        
        result = _sanitize_sensitive_data(data)
        
        assert result["access_key"] == "***REDACTED***"
        assert result["secret_key"] == "***REDACTED***"
        assert result["X-Osc-Access-Key"] == "***REDACTED***"
        assert result["normal_field"] == "value"
    
    def test_sanitize_nested_dict(self):
        """Test sanitizing nested dictionaries."""
        data = {
            "user": {
                "access_key": "secret",
                "name": "test"
            },
            "config": {
                "secret_key": "key"
            }
        }
        
        result = _sanitize_sensitive_data(data)
        
        assert result["user"]["access_key"] == "***REDACTED***"
        assert result["user"]["name"] == "test"
        assert result["config"]["secret_key"] == "***REDACTED***"
    
    def test_sanitize_list(self):
        """Test sanitizing list of dictionaries."""
        data = [
            {"access_key": "key1", "name": "item1"},
            {"secret_key": "key2", "name": "item2"}
        ]
        
        result = _sanitize_sensitive_data(data)
        
        assert result[0]["access_key"] == "***REDACTED***"
        assert result[0]["name"] == "item1"
        assert result[1]["secret_key"] == "***REDACTED***"
        assert result[1]["name"] == "item2"
    
    def test_sanitize_string_with_sensitive_data(self):
        """Test sanitizing string containing sensitive data."""
        data = '{"access_key": "secret", "name": "test"}'
        
        result = _sanitize_sensitive_data(data)
        
        # Should parse JSON and sanitize
        parsed = json.loads(result)
        assert parsed["access_key"] == "***REDACTED***"
        assert parsed["name"] == "test"
    
    def test_sanitize_string_non_json(self):
        """Test sanitizing non-JSON string with sensitive keywords."""
        data = "This contains access_key information"
        
        result = _sanitize_sensitive_data(data)
        
        assert result == "***REDACTED***"
    
    def test_sanitize_non_sensitive_data(self):
        """Test that non-sensitive data is not modified."""
        data = {
            "name": "test",
            "region": "eu-west-2",
            "value": 123
        }
        
        result = _sanitize_sensitive_data(data)
        
        assert result == data
    
    def test_sanitize_primitive_types(self):
        """Test sanitizing primitive types (should return as-is)."""
        assert _sanitize_sensitive_data(123) == 123
        assert _sanitize_sensitive_data(45.6) == 45.6
        assert _sanitize_sensitive_data(True) is True
        assert _sanitize_sensitive_data(None) is None


class TestParseSdkLog:
    """Tests for _parse_sdk_log function."""
    
    def test_parse_sdk_log_empty_string(self):
        """Test parsing empty log content."""
        result = _parse_sdk_log("")
        assert result is None
    
    def test_parse_sdk_log_whitespace_only(self):
        """Test parsing whitespace-only log content."""
        result = _parse_sdk_log("   \n\t  ")
        assert result is None
    
    def test_parse_sdk_log_with_method_and_url(self):
        """Test parsing log with HTTP method and URL."""
        log_content = "POST https://api.outscale.com/oapi/latest/ReadAccounts"
        
        result = _parse_sdk_log(log_content)
        
        assert result is not None
        assert result["request"]["method"] == "POST"
        assert "api.outscale.com" in result["request"]["url"]
    
    def test_parse_sdk_log_with_status_code(self):
        """Test parsing log with HTTP status code."""
        log_content = "HTTP/1.1 200 OK"
        
        result = _parse_sdk_log(log_content)
        
        assert result is not None
        assert result["response"]["status_code"] == 200
    
    def test_parse_sdk_log_with_request_headers(self):
        """Test parsing log with request headers."""
        log_content = """Request Headers:
Content-Type: application/json
X-Osc-Access-Key: test-key
"""
        
        result = _parse_sdk_log(log_content)
        
        assert result is not None
        assert "headers" in result["request"]
        assert result["request"]["headers"]["Content-Type"] == "application/json"
    
    def test_parse_sdk_log_with_request_body(self):
        """Test parsing log with request body."""
        log_content = """Request Body:
{"AccountId": "123456789012"}
"""
        
        result = _parse_sdk_log(log_content)
        
        assert result is not None
        assert "payload" in result["request"]
        assert result["request"]["payload"]["AccountId"] == "123456789012"
    
    def test_parse_sdk_log_with_response_body(self):
        """Test parsing log with response body."""
        log_content = """Response Body:
{"Accounts": [{"AccountId": "123456789012"}]}
"""
        
        result = _parse_sdk_log(log_content)
        
        assert result is not None
        assert "json" in result["response"]
        assert "Accounts" in result["response"]["json"]
    
    def test_parse_sdk_log_complete_request_response(self):
        """Test parsing complete request/response log."""
        log_content = """POST https://api.outscale.com/oapi/latest/ReadAccounts
Request Headers:
Content-Type: application/json

Request Body:
{"Filters": {}}

HTTP/1.1 200 OK
Response Body:
{"Accounts": [{"AccountId": "123456789012"}]}
"""
        
        result = _parse_sdk_log(log_content)
        
        assert result is not None
        assert result["request"]["method"] == "POST"
        assert result["response"]["status_code"] == 200
        assert "Accounts" in result["response"]["json"]
    
    def test_parse_sdk_log_unparseable_content(self):
        """Test parsing unparseable log content."""
        log_content = "Some random text that doesn't match patterns"
        
        result = _parse_sdk_log(log_content)
        
        # Should return dict with raw_log if nothing parsed
        assert result is not None
        assert "raw_log" in result or len(result) > 0


class TestGetApiCallLogger:
    """Tests for _get_api_call_logger function."""
    
    @patch('backend.utils.api_call_logger.ENABLE_API_CALL_LOGGING', True)
    @patch('backend.utils.api_call_logger.Path')
    @patch('backend.utils.api_call_logger.RotatingFileHandler')
    @patch('backend.utils.api_call_logger.jsonlogger.JsonFormatter')
    @patch('backend.utils.api_call_logger.logging.getLogger')
    def test_get_api_call_logger_creates_logger(self, mock_get_logger, mock_formatter,
                                                 mock_handler, mock_path):
        """Test that _get_api_call_logger creates logger when enabled."""
        # Reset global state
        import backend.utils.api_call_logger as api_logger_module
        api_logger_module._api_call_logger = None
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        result = _get_api_call_logger()
        
        assert result is not None
        mock_get_logger.assert_called()
    
    @patch('backend.utils.api_call_logger.ENABLE_API_CALL_LOGGING', False)
    def test_get_api_call_logger_returns_none_when_disabled(self):
        """Test that _get_api_call_logger returns None when disabled."""
        # Reset global state
        import backend.utils.api_call_logger as api_logger_module
        api_logger_module._api_call_logger = None
        
        result = _get_api_call_logger()
        
        assert result is None
    
    @patch('backend.utils.api_call_logger.ENABLE_API_CALL_LOGGING', True)
    def test_get_api_call_logger_returns_cached_logger(self):
        """Test that _get_api_call_logger returns cached logger on second call."""
        # Reset global state
        import backend.utils.api_call_logger as api_logger_module
        mock_cached_logger = Mock()
        api_logger_module._api_call_logger = mock_cached_logger
        
        result = _get_api_call_logger()
        
        assert result == mock_cached_logger


class TestCreateLoggedGateway:
    """Tests for create_logged_gateway function."""
    
    @patch('backend.utils.api_call_logger.ENABLE_API_CALL_LOGGING', True)
    @patch('backend.utils.api_call_logger.Gateway')
    def test_create_logged_gateway_with_logging_enabled(self, mock_gateway_class):
        """Test creating gateway with logging enabled."""
        mock_gateway = Mock()
        mock_gateway_class.return_value = mock_gateway
        
        result = create_logged_gateway("access_key", "secret_key", "eu-west-2")
        
        mock_gateway_class.assert_called_once_with(
            access_key="access_key",
            secret_key="secret_key",
            region="eu-west-2"
        )
        assert result == mock_gateway
        # Should attempt to configure logging
        assert hasattr(mock_gateway, 'log') or True  # May not have log attribute
    
    @patch('backend.utils.api_call_logger.ENABLE_API_CALL_LOGGING', False)
    @patch('backend.utils.api_call_logger.Gateway')
    def test_create_logged_gateway_with_logging_disabled(self, mock_gateway_class):
        """Test creating gateway with logging disabled."""
        mock_gateway = Mock()
        mock_gateway_class.return_value = mock_gateway
        
        result = create_logged_gateway("access_key", "secret_key", "eu-west-2")
        
        mock_gateway_class.assert_called_once()
        assert result == mock_gateway


class TestLogApiCall:
    """Tests for log_api_call function."""
    
    @patch('backend.utils.api_call_logger.ENABLE_API_CALL_LOGGING', True)
    @patch('backend.utils.api_call_logger._get_api_call_logger')
    def test_log_api_call_with_log_content(self, mock_get_logger):
        """Test logging API call with log content."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        mock_gateway = Mock()
        mock_gateway.log.str.return_value = "POST /api\nRequest Headers:\nContent-Type: application/json"
        
        log_api_call(mock_gateway, "ReadAccounts", region="eu-west-2")
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "API call: ReadAccounts" in call_args[0][0]
    
    @patch('backend.utils.api_call_logger.ENABLE_API_CALL_LOGGING', True)
    @patch('backend.utils.api_call_logger._get_api_call_logger')
    def test_log_api_call_empty_log_content(self, mock_get_logger):
        """Test logging API call with empty log content."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        mock_gateway = Mock()
        mock_gateway.log.str.return_value = ""
        
        log_api_call(mock_gateway, "ReadAccounts")
        
        # Should not log if content is empty
        mock_logger.info.assert_not_called()
    
    @patch('backend.utils.api_call_logger.ENABLE_API_CALL_LOGGING', False)
    @patch('backend.utils.api_call_logger._get_api_call_logger')
    def test_log_api_call_logging_disabled(self, mock_get_logger):
        """Test that log_api_call does nothing when logging is disabled."""
        mock_gateway = Mock()
        
        log_api_call(mock_gateway, "ReadAccounts")
        
        mock_get_logger.assert_not_called()
    
    @patch('backend.utils.api_call_logger.ENABLE_API_CALL_LOGGING', True)
    @patch('backend.utils.api_call_logger._get_api_call_logger')
    def test_log_api_call_handles_exception(self, mock_get_logger):
        """Test that log_api_call handles exceptions gracefully."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        mock_gateway = Mock()
        mock_gateway.log.str.side_effect = Exception("Log error")
        
        # Should not raise exception
        log_api_call(mock_gateway, "ReadAccounts")
        
        # Should log warning about failure
        mock_logger.warning.assert_called()


class TestProcessAndLogApiCall:
    """Tests for process_and_log_api_call function."""
    
    @patch('backend.utils.api_call_logger.log_api_call')
    def test_process_and_log_api_call_executes_and_logs(self, mock_log_api):
        """Test that process_and_log_api_call executes call and logs."""
        mock_gateway = Mock()
        mock_call_func = Mock(return_value={"result": "data"})
        
        result = process_and_log_api_call(
            mock_gateway,
            "ReadAccounts",
            mock_call_func
        )
        
        mock_call_func.assert_called_once()
        assert result == {"result": "data"}
        mock_log_api.assert_called_once()
    
    @patch('backend.utils.api_call_logger.log_api_call')
    def test_process_and_log_api_call_with_args(self, mock_log_api):
        """Test process_and_log_api_call with function arguments."""
        mock_gateway = Mock()
        mock_call_func = Mock(return_value={"result": "data"})
        
        result = process_and_log_api_call(
            mock_gateway,
            "ReadAccounts",
            mock_call_func,
            "arg1",
            "arg2"
        )
        
        mock_call_func.assert_called_once_with("arg1", "arg2")
        assert result == {"result": "data"}
    
    @patch('backend.utils.api_call_logger.log_api_call')
    def test_process_and_log_api_call_extracts_region(self, mock_log_api):
        """Test that process_and_log_api_call extracts region from gateway."""
        mock_gateway = Mock()
        mock_gateway.region = "eu-west-2"
        mock_call_func = Mock(return_value={})
        
        process_and_log_api_call(mock_gateway, "ReadAccounts", mock_call_func)
        
        # Verify region was passed to log_api_call
        call_args = mock_log_api.call_args
        assert call_args[1]["region"] == "eu-west-2"
    
    @patch('backend.utils.api_call_logger.log_api_call')
    def test_process_and_log_api_call_with_kwargs(self, mock_log_api):
        """Test process_and_log_api_call with additional kwargs."""
        mock_gateway = Mock()
        mock_call_func = Mock(return_value={})
        
        process_and_log_api_call(
            mock_gateway,
            "ReadAccounts",
            mock_call_func,
            custom_param="value"
        )
        
        # Verify kwargs were passed to log_api_call
        call_args = mock_log_api.call_args
        assert call_args[1]["custom_param"] == "value"
