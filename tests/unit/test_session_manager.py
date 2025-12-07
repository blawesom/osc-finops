"""Unit tests for backend.auth.session_manager."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from backend.auth.session_manager import Session, SessionManager
from backend.config.settings import SESSION_TIMEOUT


class TestSession:
    """Tests for Session class."""
    
    def test_session_init(self):
        """Test Session initialization."""
        session = Session("access_key", "secret_key", "eu-west-2")
        
        assert session.access_key == "access_key"
        assert session.secret_key == "secret_key"
        assert session.region == "eu-west-2"
        assert session.session_id is not None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_activity, datetime)
        assert isinstance(session.expires_at, datetime)
    
    @patch('backend.auth.session_manager.datetime')
    def test_update_activity(self, mock_datetime):
        """Test update_activity extends expiration."""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        session = Session("key", "secret", "eu-west-2")
        original_expires = session.expires_at
        
        # Move time forward
        later = now + timedelta(minutes=10)
        mock_datetime.utcnow.return_value = later
        
        session.update_activity()
        
        assert session.last_activity == later
        assert session.expires_at > original_expires
        assert session.expires_at == later + timedelta(seconds=SESSION_TIMEOUT)
    
    @patch('backend.auth.session_manager.datetime')
    def test_is_expired_false(self, mock_datetime):
        """Test is_expired returns False for active session."""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        session = Session("key", "secret", "eu-west-2")
        
        # Move time forward but before expiration
        later = now + timedelta(minutes=15)
        mock_datetime.utcnow.return_value = later
        
        assert session.is_expired() is False
    
    @patch('backend.auth.session_manager.datetime')
    def test_is_expired_true(self, mock_datetime):
        """Test is_expired returns True for expired session."""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        session = Session("key", "secret", "eu-west-2")
        
        # Move time forward past expiration
        later = now + timedelta(seconds=SESSION_TIMEOUT + 1)
        mock_datetime.utcnow.return_value = later
        
        assert session.is_expired() is True
    
    def test_to_dict(self):
        """Test to_dict excludes sensitive data."""
        session = Session("access_key", "secret_key", "eu-west-2")
        
        result = session.to_dict()
        
        assert "session_id" in result
        assert "region" in result
        assert "created_at" in result
        assert "last_activity" in result
        assert "expires_at" in result
        assert "access_key" not in result
        assert "secret_key" not in result


class TestSessionManager:
    """Tests for SessionManager class."""
    
    @patch('backend.auth.session_manager.SessionLocal')
    def test_create_session_database(self, mock_session_local):
        """Test create_session stores in database."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        mock_db_session = Mock()
        mock_db_session.session_id = "session-123"
        mock_db_session.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_db_session.last_activity = datetime(2024, 1, 1, 12, 0, 0)
        mock_db_session.expires_at = datetime(2024, 1, 1, 12, 30, 0)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('backend.auth.session_manager.SessionModel', return_value=mock_db_session):
            manager = SessionManager()
            session = manager.create_session("user-123", "access_key", "secret_key", "eu-west-2")
            
            assert session.session_id == "session-123"
            assert session.region == "eu-west-2"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @patch('backend.auth.session_manager.SessionLocal')
    def test_create_session_database_error_fallback(self, mock_session_local):
        """Test create_session falls back to in-memory on database error."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_db.add.side_effect = Exception("Database error")
        
        with patch('backend.auth.session_manager.SessionModel'):
            manager = SessionManager()
            session = manager.create_session("user-123", "access_key", "secret_key", "eu-west-2")
            
            assert session.session_id is not None
            assert session.region == "eu-west-2"
            # Should be stored in memory
            assert session.session_id in manager._sessions
    
    def test_create_session_in_memory(self):
        """Test create_session uses in-memory when database disabled."""
        manager = SessionManager()
        manager._use_database = False
        
        session = manager.create_session("user-123", "access_key", "secret_key", "eu-west-2")
        
        assert session.session_id is not None
        assert session.session_id in manager._sessions
    
    @patch('backend.auth.session_manager.SessionLocal')
    def test_get_session_database(self, mock_session_local):
        """Test get_session retrieves from database."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        mock_db_session = Mock()
        mock_db_session.session_id = "session-123"
        mock_db_session.user_id = "user-123"
        mock_db_session.access_key = "access_key"
        mock_db_session.secret_key = "secret_key"
        mock_db_session.region = "eu-west-2"
        mock_db_session.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_db_session.last_activity = datetime(2024, 1, 1, 12, 0, 0)
        mock_db_session.expires_at = datetime(2024, 1, 1, 12, 30, 0)
        mock_db_session.is_expired.return_value = False
        mock_db_session.update_activity.return_value = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_db_session
        
        manager = SessionManager()
        session = manager.get_session("session-123")
        
        assert session is not None
        assert session.session_id == "session-123"
        assert session.region == "eu-west-2"
        mock_db_session.update_activity.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @patch('backend.auth.session_manager.SessionLocal')
    def test_get_session_not_found(self, mock_session_local):
        """Test get_session returns None when not found."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        manager = SessionManager()
        session = manager.get_session("nonexistent")
        
        assert session is None
    
    def test_get_session_in_memory_fallback(self):
        """Test get_session falls back to in-memory."""
        manager = SessionManager()
        manager._use_database = False  # Disable DB to force in-memory
        
        # Create session in memory
        in_memory_session = manager.create_session("user-123", "key", "secret", "eu-west-2")
        
        # Should find in memory
        session = manager.get_session(in_memory_session.session_id)
        assert session is not None
        assert session.session_id == in_memory_session.session_id
    
    @patch('backend.auth.session_manager.SessionLocal')
    @patch('backend.auth.session_manager.datetime')
    def test_delete_session(self, mock_datetime, mock_session_local):
        """Test delete_session removes from database."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        mock_db_session = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_db_session
        
        manager = SessionManager()
        result = manager.delete_session("session-123")
        
        assert result is True
        mock_db.delete.assert_called_once_with(mock_db_session)
        mock_db.commit.assert_called_once()
    
    @patch('backend.auth.session_manager.SessionLocal')
    def test_delete_session_not_found(self, mock_session_local):
        """Test delete_session returns False when not found."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        manager = SessionManager()
        result = manager.delete_session("nonexistent")
        
        assert result is False
    
    @patch('backend.auth.session_manager.SessionLocal')
    def test_cleanup_expired(self, mock_session_local):
        """Test cleanup_expired removes expired sessions."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        expired_session = Mock()
        expired_session.session_id = "expired-123"
        expired_session.expires_at = datetime(2024, 1, 1, 12, 0, 0)
        
        active_session = Mock()
        active_session.session_id = "active-123"
        active_session.expires_at = datetime(2025, 1, 1, 12, 0, 0)
        
        mock_db.query.return_value.filter.return_value.all.return_value = [expired_session]
        
        with patch('backend.auth.session_manager.datetime') as mock_dt:
            mock_dt.utcnow.return_value = datetime(2024, 1, 1, 12, 30, 0)
            
            manager = SessionManager()
            count = manager.cleanup_expired()
            
            assert count == 1
            assert mock_db.delete.call_count == 1
            mock_db.commit.assert_called_once()
    
    @patch('backend.auth.session_manager.SessionLocal')
    def test_get_session_count(self, mock_session_local):
        """Test get_session_count returns active session count."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        manager = SessionManager()
        count = manager.get_session_count()
        
        assert count == 5

