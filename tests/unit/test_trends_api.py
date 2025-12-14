"""Unit tests for trends API endpoints."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid

from backend.app import create_app
from backend.utils.errors import APIError


class TestTrendsAPI:
    """Tests for trends API endpoints."""
    
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
        with patch('backend.api.trends.request') as mock_request:
            session = Mock()
            session.region = 'eu-west-2'
            session.access_key = 'test-access-key'
            session.secret_key = 'test-secret-key'
            mock_request.session = session
            yield mock_request
    
    @pytest.fixture
    def mock_account_id(self):
        """Mock account_id from session."""
        with patch('backend.api.trends.get_account_id_from_session') as mock:
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
    def mock_user_id(self):
        """Mock user_id from session."""
        with patch('backend.api.trends.get_user_id_from_session') as mock:
            mock.return_value = str(uuid.uuid4())
            yield mock
    
    @pytest.fixture
    def mock_calculate_trends_async(self):
        """Mock calculate_trends_async service."""
        with patch('backend.api.trends.calculate_trends_async') as mock:
            mock.return_value = 'test-job-id'
            yield mock
    
    @pytest.fixture
    def mock_job_queue(self):
        """Mock job_queue."""
        with patch('backend.api.trends.job_queue') as mock:
            job = {
                'job_id': 'test-job-id',
                'status': 'pending',
                'progress': 0
            }
            mock.get_job.return_value = job
            yield mock
    
    def test_submit_trends_job_success(self, client, mock_session_manager, mock_account_id,
                                      mock_user_id, mock_calculate_trends_async):
        """Test successful trends job submission."""
        with patch('backend.api.trends.validate_date_range') as mock_validate:
            mock_validate.return_value = (True, None)
            
            response = client.post('/api/trends/async', json={
                'from_date': '2024-01-01',
                'to_date': '2024-01-31',
                'granularity': 'day'
            }, headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 202
            data = response.get_json()
            assert 'data' in data
            assert 'job_id' in data['data']
    
    def test_submit_trends_job_missing_dates(self, client, mock_session_manager, mock_account_id):
        """Test trends job submission without required dates."""
        response = client.post('/api/trends/async', json={}, headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'from_date and to_date' in data['error']['message']
    
    def test_submit_trends_job_invalid_date_range(self, client, mock_session_manager, mock_account_id):
        """Test trends job submission with invalid date range."""
        with patch('backend.api.trends.validate_date_range') as mock_validate:
            mock_validate.return_value = (False, "Invalid date range")
            
            response = client.post('/api/trends/async', json={
                'from_date': '2024-01-31',
                'to_date': '2024-01-01',
                'granularity': 'day'
            }, headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
    
    def test_submit_trends_job_invalid_granularity(self, client, mock_session_manager, mock_account_id):
        """Test trends job submission with invalid granularity."""
        with patch('backend.api.trends.validate_date_range') as mock_validate:
            mock_validate.return_value = (True, None)
            
            response = client.post('/api/trends/async', json={
                'from_date': '2024-01-01',
                'to_date': '2024-01-31',
                'granularity': 'invalid'
            }, headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
    
    def test_submit_trends_job_invalid_region(self, client, mock_session_manager, mock_account_id):
        """Test trends job submission with invalid region."""
        with patch('backend.api.trends.validate_date_range') as mock_validate:
            mock_validate.return_value = (True, None)
            
            response = client.post('/api/trends/async', json={
                'from_date': '2024-01-01',
                'to_date': '2024-01-31',
                'region': 'invalid-region'
            }, headers={'X-Session-ID': 'test-session-id'})
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
    
    def test_get_job_status_success(self, client, mock_session_manager, mock_job_queue):
        """Test successful job status retrieval."""
        job_id = str(uuid.uuid4())
        
        response = client.get(f'/api/trends/jobs/{job_id}', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['status'] == 'pending'
    
    def test_get_job_status_not_found(self, client, mock_session_manager, mock_job_queue):
        """Test job status retrieval when job not found."""
        job_id = str(uuid.uuid4())
        mock_job_queue.get_job.return_value = None
        
        response = client.get(f'/api/trends/jobs/{job_id}', headers={'X-Session-ID': 'test-session-id'})
        
        assert response.status_code == 404
        # APIError is raised, which gets caught by error handler
        data = response.get_json()
        assert 'error' in data
