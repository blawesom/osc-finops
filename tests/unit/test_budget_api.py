"""Unit tests for budget API endpoints."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid

from backend.app import create_app
from backend.utils.errors import APIError


class TestBudgetAPI:
    """Tests for budget API endpoints."""
    
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
            session.user_id = str(uuid.uuid4())
            session.region = 'eu-west-2'
            mock.get_session.return_value = session
            yield mock
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session_manager to return valid session."""
        with patch('backend.middleware.auth_middleware.session_manager') as mock:
            session = Mock()
            session.user_id = str(uuid.uuid4())
            session.region = 'eu-west-2'
            session.access_key = 'test-access-key'
            session.secret_key = 'test-secret-key'
            mock.get_session.return_value = session
            yield mock
    
    @pytest.fixture
    def mock_user_id(self):
        """Mock user_id from session."""
        with patch('backend.api.budget.get_user_id_from_session') as mock:
            mock.return_value = str(uuid.uuid4())
            yield mock
    
    @pytest.fixture
    def mock_account_id(self):
        """Mock account_id from session."""
        with patch('backend.api.budget.get_account_id_from_session') as mock:
            mock.return_value = "test-account-id"
            yield mock
    
    @pytest.fixture
    def mock_create_budget(self):
        """Mock create_budget service."""
        with patch('backend.api.budget.create_budget') as mock:
            budget = Mock()
            budget.to_dict.return_value = {
                'budget_id': 'test-id',
                'name': 'Test Budget',
                'amount': 1000.0
            }
            mock.return_value = budget
            yield mock
    
    def test_create_budget_success(self, client, mock_session_manager, mock_user_id, mock_create_budget):
        """Test successful budget creation."""
        response = client.post('/api/budgets', json={
            'name': 'Test Budget',
            'amount': 1000.0,
            'period_type': 'monthly',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        mock_create_budget.assert_called_once()
    
    def test_create_budget_missing_name(self, client, mock_session_manager, mock_user_id):
        """Test budget creation without name."""
        response = client.post('/api/budgets', json={
            'amount': 1000.0,
            'period_type': 'monthly',
            'start_date': '2024-01-01'
        }, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'name is required' in data['error']['message']
    
    def test_create_budget_missing_amount(self, client, mock_session_manager, mock_user_id):
        """Test budget creation without amount."""
        response = client.post('/api/budgets', json={
            'name': 'Test Budget',
            'period_type': 'monthly',
            'start_date': '2024-01-01'
        }, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_create_budget_invalid_amount(self, client, mock_session_manager, mock_user_id):
        """Test budget creation with invalid amount."""
        response = client.post('/api/budgets', json={
            'name': 'Test Budget',
            'amount': 'not-a-number',
            'period_type': 'monthly',
            'start_date': '2024-01-01'
        }, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_create_budget_missing_period_type(self, client, mock_session_manager, mock_user_id):
        """Test budget creation without period_type."""
        response = client.post('/api/budgets', json={
            'name': 'Test Budget',
            'amount': 1000.0,
            'start_date': '2024-01-01'
        }, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_create_budget_missing_start_date(self, client, mock_session_manager, mock_user_id):
        """Test budget creation without start_date."""
        response = client.post('/api/budgets', json={
            'name': 'Test Budget',
            'amount': 1000.0,
            'period_type': 'monthly'
        }, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_create_budget_invalid_date_format(self, client, mock_session_manager, mock_user_id):
        """Test budget creation with invalid date format."""
        response = client.post('/api/budgets', json={
            'name': 'Test Budget',
            'amount': 1000.0,
            'period_type': 'monthly',
            'start_date': '01-01-2024'  # Wrong format
        }, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid date format' in data['error']['message']
    
    def test_create_budget_without_end_date(self, client, mock_session_manager, mock_user_id, mock_create_budget):
        """Test budget creation without optional end_date."""
        response = client.post('/api/budgets', json={
            'name': 'Test Budget',
            'amount': 1000.0,
            'period_type': 'monthly',
            'start_date': '2024-01-01'
        }, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
    
    def test_list_budgets_success(self, client, mock_session_manager, mock_user_id):
        """Test successful budget listing."""
        with patch('backend.api.budget.get_budgets') as mock_get:
            mock_get.return_value = [
                Mock(to_dict=lambda: {'budget_id': 'id1', 'name': 'Budget 1'}),
                Mock(to_dict=lambda: {'budget_id': 'id2', 'name': 'Budget 2'})
            ]
            
            response = client.get('/api/budgets', headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'data' in data
            assert len(data['data']) == 2
    
    def test_get_budget_success(self, client, mock_session_manager, mock_user_id):
        """Test successful budget retrieval."""
        budget_id = str(uuid.uuid4())
        with patch('backend.api.budget.get_budget') as mock_get:
            budget = Mock()
            budget.to_dict.return_value = {'budget_id': budget_id, 'name': 'Test Budget'}
            mock_get.return_value = budget
            
            response = client.get(f'/api/budgets/{budget_id}', headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'data' in data
    
    def test_get_budget_not_found(self, client, mock_session_manager, mock_user_id):
        """Test budget retrieval when not found."""
        budget_id = str(uuid.uuid4())
        with patch('backend.api.budget.get_budget') as mock_get:
            mock_get.return_value = None
            
            response = client.get(f'/api/budgets/{budget_id}', headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
    
    def test_update_budget_success(self, client, mock_session_manager, mock_user_id):
        """Test successful budget update."""
        budget_id = str(uuid.uuid4())
        with patch('backend.api.budget.update_budget') as mock_update:
            budget = Mock()
            budget.to_dict.return_value = {'budget_id': budget_id, 'name': 'Updated Budget'}
            mock_update.return_value = budget
            
            response = client.put(f'/api/budgets/{budget_id}', json={
                'name': 'Updated Budget',
                'amount': 2000.0
            }, headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'data' in data
    
    def test_delete_budget_success(self, client, mock_session_manager, mock_user_id):
        """Test successful budget deletion."""
        budget_id = str(uuid.uuid4())
        with patch('backend.api.budget.delete_budget') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete(f'/api/budgets/{budget_id}', headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'data' in data
    
    def test_get_budget_status_success(self, client, mock_session_manager, mock_user_id, mock_account_id):
        """Test successful budget status retrieval."""
        budget_id = str(uuid.uuid4())
        with patch('backend.api.budget.calculate_budget_status') as mock_calc:
            mock_calc.return_value = {
                'budget_id': budget_id,
                'status': 'on_track',
                'spent': 500.0,
                'remaining': 500.0
            }
            
            response = client.get(f'/api/budgets/{budget_id}/status?from_date=2024-01-01&to_date=2024-01-31',
                                 headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'data' in data
