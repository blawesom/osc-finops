"""Unit tests for consumption API endpoints."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.app import create_app
from backend.utils.errors import APIError


class TestConsumptionAPI:
    """Tests for consumption API endpoints."""
    
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
        """Mock session_manager to return valid session."""
        with patch('backend.middleware.auth_middleware.session_manager') as mock:
            session = Mock()
            session.user_id = "test-user-id"
            session.region = 'eu-west-2'
            session.access_key = 'test-access-key'
            session.secret_key = 'test-secret-key'
            mock.get_session.return_value = session
            yield mock
    
    @pytest.fixture
    def mock_account_id(self):
        """Mock account_id from session."""
        with patch('backend.api.consumption.get_account_id_from_session') as mock:
            mock.return_value = "test-account-id"
            yield mock
    
    @pytest.fixture
    def mock_get_consumption(self):
        """Mock get_consumption service."""
        with patch('backend.api.consumption.get_consumption') as mock:
            mock.return_value = {
                'entries': [
                    {'Date': '2024-01-01', 'Service': 'Compute', 'Cost': 10.0}
                ],
                'region': 'eu-west-2',
                'currency': 'EUR'
            }
            yield mock
    
    def test_get_consumption_success(self, client, mock_session_manager, mock_account_id, mock_get_consumption):
        """Test successful consumption retrieval."""
        with patch('backend.api.consumption.validate_date_range') as mock_validate:
            mock_validate.return_value = (True, None)
            
            response = client.get('/api/consumption?from_date=2024-01-01&to_date=2024-01-31',
                                 headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'data' in data
    
    def test_get_consumption_missing_dates(self, client, mock_session_manager, mock_account_id):
        """Test consumption retrieval without required dates."""
        response = client.get('/api/consumption', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'from_date and to_date' in data['error']['message']
    
    def test_get_consumption_invalid_date_range(self, client, mock_session_manager, mock_account_id):
        """Test consumption retrieval with invalid date range."""
        with patch('backend.api.consumption.validate_date_range') as mock_validate:
            mock_validate.return_value = (False, "Invalid date range")
            
            response = client.get('/api/consumption?from_date=2024-01-31&to_date=2024-01-01',
                                 headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
    
    def test_get_consumption_invalid_granularity(self, client, mock_session_manager, mock_account_id):
        """Test consumption retrieval with invalid granularity."""
        response = client.get('/api/consumption?from_date=2024-01-01&to_date=2024-01-31&granularity=invalid',
                             headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_get_consumption_invalid_region(self, client, mock_session_manager, mock_account_id):
        """Test consumption retrieval with invalid region."""
        with patch('backend.api.consumption.validate_date_range') as mock_validate:
            mock_validate.return_value = (True, None)
            
            response = client.get('/api/consumption?from_date=2024-01-01&to_date=2024-01-31&region=invalid-region',
                                 headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
    
    def test_export_consumption_csv(self, client, mock_session_manager, mock_account_id, mock_get_consumption):
        """Test consumption CSV export."""
        with patch('backend.api.consumption.validate_date_range') as mock_validate:
            mock_validate.return_value = (True, None)
            
            response = client.get('/api/consumption/export?from_date=2024-01-01&to_date=2024-01-31',
                                 headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 200
            assert response.content_type == 'text/csv'
            assert 'attachment' in response.headers.get('Content-Disposition', '')
