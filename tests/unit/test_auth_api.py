"""Unit tests for auth API endpoints."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

from backend.app import create_app
from backend.utils.errors import APIError


class TestAuthLogin:
    """Tests for /api/auth/login endpoint."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        with patch('backend.app.setup_logging'):
            with patch('backend.app.init_db'):
                return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @pytest.fixture
    def mock_user_service(self):
        """Mock UserService."""
        with patch('backend.api.auth.UserService') as mock:
            user = Mock()
            user.user_id = "test-user-id"
            mock.create_or_update_user.return_value = user
            yield mock
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session_manager."""
        with patch('backend.api.auth.session_manager') as mock:
            session = Mock()
            session.session_id = "test-session-id"
            session.region = "eu-west-2"
            session.expires_at = Mock()
            session.expires_at.isoformat.return_value = "2024-01-01T00:00:00"
            mock.create_session.return_value = session
            yield mock
    
    @pytest.fixture
    def mock_validate_credentials(self):
        """Mock validate_credentials."""
        with patch('backend.api.auth.validate_credentials') as mock:
            mock.return_value = (True, None, "test-account-id")
            yield mock
    
    @pytest.fixture
    def mock_validate_region(self):
        """Mock validate_region."""
        with patch('backend.api.auth.validate_region') as mock:
            mock.return_value = (True, None)
            yield mock
    
    @pytest.fixture
    def mock_get_db(self):
        """Mock get_db."""
        with patch('backend.api.auth.get_db') as mock:
            db = Mock()
            mock.return_value = iter([db])
            yield mock
    
    def test_login_success(self, client, mock_user_service, mock_session_manager,
                          mock_validate_credentials, mock_validate_region, mock_get_db):
        """Test successful login."""
        response = client.post('/api/auth/login', json={
            'access_key': 'test-access-key',
            'secret_key': 'test-secret-key',
            'region': 'eu-west-2'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'session_id' in data['data']
        assert data['data']['region'] == 'eu-west-2'
    
    def test_login_missing_access_key(self, client):
        """Test login with missing access_key."""
        response = client.post('/api/auth/login', json={
            'secret_key': 'test-secret-key',
            'region': 'eu-west-2'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_login_missing_secret_key(self, client):
        """Test login with missing secret_key."""
        response = client.post('/api/auth/login', json={
            'access_key': 'test-access-key',
            'region': 'eu-west-2'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_login_missing_region(self, client):
        """Test login with missing region."""
        response = client.post('/api/auth/login', json={
            'access_key': 'test-access-key',
            'secret_key': 'test-secret-key'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_login_invalid_region(self, client, mock_validate_region):
        """Test login with invalid region."""
        mock_validate_region.return_value = (False, "Invalid region")
        
        response = client.post('/api/auth/login', json={
            'access_key': 'test-access-key',
            'secret_key': 'test-secret-key',
            'region': 'invalid-region'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'INVALID_REGION'
    
    def test_login_invalid_credentials(self, client, mock_validate_region, mock_validate_credentials):
        """Test login with invalid credentials."""
        mock_validate_credentials.return_value = (False, "Invalid credentials", None)
        
        response = client.post('/api/auth/login', json={
            'access_key': 'invalid-key',
            'secret_key': 'invalid-secret',
            'region': 'eu-west-2'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'INVALID_CREDENTIALS'
    
    def test_login_no_account_id(self, client, mock_validate_region, mock_validate_credentials):
        """Test login when account_id cannot be retrieved."""
        mock_validate_credentials.return_value = (True, None, None)
        
        response = client.post('/api/auth/login', json={
            'access_key': 'test-access-key',
            'secret_key': 'test-secret-key',
            'region': 'eu-west-2'
        })
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'ACCOUNT_ERROR'
    
    def test_login_invalid_json(self, client):
        """Test login with invalid JSON."""
        response = client.post('/api/auth/login', data='invalid json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestAuthLogout:
    """Tests for /api/auth/logout endpoint."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        with patch('backend.app.setup_logging'):
            with patch('backend.app.init_db'):
                return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session_manager."""
        with patch('backend.api.auth.session_manager') as mock:
            yield mock
    
    def test_logout_success_with_header(self, client, mock_session_manager):
        """Test successful logout with session ID in header."""
        mock_session_manager.delete_session.return_value = True
        
        response = client.post('/api/auth/logout',
                              headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        mock_session_manager.delete_session.assert_called_once_with('test-session-id')
    
    def test_logout_success_with_body(self, client, mock_session_manager):
        """Test successful logout with session ID in body."""
        mock_session_manager.delete_session.return_value = True
        
        response = client.post('/api/auth/logout', json={'session_id': 'test-session-id'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
    
    def test_logout_missing_session_id(self, client):
        """Test logout without session ID."""
        response = client.post('/api/auth/logout', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'MISSING_SESSION'
    
    def test_logout_invalid_session(self, client, mock_session_manager):
        """Test logout with invalid session ID."""
        mock_session_manager.delete_session.return_value = False
        
        response = client.post('/api/auth/logout',
                              headers={'X-Session-ID': 'invalid-session-id'})
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_SESSION'


class TestAuthSession:
    """Tests for /api/auth/session endpoint."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        with patch('backend.app.setup_logging'):
            with patch('backend.app.init_db'):
                return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session_manager."""
        with patch('backend.api.auth.session_manager') as mock:
            session = Mock()
            session.to_dict.return_value = {
                'session_id': 'test-session-id',
                'region': 'eu-west-2'
            }
            mock.get_session.return_value = session
            yield mock
    
    def test_get_session_success_with_header(self, client, mock_session_manager):
        """Test successful session retrieval with header."""
        response = client.get('/api/auth/session',
                            headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'data' in data
        assert data['data']['session_id'] == 'test-session-id'
    
    def test_get_session_success_with_query(self, client, mock_session_manager):
        """Test successful session retrieval with query parameter."""
        response = client.get('/api/auth/session?session_id=test-session-id')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
    
    def test_get_session_missing_session_id(self, client):
        """Test get session without session ID."""
        response = client.get('/api/auth/session')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'MISSING_SESSION'
    
    def test_get_session_not_found(self, client, mock_session_manager):
        """Test get session with invalid session ID."""
        mock_session_manager.get_session.return_value = None
        
        response = client.get('/api/auth/session?session_id=invalid-session-id')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_SESSION'
