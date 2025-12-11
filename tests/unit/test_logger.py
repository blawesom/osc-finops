"""Unit tests for backend.utils.logger."""
import pytest
import os
import logging
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from backend.utils.logger import setup_logging, get_logger


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    @patch('backend.utils.logger.Path')
    @patch('backend.utils.logger.RotatingFileHandler')
    @patch('backend.utils.logger.jsonlogger.JsonFormatter')
    @patch('backend.utils.logger.logging.getLogger')
    def test_setup_logging_creates_log_directory(self, mock_get_logger, mock_formatter, 
                                                  mock_handler, mock_path_class):
        """Test that setup_logging creates log directory."""
        mock_log_dir = Mock()
        # Make Path return the mock when called, and support division operator
        mock_path_class.return_value = mock_log_dir
        # Mock the division operator for Path objects
        type(mock_log_dir).__truediv__ = Mock(return_value=mock_log_dir)
        
        setup_logging()
        
        mock_path_class.assert_called()
        mock_log_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    @patch('backend.utils.logger.Path')
    @patch('backend.utils.logger.RotatingFileHandler')
    @patch('backend.utils.logger.jsonlogger.JsonFormatter')
    @patch('backend.utils.logger.logging.getLogger')
    def test_setup_logging_configures_root_logger(self, mock_get_logger, mock_formatter,
                                                   mock_handler, mock_path_class):
        """Test that setup_logging configures root logger."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        setup_logging()
        
        mock_get_logger.assert_called()
        mock_logger.setLevel.assert_called()
        mock_logger.handlers.clear.assert_called_once()
    
    @patch('backend.utils.logger.Path')
    @patch('backend.utils.logger.RotatingFileHandler')
    @patch('backend.utils.logger.jsonlogger.JsonFormatter')
    @patch('backend.utils.logger.logging.getLogger')
    @patch('backend.utils.logger.logging.StreamHandler')
    @patch.dict(os.environ, {'FLASK_ENV': 'development'})
    def test_setup_logging_adds_console_handler_in_dev(self, mock_stream_handler,
                                                        mock_get_logger, mock_formatter,
                                                        mock_handler, mock_path_class):
        """Test that setup_logging adds console handler in development."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_console = Mock()
        mock_stream_handler.return_value = mock_console
        
        setup_logging()
        
        mock_stream_handler.assert_called_once()
        mock_logger.addHandler.assert_any_call(mock_console)
    
    @patch('backend.utils.logger.Path')
    @patch('backend.utils.logger.RotatingFileHandler')
    @patch('backend.utils.logger.jsonlogger.JsonFormatter')
    @patch('backend.utils.logger.logging.getLogger')
    @patch('backend.utils.logger.logging.StreamHandler')
    @patch.dict(os.environ, {'FLASK_ENV': 'production'}, clear=False)
    def test_setup_logging_no_console_handler_in_production(self, mock_stream_handler,
                                                             mock_get_logger, mock_formatter,
                                                             mock_handler, mock_path_class):
        """Test that setup_logging doesn't add console handler in production."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        setup_logging()
        
        # StreamHandler should not be called in production
        mock_stream_handler.assert_not_called()
    
    @patch('backend.utils.logger.Path')
    @patch('backend.utils.logger.RotatingFileHandler')
    @patch('backend.utils.logger.jsonlogger.JsonFormatter')
    @patch('backend.utils.logger.logging.getLogger')
    def test_setup_logging_creates_app_and_error_handlers(self, mock_get_logger, mock_formatter,
                                                           mock_handler, mock_path_class):
        """Test that setup_logging creates both app and error log handlers."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        setup_logging()
        
        # Should create two RotatingFileHandlers (app log and error log)
        assert mock_handler.call_count == 2
        mock_logger.addHandler.assert_called()
    
    @patch('backend.utils.logger.Path')
    @patch('backend.utils.logger.RotatingFileHandler')
    @patch('backend.utils.logger.jsonlogger.JsonFormatter')
    @patch('backend.utils.logger.logging.getLogger')
    def test_setup_logging_returns_logger(self, mock_get_logger, mock_formatter,
                                          mock_handler, mock_path_class):
        """Test that setup_logging returns the root logger."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        result = setup_logging()
        
        assert result == mock_logger


class TestGetLogger:
    """Tests for get_logger function."""
    
    @patch('backend.utils.logger.logging.getLogger')
    def test_get_logger_with_name(self, mock_get_logger):
        """Test getting logger with a specific name."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        result = get_logger("test.module")
        
        mock_get_logger.assert_called_once_with("test.module")
        assert result == mock_logger
    
    @patch('backend.utils.logger.logging.getLogger')
    def test_get_logger_without_name(self, mock_get_logger):
        """Test getting logger without name (returns root logger)."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        result = get_logger()
        
        mock_get_logger.assert_called_once_with()
        assert result == mock_logger
    
    @patch('backend.utils.logger.logging.getLogger')
    def test_get_logger_with_none_name(self, mock_get_logger):
        """Test getting logger with None name."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        result = get_logger(None)
        
        mock_get_logger.assert_called_once_with()
        assert result == mock_logger

