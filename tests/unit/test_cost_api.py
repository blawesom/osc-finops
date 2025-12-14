"""Unit tests for cost API endpoints."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.app import create_app
from backend.utils.errors import APIError


class TestCostAPI:
    """Tests for cost API endpoints."""
    
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
    def mock_session(self):
        """Mock request session."""
        with patch('backend.api.cost.request') as mock_request:
            session = Mock()
            session.region = 'eu-west-2'
            session.access_key = 'test-access-key'
            session.secret_key = 'test-secret-key'
            mock_request.session = session
            yield mock_request
    
    @pytest.fixture
    def mock_account_id(self):
        """Mock account_id from session."""
        with patch('backend.api.cost.get_account_id_from_session') as mock:
            mock.return_value = "test-account-id"
            yield mock
    
    @pytest.fixture
    def mock_db_user(self):
        """Mock database user query."""
        with patch('backend.utils.session_helpers.SessionLocal') as mock_session:
            db = Mock()
            user = Mock()
            user.account_id = "test-account-id"
            db.query.return_value.filter.return_value.first.return_value = user
            mock_session.return_value = db
            yield db
    
    @pytest.fixture
    def mock_get_current_costs(self):
        """Mock get_current_costs service."""
        with patch('backend.api.cost.get_current_costs') as mock:
            mock.return_value = {
                'resources': [
                    {'resource_id': 'i-123', 'resource_type': 'vm', 'cost_per_hour': 0.10}
                ],
                'totals': {'cost_per_hour': 0.10},
                'region': 'eu-west-2',
                'currency': 'EUR'
            }
            yield mock
    
    def test_get_cost_success(self, client, mock_session_manager, mock_account_id, mock_get_current_costs):
        """Test successful cost retrieval."""
        response = client.get('/api/cost', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        mock_get_current_costs.assert_called_once()
    
    def test_get_cost_invalid_region(self, client, mock_session_manager, mock_account_id):
        """Test cost retrieval with invalid region."""
        response = client.get('/api/cost?region=invalid-region', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_get_cost_incomplete_tag_filter(self, client, mock_session_manager, mock_account_id):
        """Test cost retrieval with incomplete tag filter."""
        response = client.get('/api/cost?tag_key=Environment', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'tag_key and tag_value' in data['error']['message']
    
    def test_get_cost_csv_export(self, client, mock_session_manager, mock_account_id, mock_get_current_costs):
        """Test cost CSV export."""
        response = client.get('/api/cost?format=csv', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
        assert 'attachment' in response.headers.get('Content-Disposition', '')
    
    def test_get_cost_human_format(self, client, mock_session_manager, mock_account_id, mock_get_current_costs):
        """Test cost retrieval in human-readable format."""
        response = client.get('/api/cost?format=human', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        assert response.content_type == 'text/plain; charset=utf-8'
