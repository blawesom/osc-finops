"""Integration tests for Consumption API endpoints."""
import pytest
import requests
from datetime import datetime, timedelta


@pytest.mark.requires_credentials
class TestGetConsumption:
    """Tests for GET /api/consumption endpoint."""
    
    def test_get_consumption_success(self, test_base_url, authenticated_session):
        """Test getting consumption data successfully."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        # Use past dates
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert "entries" in result["data"]
    
    def test_get_consumption_with_granularity_day(self, test_base_url, authenticated_session):
        """Test getting consumption with day granularity."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "granularity": "day"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_get_consumption_with_granularity_week(self, test_base_url, authenticated_session):
        """Test getting consumption with week granularity."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "granularity": "week"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_get_consumption_with_granularity_month(self, test_base_url, authenticated_session):
        """Test getting consumption with month granularity."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=60)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "granularity": "month"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_get_consumption_with_region_filter(self, test_base_url, authenticated_session):
        """Test getting consumption filtered by region."""
        session_id = authenticated_session["session_id"]
        region = authenticated_session["region"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "region": region
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_get_consumption_with_service_filter(self, test_base_url, authenticated_session):
        """Test getting consumption filtered by service."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "service": "Compute"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_get_consumption_with_resource_type_filter(self, test_base_url, authenticated_session):
        """Test getting consumption filtered by resource type."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "resource_type": "t2.micro"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_get_consumption_with_aggregate_by_resource_type(self, test_base_url, authenticated_session):
        """Test getting consumption aggregated by resource type."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "aggregate_by": "resource_type"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_get_consumption_missing_dates(self, test_base_url, authenticated_session):
        """Test getting consumption without required date parameters."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        assert response.status_code == 400
        result = response.json()
        assert "from_date and to_date parameters are required" in result["error"]["message"]
    
    def test_get_consumption_invalid_date_range(self, test_base_url, authenticated_session):
        """Test getting consumption with invalid date range."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        # to_date before from_date
        params = {
            "from_date": "2024-01-10",
            "to_date": "2024-01-01"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        assert response.status_code == 400
    
    def test_get_consumption_invalid_granularity(self, test_base_url, authenticated_session):
        """Test getting consumption with invalid granularity."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "granularity": "invalid"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        assert response.status_code == 400
        result = response.json()
        assert "granularity must be" in result["error"]["message"]
    
    def test_get_consumption_invalid_region(self, test_base_url, authenticated_session):
        """Test getting consumption with invalid region."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "region": "invalid-region"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        assert response.status_code == 400
    
    def test_get_consumption_with_force_refresh(self, test_base_url, authenticated_session):
        """Test getting consumption with force refresh."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "force_refresh": "true"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_get_consumption_requires_auth(self, test_base_url):
        """Test that getting consumption requires authentication."""
        url = f"{test_base_url}/api/consumption"
        params = {
            "from_date": "2024-01-01",
            "to_date": "2024-01-02"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestExportConsumption:
    """Tests for GET /api/consumption/export endpoint."""
    
    def test_export_consumption_csv(self, test_base_url, authenticated_session):
        """Test exporting consumption as CSV."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption/export"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "format": "csv"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["Content-Type"]
        assert "attachment" in response.headers.get("Content-Disposition", "")
        assert "consumption_export" in response.headers.get("Content-Disposition", "")
        assert "Date" in response.text
    
    def test_export_consumption_json(self, test_base_url, authenticated_session):
        """Test exporting consumption as JSON."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption/export"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "format": "json"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        assert "application/json" in response.headers["Content-Type"]
        assert "attachment" in response.headers.get("Content-Disposition", "")
        
        result = response.json()
        assert "entries" in result
    
    def test_export_consumption_default_format_csv(self, test_base_url, authenticated_session):
        """Test that default export format is CSV."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption/export"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["Content-Type"]
    
    def test_export_consumption_missing_dates(self, test_base_url, authenticated_session):
        """Test exporting consumption without required date parameters."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/consumption/export"
        headers = {"X-Session-ID": session_id}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        assert response.status_code == 400
    
    def test_export_consumption_requires_auth(self, test_base_url):
        """Test that exporting consumption requires authentication."""
        url = f"{test_base_url}/api/consumption/export"
        params = {
            "from_date": "2024-01-01",
            "to_date": "2024-01-02"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        assert response.status_code == 401
