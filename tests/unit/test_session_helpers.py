"""Unit tests for backend.utils.session_helpers."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, request
import uuid

from backend.utils.session_helpers import (
    get_user_id_from_session,
    get_account_id_from_session
)


class TestGetUserIdFromSession:
    """Tests for get_user_id_from_session function."""
    
    def test_get_user_id_with_valid_session(self):
        """Test getting user_id from valid session."""
        app = Flask(__name__)
        test_user_id = str(uuid.uuid4())
        
        with app.test_request_context():
            # Mock session object on request
            mock_session = Mock()
            mock_session.user_id = test_user_id
            request.session = mock_session
            
            result = get_user_id_from_session()
            assert result == test_user_id
    
    def test_get_user_id_no_session_on_request(self):
        """Test when request has no session attribute."""
        app = Flask(__name__)
        
        with app.test_request_context():
            # Ensure request has no session attribute
            if hasattr(request, 'session'):
                delattr(request, 'session')
            
            result = get_user_id_from_session()
            assert result is None
    
    def test_get_user_id_session_is_none(self):
        """Test when request.session is None."""
        app = Flask(__name__)
        
        with app.test_request_context():
            request.session = None
            
            result = get_user_id_from_session()
            assert result is None
    
    def test_get_user_id_session_without_user_id(self):
        """Test when session exists but has no user_id attribute."""
        app = Flask(__name__)
        
        with app.test_request_context():
            mock_session = Mock()
            # Don't set user_id attribute
            delattr(mock_session, 'user_id') if hasattr(mock_session, 'user_id') else None
            request.session = mock_session
            
            result = get_user_id_from_session()
            assert result is None
    
    def test_get_user_id_session_with_none_user_id(self):
        """Test when session has user_id set to None."""
        app = Flask(__name__)
        
        with app.test_request_context():
            mock_session = Mock()
            mock_session.user_id = None
            request.session = mock_session
            
            result = get_user_id_from_session()
            assert result is None
    
    def test_get_user_id_session_with_empty_user_id(self):
        """Test when session has empty string user_id."""
        app = Flask(__name__)
        
        with app.test_request_context():
            mock_session = Mock()
            mock_session.user_id = ""
            request.session = mock_session
            
            # Empty string is falsy, so should return None
            result = get_user_id_from_session()
            assert result is None


class TestGetAccountIdFromSession:
    """Tests for get_account_id_from_session function."""
    
    def test_get_account_id_with_valid_session_and_user(self):
        """Test getting account_id when session and user exist."""
        app = Flask(__name__)
        test_user_id = str(uuid.uuid4())
        test_account_id = "test-account-123"
        
        with app.test_request_context():
            # Mock session
            mock_session = Mock()
            mock_session.user_id = test_user_id
            request.session = mock_session
            
            # Mock database and user
            mock_user = Mock()
            mock_user.account_id = test_account_id
            
            mock_db = MagicMock()
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_filter.first.return_value = mock_user
            mock_query.filter.return_value = mock_filter
            mock_db.query.return_value = mock_query
            
            with patch('backend.utils.session_helpers.SessionLocal', return_value=mock_db):
                result = get_account_id_from_session()
                assert result == test_account_id
                mock_db.close.assert_called_once()
    
    def test_get_account_id_no_session(self):
        """Test when request has no session."""
        app = Flask(__name__)
        
        with app.test_request_context():
            if hasattr(request, 'session'):
                delattr(request, 'session')
            
            result = get_account_id_from_session()
            assert result is None
    
    def test_get_account_id_session_is_none(self):
        """Test when request.session is None."""
        app = Flask(__name__)
        
        with app.test_request_context():
            request.session = None
            
            result = get_account_id_from_session()
            assert result is None
    
    def test_get_account_id_session_without_user_id(self):
        """Test when session has no user_id."""
        app = Flask(__name__)
        
        with app.test_request_context():
            mock_session = Mock()
            # Don't set user_id
            if hasattr(mock_session, 'user_id'):
                delattr(mock_session, 'user_id')
            request.session = mock_session
            
            result = get_account_id_from_session()
            assert result is None
            # Should not query database if no user_id
    
    def test_get_account_id_user_not_found(self):
        """Test when user is not found in database."""
        app = Flask(__name__)
        test_user_id = str(uuid.uuid4())
        
        with app.test_request_context():
            mock_session = Mock()
            mock_session.user_id = test_user_id
            request.session = mock_session
            
            # Mock database returning None (user not found)
            mock_db = MagicMock()
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_filter.first.return_value = None
            mock_query.filter.return_value = mock_filter
            mock_db.query.return_value = mock_query
            
            with patch('backend.utils.session_helpers.SessionLocal', return_value=mock_db):
                result = get_account_id_from_session()
                assert result is None
                mock_db.close.assert_called_once()
    
    def test_get_account_id_database_exception(self):
        """Test when database query raises exception."""
        app = Flask(__name__)
        test_user_id = str(uuid.uuid4())
        
        with app.test_request_context():
            mock_session = Mock()
            mock_session.user_id = test_user_id
            request.session = mock_session
            
            # Mock database raising exception
            mock_db = MagicMock()
            mock_db.query.side_effect = Exception("Database error")
            
            with patch('backend.utils.session_helpers.SessionLocal', return_value=mock_db):
                result = get_account_id_from_session()
                assert result is None
                # Should still close database connection
                mock_db.close.assert_called_once()
    
    def test_get_account_id_query_exception(self):
        """Test when query filter raises exception."""
        app = Flask(__name__)
        test_user_id = str(uuid.uuid4())
        
        with app.test_request_context():
            mock_session = Mock()
            mock_session.user_id = test_user_id
            request.session = mock_session
            
            # Mock database with exception in filter
            mock_db = MagicMock()
            mock_query = MagicMock()
            mock_query.filter.side_effect = Exception("Query error")
            mock_db.query.return_value = mock_query
            
            with patch('backend.utils.session_helpers.SessionLocal', return_value=mock_db):
                result = get_account_id_from_session()
                assert result is None
                mock_db.close.assert_called_once()
    
    def test_get_account_id_always_closes_db(self):
        """Test that database connection is always closed even on success."""
        app = Flask(__name__)
        test_user_id = str(uuid.uuid4())
        test_account_id = "test-account-123"
        
        with app.test_request_context():
            mock_session = Mock()
            mock_session.user_id = test_user_id
            request.session = mock_session
            
            mock_user = Mock()
            mock_user.account_id = test_account_id
            
            mock_db = MagicMock()
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_filter.first.return_value = mock_user
            mock_query.filter.return_value = mock_filter
            mock_db.query.return_value = mock_query
            
            with patch('backend.utils.session_helpers.SessionLocal', return_value=mock_db):
                result = get_account_id_from_session()
                assert result == test_account_id
                # Verify close was called
                assert mock_db.close.call_count == 1
