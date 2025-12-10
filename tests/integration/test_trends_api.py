"""Integration tests for Trends API endpoints."""
import pytest
import requests
import time
from datetime import datetime, timedelta


@pytest.mark.requires_credentials
class TestSubmitTrendsJob:
    """Tests for POST /api/trends/async endpoint."""
    
    def test_submit_trends_job_success(self, test_base_url, authenticated_session):
        """Test submitting a trends calculation job successfully."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/trends/async"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        data = {
            "from_date": from_date,
            "to_date": to_date,
            "granularity": "day"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert "job_id" in result["data"]
        assert result["data"]["status"] == "pending"
    
    def test_submit_trends_job_with_week_granularity(self, test_base_url, authenticated_session):
        """Test submitting a trends job with week granularity."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/trends/async"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%d")
        
        data = {
            "from_date": from_date,
            "to_date": to_date,
            "granularity": "week"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "job_id" in result["data"]
    
    def test_submit_trends_job_with_month_granularity(self, test_base_url, authenticated_session):
        """Test submitting a trends job with month granularity."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/trends/async"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=60)).strftime("%Y-%m-%d")
        
        data = {
            "from_date": from_date,
            "to_date": to_date,
            "granularity": "month"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_submit_trends_job_with_region(self, test_base_url, authenticated_session):
        """Test submitting a trends job with specific region."""
        session_id = authenticated_session["session_id"]
        region = authenticated_session["region"]
        url = f"{test_base_url}/api/trends/async"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        data = {
            "from_date": from_date,
            "to_date": to_date,
            "region": region
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_submit_trends_job_with_resource_type(self, test_base_url, authenticated_session):
        """Test submitting a trends job with resource type filter."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/trends/async"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        data = {
            "from_date": from_date,
            "to_date": to_date,
            "resource_type": "t2.micro"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_submit_trends_job_with_force_refresh(self, test_base_url, authenticated_session):
        """Test submitting a trends job with force refresh."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/trends/async"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        data = {
            "from_date": from_date,
            "to_date": to_date,
            "force_refresh": True
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_submit_trends_job_missing_dates(self, test_base_url, authenticated_session):
        """Test submitting a trends job without required dates."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/trends/async"
        headers = {"X-Session-ID": session_id}
        
        data = {}
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 400
        result = response.json()
        assert "from_date and to_date are required" in result["error"]["message"]
    
    def test_submit_trends_job_invalid_date_range(self, test_base_url, authenticated_session):
        """Test submitting a trends job with invalid date range."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/trends/async"
        headers = {"X-Session-ID": session_id}
        
        # to_date before from_date
        data = {
            "from_date": "2024-01-10",
            "to_date": "2024-01-01"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 400
    
    def test_submit_trends_job_invalid_granularity(self, test_base_url, authenticated_session):
        """Test submitting a trends job with invalid granularity."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/trends/async"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        data = {
            "from_date": from_date,
            "to_date": to_date,
            "granularity": "invalid"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 400
        result = response.json()
        assert "granularity must be" in result["error"]["message"]
    
    def test_submit_trends_job_invalid_region(self, test_base_url, authenticated_session):
        """Test submitting a trends job with invalid region."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/trends/async"
        headers = {"X-Session-ID": session_id}
        
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        data = {
            "from_date": from_date,
            "to_date": to_date,
            "region": "invalid-region"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 400
    
    def test_submit_trends_job_requires_auth(self, test_base_url):
        """Test that submitting a trends job requires authentication."""
        url = f"{test_base_url}/api/trends/async"
        data = {
            "from_date": "2024-01-01",
            "to_date": "2024-01-02"
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestGetJobStatus:
    """Tests for GET /api/trends/jobs/:job_id endpoint."""
    
    def test_get_job_status_pending(self, test_base_url, authenticated_session):
        """Test getting status of a pending job."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Submit a job
        submit_url = f"{test_base_url}/api/trends/async"
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        submit_data = {
            "from_date": from_date,
            "to_date": to_date
        }
        submit_response = requests.post(
            submit_url,
            json=submit_data,
            headers=headers,
            timeout=10
        )
        job_id = submit_response.json()["data"]["job_id"]
        
        # Get job status immediately (should be pending or processing)
        status_url = f"{test_base_url}/api/trends/jobs/{job_id}"
        status_response = requests.get(status_url, headers=headers, timeout=10)
        
        assert status_response.status_code == 200
        result = status_response.json()
        assert result["success"] is True
        assert "data" in result
        assert "status" in result["data"]
        assert result["data"]["status"] in ["pending", "processing", "completed", "failed"]
        assert "job_id" in result["data"]
        assert result["data"]["job_id"] == job_id
    
    def test_get_job_status_nonexistent(self, test_base_url, authenticated_session):
        """Test getting status of a non-existent job."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        url = f"{test_base_url}/api/trends/jobs/{fake_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False
        assert "not found" in result["error"]["message"].lower()
    
    def test_get_job_status_requires_auth(self, test_base_url):
        """Test that getting job status requires authentication."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{test_base_url}/api/trends/jobs/{fake_id}"
        
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 401
    
    def test_get_job_status_progress(self, test_base_url, authenticated_session):
        """Test that job status includes progress information."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Submit a job
        submit_url = f"{test_base_url}/api/trends/async"
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        submit_data = {
            "from_date": from_date,
            "to_date": to_date
        }
        submit_response = requests.post(
            submit_url,
            json=submit_data,
            headers=headers,
            timeout=10
        )
        job_id = submit_response.json()["data"]["job_id"]
        
        # Get job status
        status_url = f"{test_base_url}/api/trends/jobs/{job_id}"
        status_response = requests.get(status_url, headers=headers, timeout=10)
        
        assert status_response.status_code == 200
        result = status_response.json()
        assert "progress" in result["data"]
        assert "created_at" in result["data"]
        assert "updated_at" in result["data"]
