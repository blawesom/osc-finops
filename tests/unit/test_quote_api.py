"""Unit tests for quote API endpoints."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid

from backend.app import create_app
from backend.utils.errors import APIError


class TestQuoteAPI:
    """Tests for quote API endpoints."""
    
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
    def mock_user_id(self):
        """Mock user_id from session."""
        with patch('backend.api.quote.get_user_id_from_session') as mock:
            mock.return_value = str(uuid.uuid4())
            yield mock
    
    @pytest.fixture
    def mock_quote_service(self):
        """Mock QuoteServiceDB."""
        with patch('backend.api.quote.QuoteServiceDB') as mock:
            yield mock
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        with patch('backend.api.quote.SessionLocal') as mock:
            db = Mock()
            mock.return_value = db
            yield db
    
    def test_create_quote_success(self, client, mock_session_manager, mock_user_id, mock_quote_service, mock_db_session):
        """Test successful quote creation."""
        quote = Mock()
        quote.to_dict.return_value = {'quote_id': 'test-id', 'name': 'Test Quote'}
        mock_quote_service.create_quote.return_value = quote
        
        response = client.post('/api/quotes', json={'name': 'Test Quote'}, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'data' in data
        mock_quote_service.create_quote.assert_called_once()
    
    def test_create_quote_default_name(self, client, mock_user_id, mock_quote_service, mock_db_session):
        """Test quote creation with default name."""
        quote = Mock()
        quote.to_dict.return_value = {'quote_id': 'test-id', 'name': 'Untitled Quote'}
        mock_quote_service.create_quote.return_value = quote
        
        response = client.post('/api/quotes', json={}, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 201
        mock_quote_service.create_quote.assert_called_once()
        # Check that default name is used
        call_args = mock_quote_service.create_quote.call_args
        assert call_args[0][1] == 'Untitled Quote'
    
    def test_create_quote_validation_error(self, client, mock_session_manager, mock_user_id, mock_quote_service, mock_db_session):
        """Test quote creation with validation error."""
        mock_quote_service.create_quote.side_effect = ValueError("Invalid quote data")
        
        response = client.post('/api/quotes', json={'name': 'Test Quote'}, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_create_quote_internal_error(self, client, mock_user_id, mock_quote_service, mock_db_session):
        """Test quote creation with internal error."""
        mock_quote_service.create_quote.side_effect = Exception("Database error")
        
        response = client.post('/api/quotes', json={'name': 'Test Quote'}, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
    
    def test_list_quotes_success(self, client, mock_session_manager, mock_user_id, mock_quote_service, mock_db_session):
        """Test successful quote listing."""
        mock_quote_service.list_quotes.return_value = [
            {'quote_id': 'id1', 'name': 'Quote 1'},
            {'quote_id': 'id2', 'name': 'Quote 2'}
        ]
        
        response = client.get('/api/quotes', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert len(data['data']) == 2
    
    def test_get_quote_success(self, client, mock_user_id, mock_quote_service, mock_db_session):
        """Test successful quote retrieval."""
        quote_id = str(uuid.uuid4())
        quote = Mock()
        quote.status = 'active'
        quote.to_dict.return_value = {'quote_id': quote_id, 'name': 'Test Quote'}
        mock_quote_service.get_quote.return_value = quote
        
        response = client.get(f'/api/quotes/{quote_id}', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert data['data']['quote_id'] == quote_id
    
    def test_get_quote_not_found(self, client, mock_session_manager, mock_user_id, mock_quote_service, mock_db_session):
        """Test quote retrieval when quote not found."""
        quote_id = str(uuid.uuid4())
        mock_quote_service.get_quote.return_value = None
        
        response = client.get(f'/api/quotes/{quote_id}', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_get_quote_loads_saved(self, client, mock_user_id, mock_quote_service, mock_db_session):
        """Test that saved quotes are loaded (made active) when retrieved."""
        quote_id = str(uuid.uuid4())
        saved_quote = Mock()
        saved_quote.status = 'saved'
        saved_quote.to_dict.return_value = {'quote_id': quote_id, 'name': 'Saved Quote'}
        
        active_quote = Mock()
        active_quote.to_dict.return_value = {'quote_id': quote_id, 'name': 'Saved Quote', 'status': 'active'}
        
        mock_quote_service.get_quote.return_value = saved_quote
        mock_quote_service.load_quote.return_value = active_quote
        
        response = client.get(f'/api/quotes/{quote_id}', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        mock_quote_service.load_quote.assert_called_once()
    
    def test_update_quote_success(self, client, mock_session_manager, mock_user_id, mock_quote_service, mock_db_session):
        """Test successful quote update."""
        quote_id = str(uuid.uuid4())
        quote = Mock()
        quote.to_dict.return_value = {'quote_id': quote_id, 'name': 'Updated Quote'}
        mock_quote_service.update_quote.return_value = quote
        
        response = client.put(f'/api/quotes/{quote_id}', json={'name': 'Updated Quote'}, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_update_quote_not_found(self, client, mock_user_id, mock_quote_service, mock_db_session):
        """Test quote update when quote not found."""
        quote_id = str(uuid.uuid4())
        mock_quote_service.update_quote.return_value = None
        
        response = client.put(f'/api/quotes/{quote_id}', json={'name': 'Updated Quote'}, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_delete_quote_success(self, client, mock_session_manager, mock_user_id, mock_quote_service, mock_db_session):
        """Test successful quote deletion."""
        quote_id = str(uuid.uuid4())
        mock_quote_service.delete_quote.return_value = True
        
        response = client.delete(f'/api/quotes/{quote_id}', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_delete_quote_not_found(self, client, mock_user_id, mock_quote_service, mock_db_session):
        """Test quote deletion when quote not found."""
        quote_id = str(uuid.uuid4())
        mock_quote_service.delete_quote.return_value = False
        
        response = client.delete(f'/api/quotes/{quote_id}', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_add_quote_item_success(self, client, mock_session_manager, mock_user_id, mock_quote_service, mock_db_session):
        """Test successful quote item addition."""
        quote_id = str(uuid.uuid4())
        quote = Mock()
        quote.to_dict.return_value = {'quote_id': quote_id, 'items': []}
        mock_quote_service.add_item.return_value = quote
        
        response = client.post(f'/api/quotes/{quote_id}/items', json={
            'resource_name': 't2.micro',
            'quantity': 1.0,
            'unit_price': 0.10
        }, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_remove_quote_item_success(self, client, mock_user_id, mock_quote_service, mock_db_session):
        """Test successful quote item removal."""
        quote_id = str(uuid.uuid4())
        quote = Mock()
        quote.to_dict.return_value = {'quote_id': quote_id, 'items': []}
        mock_quote_service.remove_item.return_value = quote
        
        response = client.delete(f'/api/quotes/{quote_id}/items/item-123', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
    
    def test_export_quote_csv(self, client, mock_session_manager, mock_user_id, mock_quote_service, mock_db_session):
        """Test quote CSV export."""
        quote_id = str(uuid.uuid4())
        quote = Mock()
        quote.to_dict.return_value = {
            'quote_id': quote_id,
            'name': 'Test Quote',
            'items': [{'resource_name': 't2.micro', 'quantity': 1.0, 'unit_price': 0.10}]
        }
        mock_quote_service.get_quote.return_value = quote
        
        response = client.get(f'/api/quotes/{quote_id}/export/csv', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
        assert 'attachment' in response.headers.get('Content-Disposition', '')
