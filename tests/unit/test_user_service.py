"""Unit tests for backend.services.user_service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from backend.services.user_service import UserService, get_user_service
from backend.models.user import User


class TestUserService:
    """Tests for UserService class."""
    
    def test_get_user_by_account_id_found(self):
        """Test getting user by account_id when user exists."""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = UserService.get_user_by_account_id(mock_db, "123456789012")
        
        assert result == mock_user
        mock_db.query.assert_called_once_with(User)
        mock_db.query.return_value.filter.assert_called_once()
        mock_db.query.return_value.filter.return_value.first.assert_called_once()
    
    def test_get_user_by_account_id_not_found(self):
        """Test getting user by account_id when user doesn't exist."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.get_user_by_account_id(mock_db, "123456789012")
        
        assert result is None
    
    def test_get_user_by_id_found(self):
        """Test getting user by user_id when user exists."""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = UserService.get_user_by_id(mock_db, "user-uuid-123")
        
        assert result == mock_user
    
    def test_get_user_by_id_not_found(self):
        """Test getting user by user_id when user doesn't exist."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.get_user_by_id(mock_db, "user-uuid-123")
        
        assert result is None
    
    def test_get_user_by_access_key_found(self):
        """Test getting user by access_key when user exists."""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = UserService.get_user_by_access_key(mock_db, "access-key-123")
        
        assert result == mock_user
    
    def test_get_user_by_access_key_not_found(self):
        """Test getting user by access_key when user doesn't exist."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.get_user_by_access_key(mock_db, "access-key-123")
        
        assert result is None
    
    @patch('backend.services.user_service.datetime')
    def test_create_or_update_user_existing(self, mock_datetime):
        """Test create_or_update_user with existing user."""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_user.access_key = "old-key"
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        result = UserService.create_or_update_user(mock_db, "123456789012", "new-key")
        
        assert result == mock_user
        assert mock_user.access_key == "new-key"
        assert mock_user.is_active is True
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)
    
    @patch('backend.services.user_service.datetime')
    def test_create_or_update_user_new(self, mock_datetime):
        """Test create_or_update_user with new user."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        with patch('backend.services.user_service.User') as mock_user_class:
            mock_user = Mock(spec=User)
            mock_user_class.return_value = mock_user
            
            result = UserService.create_or_update_user(mock_db, "123456789012", "new-key")
            
            assert result == mock_user
            mock_user_class.assert_called_once_with(
                account_id="123456789012",
                access_key="new-key",
                last_login_at=datetime(2024, 1, 1, 12, 0, 0)
            )
            mock_db.add.assert_called_once_with(mock_user)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_user)
    
    @patch('backend.services.user_service.datetime')
    def test_create_or_update_user_integrity_error_recovery(self, mock_datetime):
        """Test create_or_update_user handles IntegrityError and recovers."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [None, Mock(spec=User)]
        mock_db.commit.side_effect = [IntegrityError("", "", ""), None]
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        with patch('backend.services.user_service.User') as mock_user_class:
            mock_user = Mock(spec=User)
            mock_user_class.return_value = mock_user
            existing_user = Mock(spec=User)
            existing_user.access_key = "old-key"
            mock_db.query.return_value.filter.return_value.first.side_effect = [None, existing_user]
            
            result = UserService.create_or_update_user(mock_db, "123456789012", "new-key")
            
            assert result == existing_user
            assert existing_user.access_key == "new-key"
            mock_db.rollback.assert_called_once()
            assert mock_db.commit.call_count == 2
    
    @patch('backend.services.user_service.datetime')
    def test_create_or_update_user_integrity_error_no_recovery(self, mock_datetime):
        """Test create_or_update_user raises IntegrityError if recovery fails."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [None, None]
        mock_db.commit.side_effect = IntegrityError("", "", "")
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        with patch('backend.services.user_service.User') as mock_user_class:
            mock_user = Mock(spec=User)
            mock_user_class.return_value = mock_user
            
            with pytest.raises(IntegrityError):
                UserService.create_or_update_user(mock_db, "123456789012", "new-key")
            
            mock_db.rollback.assert_called_once()
    
    @patch('backend.services.user_service.datetime')
    def test_update_last_login_existing_user(self, mock_datetime):
        """Test update_last_login with existing user."""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        UserService.update_last_login(mock_db, "user-uuid-123")
        
        assert mock_user.last_login_at == datetime(2024, 1, 1, 12, 0, 0)
        mock_db.commit.assert_called_once()
    
    def test_update_last_login_no_user(self):
        """Test update_last_login when user doesn't exist."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        UserService.update_last_login(mock_db, "user-uuid-123")
        
        mock_db.commit.assert_not_called()


class TestGetUserService:
    """Tests for get_user_service function."""
    
    def test_get_user_service_returns_instance(self):
        """Test that get_user_service returns UserService instance."""
        service = get_user_service()
        assert isinstance(service, UserService)

