"""Integration tests for Budget API endpoints."""
import pytest
import requests
from datetime import datetime, timedelta


@pytest.mark.requires_credentials
class TestCreateBudget:
    """Tests for POST /api/budgets endpoint."""
    
    def test_create_budget_success(self, test_base_url, authenticated_session):
        """Test creating a budget successfully."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/budgets"
        headers = {"X-Session-ID": session_id}
        
        # Use past dates
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (datetime.utcnow() + timedelta(days=335)).strftime("%Y-%m-%d")
        
        data = {
            "name": "Test Budget",
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": start_date,
            "end_date": end_date
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert result["data"]["name"] == "Test Budget"
        assert result["data"]["amount"] == 1000.0
        assert result["data"]["period_type"] == "monthly"
        assert "budget_id" in result["data"]
    
    def test_create_budget_without_end_date(self, test_base_url, authenticated_session):
        """Test creating a budget without end_date."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/budgets"
        headers = {"X-Session-ID": session_id}
        
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        data = {
            "name": "Test Budget",
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": start_date
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 201
        result = response.json()
        assert result["data"]["end_date"] is None
    
    def test_create_budget_quarterly(self, test_base_url, authenticated_session):
        """Test creating a quarterly budget."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/budgets"
        headers = {"X-Session-ID": session_id}
        
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        data = {
            "name": "Quarterly Budget",
            "amount": 3000.0,
            "period_type": "quarterly",
            "start_date": start_date
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 201
        result = response.json()
        assert result["data"]["period_type"] == "quarterly"
    
    def test_create_budget_yearly(self, test_base_url, authenticated_session):
        """Test creating a yearly budget."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/budgets"
        headers = {"X-Session-ID": session_id}
        
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        data = {
            "name": "Yearly Budget",
            "amount": 12000.0,
            "period_type": "yearly",
            "start_date": start_date
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 201
        result = response.json()
        assert result["data"]["period_type"] == "yearly"
    
    def test_create_budget_missing_name(self, test_base_url, authenticated_session):
        """Test creating a budget without name."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/budgets"
        headers = {"X-Session-ID": session_id}
        
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        data = {
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": start_date
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 400
    
    def test_create_budget_missing_amount(self, test_base_url, authenticated_session):
        """Test creating a budget without amount."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/budgets"
        headers = {"X-Session-ID": session_id}
        
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        data = {
            "name": "Test Budget",
            "period_type": "monthly",
            "start_date": start_date
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 400
    
    def test_create_budget_invalid_date_format(self, test_base_url, authenticated_session):
        """Test creating a budget with invalid date format."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/budgets"
        headers = {"X-Session-ID": session_id}
        
        data = {
            "name": "Test Budget",
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": "2024/01/01"  # Wrong format
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 400
    
    def test_create_budget_requires_auth(self, test_base_url):
        """Test that creating a budget requires authentication."""
        url = f"{test_base_url}/api/budgets"
        data = {"name": "Test Budget", "amount": 1000.0}
        
        response = requests.post(url, json=data, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestListBudgets:
    """Tests for GET /api/budgets endpoint."""
    
    def test_list_budgets_success(self, test_base_url, authenticated_session):
        """Test listing budgets successfully."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/budgets"
        headers = {"X-Session-ID": session_id}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert isinstance(result["data"], list)
    
    def test_list_budgets_requires_auth(self, test_base_url):
        """Test that listing budgets requires authentication."""
        url = f"{test_base_url}/api/budgets"
        
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestGetBudget:
    """Tests for GET /api/budgets/:id endpoint."""
    
    def test_get_budget_success(self, test_base_url, authenticated_session):
        """Test getting a budget by ID."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a budget
        create_url = f"{test_base_url}/api/budgets"
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        create_data = {
            "name": "Test Budget",
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": start_date
        }
        create_response = requests.post(
            create_url,
            json=create_data,
            headers=headers,
            timeout=10
        )
        budget_id = create_response.json()["data"]["budget_id"]
        
        # Get it
        get_url = f"{test_base_url}/api/budgets/{budget_id}"
        response = requests.get(get_url, headers=headers, timeout=10)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["budget_id"] == budget_id
        assert result["data"]["name"] == "Test Budget"
    
    def test_get_budget_not_found(self, test_base_url, authenticated_session):
        """Test getting a non-existent budget."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        url = f"{test_base_url}/api/budgets/{fake_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        assert response.status_code == 404
    
    def test_get_budget_requires_auth(self, test_base_url):
        """Test that getting a budget requires authentication."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{test_base_url}/api/budgets/{fake_id}"
        
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestUpdateBudget:
    """Tests for PUT /api/budgets/:id endpoint."""
    
    def test_update_budget_name(self, test_base_url, authenticated_session):
        """Test updating a budget's name."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a budget
        create_url = f"{test_base_url}/api/budgets"
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        create_data = {
            "name": "Original Name",
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": start_date
        }
        create_response = requests.post(
            create_url,
            json=create_data,
            headers=headers,
            timeout=10
        )
        budget_id = create_response.json()["data"]["budget_id"]
        
        # Update it
        update_url = f"{test_base_url}/api/budgets/{budget_id}"
        update_response = requests.put(
            update_url,
            json={"name": "Updated Name"},
            headers=headers,
            timeout=10
        )
        
        assert update_response.status_code == 200
        result = update_response.json()
        assert result["data"]["name"] == "Updated Name"
    
    def test_update_budget_amount(self, test_base_url, authenticated_session):
        """Test updating a budget's amount."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a budget
        create_url = f"{test_base_url}/api/budgets"
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        create_data = {
            "name": "Test Budget",
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": start_date
        }
        create_response = requests.post(
            create_url,
            json=create_data,
            headers=headers,
            timeout=10
        )
        budget_id = create_response.json()["data"]["budget_id"]
        
        # Update amount
        update_url = f"{test_base_url}/api/budgets/{budget_id}"
        update_response = requests.put(
            update_url,
            json={"amount": 2000.0},
            headers=headers,
            timeout=10
        )
        
        assert update_response.status_code == 200
        result = update_response.json()
        assert result["data"]["amount"] == 2000.0
    
    def test_update_budget_period_type(self, test_base_url, authenticated_session):
        """Test updating a budget's period type."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a budget
        create_url = f"{test_base_url}/api/budgets"
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        create_data = {
            "name": "Test Budget",
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": start_date
        }
        create_response = requests.post(
            create_url,
            json=create_data,
            headers=headers,
            timeout=10
        )
        budget_id = create_response.json()["data"]["budget_id"]
        
        # Update period type
        update_url = f"{test_base_url}/api/budgets/{budget_id}"
        update_response = requests.put(
            update_url,
            json={"period_type": "quarterly"},
            headers=headers,
            timeout=10
        )
        
        assert update_response.status_code == 200
        result = update_response.json()
        assert result["data"]["period_type"] == "quarterly"
    
    def test_update_budget_not_found(self, test_base_url, authenticated_session):
        """Test updating a non-existent budget."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        url = f"{test_base_url}/api/budgets/{fake_id}"
        response = requests.put(
            url,
            json={"name": "Updated"},
            headers=headers,
            timeout=10
        )
        
        assert response.status_code == 404
    
    def test_update_budget_requires_auth(self, test_base_url):
        """Test that updating a budget requires authentication."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{test_base_url}/api/budgets/{fake_id}"
        
        response = requests.put(url, json={"name": "Updated"}, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestDeleteBudget:
    """Tests for DELETE /api/budgets/:id endpoint."""
    
    def test_delete_budget_success(self, test_base_url, authenticated_session):
        """Test deleting a budget successfully."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a budget
        create_url = f"{test_base_url}/api/budgets"
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        create_data = {
            "name": "To Delete",
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": start_date
        }
        create_response = requests.post(
            create_url,
            json=create_data,
            headers=headers,
            timeout=10
        )
        budget_id = create_response.json()["data"]["budget_id"]
        
        # Delete it
        delete_url = f"{test_base_url}/api/budgets/{budget_id}"
        delete_response = requests.delete(delete_url, headers=headers, timeout=10)
        
        assert delete_response.status_code == 200
        result = delete_response.json()
        assert result["success"] is True
        
        # Verify it's deleted
        get_url = f"{test_base_url}/api/budgets/{budget_id}"
        get_response = requests.get(get_url, headers=headers, timeout=10)
        assert get_response.status_code == 404
    
    def test_delete_budget_not_found(self, test_base_url, authenticated_session):
        """Test deleting a non-existent budget."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        url = f"{test_base_url}/api/budgets/{fake_id}"
        response = requests.delete(url, headers=headers, timeout=10)
        
        assert response.status_code == 404
    
    def test_delete_budget_requires_auth(self, test_base_url):
        """Test that deleting a budget requires authentication."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{test_base_url}/api/budgets/{fake_id}"
        
        response = requests.delete(url, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestGetBudgetStatus:
    """Tests for GET /api/budgets/:id/status endpoint."""
    
    def test_get_budget_status_success(self, test_base_url, authenticated_session):
        """Test getting budget status successfully."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a budget
        create_url = f"{test_base_url}/api/budgets"
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        create_data = {
            "name": "Test Budget",
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": start_date
        }
        create_response = requests.post(
            create_url,
            json=create_data,
            headers=headers,
            timeout=10
        )
        budget_id = create_response.json()["data"]["budget_id"]
        
        # Get status
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        status_url = f"{test_base_url}/api/budgets/{budget_id}/status"
        status_response = requests.get(
            status_url,
            params={"from_date": from_date, "to_date": to_date},
            headers=headers,
            timeout=30  # May take longer due to consumption API calls
        )
        
        assert status_response.status_code == 200
        result = status_response.json()
        assert result["success"] is True
        assert "data" in result
        assert "spent" in result["data"]
        assert "budget" in result["data"]
    
    def test_get_budget_status_missing_dates(self, test_base_url, authenticated_session):
        """Test getting budget status without date parameters."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a budget
        create_url = f"{test_base_url}/api/budgets"
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        create_data = {
            "name": "Test Budget",
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": start_date
        }
        create_response = requests.post(
            create_url,
            json=create_data,
            headers=headers,
            timeout=10
        )
        budget_id = create_response.json()["data"]["budget_id"]
        
        # Get status without dates
        status_url = f"{test_base_url}/api/budgets/{budget_id}/status"
        status_response = requests.get(
            status_url,
            headers=headers,
            timeout=10
        )
        
        assert status_response.status_code == 400
    
    def test_get_budget_status_invalid_date_format(self, test_base_url, authenticated_session):
        """Test getting budget status with invalid date format."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a budget
        create_url = f"{test_base_url}/api/budgets"
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        create_data = {
            "name": "Test Budget",
            "amount": 1000.0,
            "period_type": "monthly",
            "start_date": start_date
        }
        create_response = requests.post(
            create_url,
            json=create_data,
            headers=headers,
            timeout=10
        )
        budget_id = create_response.json()["data"]["budget_id"]
        
        # Get status with invalid date format
        status_url = f"{test_base_url}/api/budgets/{budget_id}/status"
        status_response = requests.get(
            status_url,
            params={"from_date": "2024/01/01", "to_date": "2024/01/02"},
            headers=headers,
            timeout=10
        )
        
        assert status_response.status_code == 400
    
    def test_get_budget_status_not_found(self, test_base_url, authenticated_session):
        """Test getting status for non-existent budget."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        url = f"{test_base_url}/api/budgets/{fake_id}/status"
        response = requests.get(
            url,
            params={"from_date": from_date, "to_date": to_date},
            headers=headers,
            timeout=10
        )
        
        assert response.status_code == 404
    
    def test_get_budget_status_requires_auth(self, test_base_url):
        """Test that getting budget status requires authentication."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{test_base_url}/api/budgets/{fake_id}/status"
        
        response = requests.get(
            url,
            params={"from_date": "2024-01-01", "to_date": "2024-01-02"},
            timeout=10
        )
        
        assert response.status_code == 401

