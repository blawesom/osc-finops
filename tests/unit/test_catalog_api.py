"""Unit tests for catalog API endpoints."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.app import create_app
from backend.utils.errors import APIError


class TestCatalogAPI:
    """Tests for /api/catalog endpoint."""
    
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
    def mock_get_catalog(self):
        """Mock get_catalog service."""
        with patch('backend.api.catalog.get_catalog') as mock:
            mock.return_value = {
                'region': 'eu-west-2',
                'currency': 'EUR',
                'entries': [
                    {'Service': 'Compute', 'Category': 'compute', 'Price': '0.10'},
                    {'Service': 'Storage', 'Category': 'storage', 'Price': '0.15'}
                ],
                'entry_count': 2
            }
            yield mock
    
    @pytest.fixture
    def mock_filter_catalog(self):
        """Mock filter_catalog_by_category."""
        with patch('backend.api.catalog.filter_catalog_by_category') as mock:
            mock.return_value = [
                {'Service': 'Compute', 'Category': 'compute', 'Price': '0.10'}
            ]
            yield mock
    
    def test_get_catalog_success(self, client, mock_get_catalog):
        """Test successful catalog retrieval."""
        response = client.get('/api/catalog?region=eu-west-2')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['region'] == 'eu-west-2'
        assert 'entries' in data['data']
        mock_get_catalog.assert_called_once_with('eu-west-2', force_refresh=False)
    
    def test_get_catalog_with_force_refresh(self, client, mock_get_catalog):
        """Test catalog retrieval with force refresh."""
        response = client.get('/api/catalog?region=eu-west-2&force_refresh=true')
        
        assert response.status_code == 200
        mock_get_catalog.assert_called_once_with('eu-west-2', force_refresh=True)
    
    def test_get_catalog_with_category_filter(self, client, mock_get_catalog, mock_filter_catalog):
        """Test catalog retrieval with category filter."""
        response = client.get('/api/catalog?region=eu-west-2&category=Compute')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert data['data']['filtered_by'] == 'Compute'
        mock_filter_catalog.assert_called_once()
    
    def test_get_catalog_missing_region(self, client):
        """Test catalog retrieval without region parameter."""
        response = client.get('/api/catalog')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_get_catalog_invalid_region(self, client):
        """Test catalog retrieval with invalid region."""
        response = client.get('/api/catalog?region=invalid-region')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Unsupported region' in data['error']['message']
    
    def test_get_catalog_service_error(self, client, mock_get_catalog):
        """Test catalog retrieval when service raises ValueError."""
        mock_get_catalog.side_effect = ValueError("Invalid region")
        
        response = client.get('/api/catalog?region=eu-west-2')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_get_catalog_internal_error(self, client, mock_get_catalog):
        """Test catalog retrieval when service raises generic exception."""
        mock_get_catalog.side_effect = Exception("Database error")
        
        response = client.get('/api/catalog?region=eu-west-2')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert 'Failed to fetch catalog' in data['error']['message']
