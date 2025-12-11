"""Integration tests for Catalog API endpoint."""
import pytest
import requests


class TestGetCatalog:
    """Tests for GET /api/catalog endpoint."""
    
    def test_get_catalog_success(self, test_base_url):
        """Test getting catalog successfully."""
        url = f"{test_base_url}/api/catalog"
        params = {"region": "eu-west-2"}
        
        response = requests.get(url, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert "entries" in result["data"]
        assert "region" in result["data"]
        assert result["data"]["region"] == "eu-west-2"
    
    def test_get_catalog_different_regions(self, test_base_url):
        """Test getting catalog for different regions."""
        url = f"{test_base_url}/api/catalog"
        
        regions = ["eu-west-2", "us-east-2", "us-west-1"]
        
        for region in regions:
            params = {"region": region}
            response = requests.get(url, params=params, timeout=30)
            
            # Some regions might not be available, but should not return 400
            if response.status_code == 200:
                result = response.json()
                assert result["data"]["region"] == region
    
    def test_get_catalog_with_category_filter(self, test_base_url):
        """Test getting catalog filtered by category."""
        url = f"{test_base_url}/api/catalog"
        params = {
            "region": "eu-west-2",
            "category": "Compute"
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "filtered_by" in result["data"]
        assert result["data"]["filtered_by"] == "Compute"
        
        # All entries should be in the Compute category (case-insensitive comparison)
        entries = result["data"]["entries"]
        if entries:
            for entry in entries:
                # Category in entries might be lowercase "compute" while filtered_by is "Compute"
                category = entry.get("Category", "")
                assert category.lower() == "compute" or category == "Compute"
    
    def test_get_catalog_with_storage_category(self, test_base_url):
        """Test getting catalog filtered by Storage category."""
        url = f"{test_base_url}/api/catalog"
        params = {
            "region": "eu-west-2",
            "category": "Storage"
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        if result["data"]["entries"]:
            assert result["data"]["filtered_by"] == "Storage"
    
    def test_get_catalog_with_network_category(self, test_base_url):
        """Test getting catalog filtered by Network category."""
        url = f"{test_base_url}/api/catalog"
        params = {
            "region": "eu-west-2",
            "category": "Network"
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        if result["data"]["entries"]:
            assert result["data"]["filtered_by"] == "Network"
    
    def test_get_catalog_with_force_refresh(self, test_base_url):
        """Test getting catalog with force refresh."""
        url = f"{test_base_url}/api/catalog"
        params = {
            "region": "eu-west-2",
            "force_refresh": "true"
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_get_catalog_missing_region(self, test_base_url):
        """Test getting catalog without region parameter."""
        url = f"{test_base_url}/api/catalog"
        
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 400
        result = response.json()
        assert "Region parameter is required" in result["error"]["message"]
    
    def test_get_catalog_invalid_region(self, test_base_url):
        """Test getting catalog with invalid region."""
        url = f"{test_base_url}/api/catalog"
        params = {"region": "invalid-region"}
        
        response = requests.get(url, params=params, timeout=10)
        
        assert response.status_code == 400
        result = response.json()
        assert "Unsupported region" in result["error"]["message"]
    
    def test_get_catalog_no_auth_required(self, test_base_url):
        """Test that catalog endpoint doesn't require authentication."""
        url = f"{test_base_url}/api/catalog"
        params = {"region": "eu-west-2"}
        
        # Don't provide any authentication headers
        response = requests.get(url, params=params, timeout=30)
        
        # Should succeed without authentication
        assert response.status_code == 200
    
    def test_get_catalog_structure(self, test_base_url):
        """Test that catalog response has correct structure."""
        url = f"{test_base_url}/api/catalog"
        params = {"region": "eu-west-2"}
        
        response = requests.get(url, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        data = result["data"]
        
        # Check required fields
        assert "region" in data
        assert "currency" in data
        assert "entries" in data
        assert "entry_count" in data
        assert isinstance(data["entries"], list)
        assert isinstance(data["entry_count"], int)
        
        # If there are entries, check their structure
        if data["entries"]:
            entry = data["entries"][0]
            assert "Service" in entry or "Category" in entry
            assert "Price" in entry or "Operation" in entry

