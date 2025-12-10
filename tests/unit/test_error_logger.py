"""Unit tests for backend.utils.error_logger."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, request
import traceback

from backend.utils.error_logger import (
    get_request_context,
    log_exception,
    log_error_message
)


class TestGetRequestContext:
    """Tests for get_request_context function."""
    
    def test_get_request_context_without_request(self):
        """Test when there's no Flask request context."""
        context = get_request_context()
        assert context == {}
    
    def test_get_request_context_with_request(self):
        """Test extracting context from Flask request."""
        app = Flask(__name__)
        
        with app.test_request_context('/test/path?param=value', method='GET'):
            context = get_request_context()
            
            assert context["method"] == "GET"
            assert context["path"] == "/test/path"
            assert "param" in context.get("query_params", {})
            assert context["query_params"]["param"] == "value"
    
    def test_get_request_context_removes_sensitive_query_params(self):
        """Test that sensitive query parameters are removed."""
        app = Flask(__name__)
        
        with app.test_request_context(
            '/test?access_key=secret&secret_key=key&param=value',
            method='GET'
        ):
            context = get_request_context()
            
            assert "access_key" not in context.get("query_params", {})
            assert "secret_key" not in context.get("query_params", {})
            assert "param" in context.get("query_params", {})
    
    def test_get_request_context_with_post_data(self):
        """Test extracting context from POST request."""
        app = Flask(__name__)
        
        with app.test_request_context(
            '/test',
            method='POST',
            json={"name": "test", "value": 123}
        ):
            context = get_request_context()
            
            assert context["method"] == "POST"
            assert "request_data" in context
            assert context["request_data"]["name"] == "test"
            assert context["request_data"]["value"] == 123
    
    def test_get_request_context_removes_sensitive_post_data(self):
        """Test that sensitive POST data is removed."""
        app = Flask(__name__)
        
        with app.test_request_context(
            '/test',
            method='POST',
            json={
                "name": "test",
                "access_key": "secret",
                "secret_key": "key",
                "password": "pass"
            }
        ):
            context = get_request_context()
            
            assert "request_data" in context
            assert "name" in context["request_data"]
            assert "access_key" not in context["request_data"]
            assert "secret_key" not in context["request_data"]
            assert "password" not in context["request_data"]
    
    def test_get_request_context_with_session(self):
        """Test extracting session information."""
        app = Flask(__name__)
        
        with app.test_request_context('/test', method='GET'):
            # Mock session on request
            mock_session = Mock()
            mock_session.user_id = "user-123"
            mock_session.region = "eu-west-2"
            request.session = mock_session
            
            context = get_request_context()
            
            assert "session" in context
            assert context["session"]["user_id"] == "user-123"
            assert context["session"]["region"] == "eu-west-2"
    
    def test_get_request_context_handles_exception(self):
        """Test that exceptions during context extraction are handled."""
        app = Flask(__name__)
        
        with app.test_request_context('/test', method='GET'):
            # Make request.method raise an exception
            with patch.object(request, 'method', side_effect=Exception("Test error")):
                context = get_request_context()
                
                # Should return context with error info or empty dict
                assert isinstance(context, dict)


