"""Integration tests for Cost API endpoints."""
import pytest
import requests


@pytest.mark.requires_credentials
class TestGetCost:
    """Tests for GET /api/cost endpoint."""
    
    def test_get_cost_json_format(self, test_base_url, authenticated_session):
        """Test getting costs in JSON format."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost"
        headers = {"X-Session-ID": session_id}
        
        response = requests.get(url, headers=headers, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert "metadata" in result
        assert "resources" in result["data"]
        assert "totals" in result["data"]
    
    def test_get_cost_human_format(self, test_base_url, authenticated_session):
        """Test getting costs in human-readable format."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost"
        headers = {"X-Session-ID": session_id}
        params = {"format": "human"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/plain; charset=utf-8"
        assert "Current Cost Evaluation" in response.text
        assert "TOTALS" in response.text
    
    def test_get_cost_csv_format(self, test_base_url, authenticated_session):
        """Test getting costs in CSV format."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost"
        headers = {"X-Session-ID": session_id}
        params = {"format": "csv"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["Content-Type"]
        assert "Resource ID" in response.text
        assert "Resource Type" in response.text
    
    def test_get_cost_ods_format(self, test_base_url, authenticated_session):
        """Test getting costs in ODS format (not implemented, returns JSON)."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost"
        headers = {"X-Session-ID": session_id}
        params = {"format": "ods"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "ODS export not yet implemented" in result.get("message", "")
    
    def test_get_cost_with_region(self, test_base_url, authenticated_session):
        """Test getting costs for a specific region."""
        session_id = authenticated_session["session_id"]
        region = authenticated_session["region"]
        url = f"{test_base_url}/api/cost"
        headers = {"X-Session-ID": session_id}
        params = {"region": region}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["metadata"]["region"] == region
    
    def test_get_cost_with_tag_filter(self, test_base_url, authenticated_session):
        """Test getting costs filtered by tags."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost"
        headers = {"X-Session-ID": session_id}
        params = {"tag_key": "Environment", "tag_value": "Test"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        # Should succeed even if no resources match the filter
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_get_cost_tag_key_without_value(self, test_base_url, authenticated_session):
        """Test that tag_key without tag_value returns error."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost"
        headers = {"X-Session-ID": session_id}
        params = {"tag_key": "Environment"}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False
        assert "Both tag_key and tag_value must be provided" in result["error"]["message"]
    
    def test_get_cost_tag_value_without_key(self, test_base_url, authenticated_session):
        """Test that tag_value without tag_key returns error."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost"
        headers = {"X-Session-ID": session_id}
        params = {"tag_value": "Test"}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        assert response.status_code == 400
    
    def test_get_cost_invalid_region(self, test_base_url, authenticated_session):
        """Test getting costs with invalid region."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost"
        headers = {"X-Session-ID": session_id}
        params = {"region": "invalid-region"}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        assert response.status_code == 400
        result = response.json()
        assert "Unsupported region" in result["error"]["message"]
    
    def test_get_cost_with_force_refresh(self, test_base_url, authenticated_session):
        """Test getting costs with force refresh."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost"
        headers = {"X-Session-ID": session_id}
        params = {"force_refresh": "true"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_get_cost_requires_auth(self, test_base_url):
        """Test that getting costs requires authentication."""
        url = f"{test_base_url}/api/cost"
        
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestExportCost:
    """Tests for GET /api/cost/export endpoint."""
    
    def test_export_cost_csv(self, test_base_url, authenticated_session):
        """Test exporting costs as CSV."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost/export"
        headers = {"X-Session-ID": session_id}
        params = {"format": "csv"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["Content-Type"]
        assert "attachment" in response.headers.get("Content-Disposition", "")
        assert "cost_export" in response.headers.get("Content-Disposition", "")
        assert "Resource ID" in response.text
    
    def test_export_cost_json(self, test_base_url, authenticated_session):
        """Test exporting costs as JSON."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost/export"
        headers = {"X-Session-ID": session_id}
        params = {"format": "json"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        assert "application/json" in response.headers["Content-Type"]
        assert "attachment" in response.headers.get("Content-Disposition", "")
        
        result = response.json()
        assert "resources" in result
    
    def test_export_cost_ods_not_implemented(self, test_base_url, authenticated_session):
        """Test that ODS export is not implemented."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost/export"
        headers = {"X-Session-ID": session_id}
        params = {"format": "ods"}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        assert response.status_code == 501
        result = response.json()
        assert result["success"] is False
        assert "ODS export not yet implemented" in result["error"]["message"]
    
    def test_export_cost_default_format_csv(self, test_base_url, authenticated_session):
        """Test that default export format is CSV."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost/export"
        headers = {"X-Session-ID": session_id}
        
        response = requests.get(url, headers=headers, timeout=30)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["Content-Type"]
    
    def test_export_cost_with_region(self, test_base_url, authenticated_session):
        """Test exporting costs for a specific region."""
        session_id = authenticated_session["session_id"]
        region = authenticated_session["region"]
        url = f"{test_base_url}/api/cost/export"
        headers = {"X-Session-ID": session_id}
        params = {"region": region, "format": "csv"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        assert region in response.headers.get("Content-Disposition", "")
    
    def test_export_cost_with_tag_filter(self, test_base_url, authenticated_session):
        """Test exporting costs with tag filter."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost/export"
        headers = {"X-Session-ID": session_id}
        params = {
            "format": "csv",
            "tag_key": "Environment",
            "tag_value": "Production"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
    
    def test_export_cost_invalid_region(self, test_base_url, authenticated_session):
        """Test exporting costs with invalid region."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/cost/export"
        headers = {"X-Session-ID": session_id}
        params = {"region": "invalid-region"}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        assert response.status_code == 400
    
    def test_export_cost_requires_auth(self, test_base_url):
        """Test that exporting costs requires authentication."""
        url = f"{test_base_url}/api/cost/export"
        
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 401