class TestLogException:
    """Tests for log_exception function."""
    
    @patch('backend.utils.error_logger.logger')
    def test_log_exception_basic(self, mock_logger):
        """Test logging a basic exception."""
        exception = ValueError("Test error message")
        
        log_exception(exception)
        
        # Verify logger.error was called
        assert mock_logger.error.called
        call_args = mock_logger.error.call_args
        
        # Check log message
        assert "Exception occurred" in call_args[0][0]
        assert "ValueError" in call_args[0][0]
        
        # Check extra data
        extra_data = call_args[1]["extra"]
        assert extra_data["exception_type"] == "ValueError"
        assert extra_data["exception_message"] == "Test error message"
        assert "stack_trace" in extra_data
    
    @patch('backend.utils.error_logger.logger')
    def test_log_exception_with_status_code(self, mock_logger):
        """Test logging exception with status code."""
        exception = ValueError("Test error")
        
        log_exception(exception, status_code=404)
        
        call_args = mock_logger.error.call_args
        extra_data = call_args[1]["extra"]
        assert extra_data["status_code"] == 404
    
    @patch('backend.utils.error_logger.logger')
    def test_log_exception_with_additional_context(self, mock_logger):
        """Test logging exception with additional context."""
        exception = ValueError("Test error")
        additional_context = {"custom_field": "custom_value", "error_code": "ERR001"}
        
        log_exception(exception, additional_context=additional_context)
        
        call_args = mock_logger.error.call_args
        extra_data = call_args[1]["extra"]
        assert extra_data["custom_field"] == "custom_value"
        assert extra_data["error_code"] == "ERR001"
    
    @patch('backend.utils.error_logger.logger')
    def test_log_exception_with_request_context(self, mock_logger):
        """Test logging exception with Flask request context."""
        app = Flask(__name__)
        exception = ValueError("Test error")
        
        with app.test_request_context('/test/path', method='GET'):
            log_exception(exception)
            
            call_args = mock_logger.error.call_args
            extra_data = call_args[1]["extra"]
            assert "request" in extra_data
            assert extra_data["request"]["method"] == "GET"
            assert extra_data["request"]["path"] == "/test/path"
    
    @patch('backend.utils.error_logger.logger')
    def test_log_exception_with_traceback(self, mock_logger):
        """Test that stack trace is included in log."""
        try:
            raise ValueError("Test error with traceback")
        except ValueError as e:
            exception = e
        
        log_exception(exception)
        
        call_args = mock_logger.error.call_args
        extra_data = call_args[1]["extra"]
        assert "stack_trace" in extra_data
        assert "ValueError" in extra_data["stack_trace"]
        assert "Test error with traceback" in extra_data["stack_trace"]
    
    @patch('backend.utils.error_logger.logger')
    def test_log_exception_handles_logging_failure(self, mock_logger):
        """Test that logging failure is handled gracefully."""
        exception = ValueError("Test error")
        
        # Make logger.error raise an exception
        mock_logger.error.side_effect = Exception("Logger error")
        
        # Should not raise exception, should try stderr fallback
        with patch('sys.stderr') as mock_stderr:
            log_exception(exception)
            # Should attempt to write to stderr
            # (We can't easily verify this without more complex mocking)
    
    @patch('backend.utils.error_logger.logger')
    def test_log_exception_different_exception_types(self, mock_logger):
        """Test logging different exception types."""
        exceptions = [
            ValueError("Value error"),
            KeyError("key"),
            TypeError("Type error"),
            RuntimeError("Runtime error"),
        ]
        
        for exc in exceptions:
            log_exception(exc)
            call_args = mock_logger.error.call_args
            extra_data = call_args[1]["extra"]
            assert extra_data["exception_type"] == type(exc).__name__
            assert extra_data["exception_message"] == str(exc)


class TestLogErrorMessage:
    """Tests for log_error_message function."""
    
    @patch('backend.utils.error_logger.logger')
    def test_log_error_message_basic(self, mock_logger):
        """Test logging a basic error message."""
        message = "Test error message"
        
        log_error_message(message)
        
        # Verify logger.error was called
        assert mock_logger.error.called
        call_args = mock_logger.error.call_args
        
        # Check log message
        assert call_args[0][0] == message
        
        # Check extra data
        extra_data = call_args[1]["extra"]
        assert extra_data["error_message"] == message
    
    @patch('backend.utils.error_logger.logger')
    def test_log_error_message_with_status_code(self, mock_logger):
        """Test logging error message with status code."""
        message = "Test error"
        
        log_error_message(message, status_code=500)
        
        call_args = mock_logger.error.call_args
        extra_data = call_args[1]["extra"]
        assert extra_data["status_code"] == 500
    
    @patch('backend.utils.error_logger.logger')
    def test_log_error_message_with_additional_context(self, mock_logger):
        """Test logging error message with additional context."""
        message = "Test error"
        additional_context = {"error_type": "VALIDATION", "field": "email"}
        
        log_error_message(message, additional_context=additional_context)
        
        call_args = mock_logger.error.call_args
        extra_data = call_args[1]["extra"]
        assert extra_data["error_type"] == "VALIDATION"
        assert extra_data["field"] == "email"
    
    @patch('backend.utils.error_logger.logger')
    def test_log_error_message_with_request_context(self, mock_logger):
        """Test logging error message with Flask request context."""
        app = Flask(__name__)
        message = "Test error"
        
        with app.test_request_context('/api/test', method='POST'):
            log_error_message(message)
            
            call_args = mock_logger.error.call_args
            extra_data = call_args[1]["extra"]
            assert "request" in extra_data
            assert extra_data["request"]["method"] == "POST"
            assert extra_data["request"]["path"] == "/api/test"
    
    @patch('backend.utils.error_logger.logger')
    def test_log_error_message_handles_logging_failure(self, mock_logger):
        """Test that logging failure is handled gracefully."""
        message = "Test error"
        
        # Make logger.error raise an exception
        mock_logger.error.side_effect = Exception("Logger error")
        
        # Should not raise exception
        with patch('sys.stderr'):
            log_error_message(message)
            # Should attempt to write to stderr as fallback
