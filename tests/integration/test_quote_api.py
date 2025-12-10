"""Integration tests for Quote API endpoints."""
import pytest
import requests
import csv
import io


@pytest.mark.requires_credentials
class TestCreateQuote:
    """Tests for POST /api/quotes endpoint."""
    
    def test_create_quote_success(self, test_base_url, authenticated_session):
        """Test creating a quote successfully."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/quotes"
        headers = {"X-Session-ID": session_id}
        data = {"name": "Test Quote"}
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["name"] == "Test Quote"
        assert result["data"]["status"] == "active"
        assert "quote_id" in result["data"]
    
    def test_create_quote_with_default_name(self, test_base_url, authenticated_session):
        """Test creating a quote without providing name."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/quotes"
        headers = {"X-Session-ID": session_id}
        
        response = requests.post(url, json={}, headers=headers, timeout=10)
        
        assert response.status_code == 201
        result = response.json()
        assert result["data"]["name"] == "Untitled Quote"
    
    def test_create_quote_requires_auth(self, test_base_url):
        """Test that creating a quote requires authentication."""
        url = f"{test_base_url}/api/quotes"
        data = {"name": "Test Quote"}
        
        response = requests.post(url, json=data, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestListQuotes:
    """Tests for GET /api/quotes endpoint."""
    
    def test_list_quotes_success(self, test_base_url, authenticated_session):
        """Test listing quotes successfully."""
        session_id = authenticated_session["session_id"]
        url = f"{test_base_url}/api/quotes"
        headers = {"X-Session-ID": session_id}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert isinstance(result["data"], list)
    
    def test_list_quotes_requires_auth(self, test_base_url):
        """Test that listing quotes requires authentication."""
        url = f"{test_base_url}/api/quotes"
        
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestGetQuote:
    """Tests for GET /api/quotes/:id endpoint."""
    
    def test_get_quote_success(self, test_base_url, authenticated_session):
        """Test getting a quote by ID."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # First create a quote
        create_url = f"{test_base_url}/api/quotes"
        create_response = requests.post(
            create_url,
            json={"name": "Test Quote"},
            headers=headers,
            timeout=10
        )
        quote_id = create_response.json()["data"]["quote_id"]
        
        # Then get it
        get_url = f"{test_base_url}/api/quotes/{quote_id}"
        response = requests.get(get_url, headers=headers, timeout=10)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["quote_id"] == quote_id
        assert result["data"]["name"] == "Test Quote"
    
    def test_get_quote_not_found(self, test_base_url, authenticated_session):
        """Test getting a non-existent quote."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        url = f"{test_base_url}/api/quotes/{fake_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        assert response.status_code == 404
    
    def test_get_quote_requires_auth(self, test_base_url):
        """Test that getting a quote requires authentication."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{test_base_url}/api/quotes/{fake_id}"
        
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestUpdateQuote:
    """Tests for PUT /api/quotes/:id endpoint."""
    
    def test_update_quote_name(self, test_base_url, authenticated_session):
        """Test updating a quote's name."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a quote
        create_url = f"{test_base_url}/api/quotes"
        create_response = requests.post(
            create_url,
            json={"name": "Original Name"},
            headers=headers,
            timeout=10
        )
        quote_id = create_response.json()["data"]["quote_id"]
        
        # Update it
        update_url = f"{test_base_url}/api/quotes/{quote_id}"
        update_response = requests.put(
            update_url,
            json={"name": "Updated Name"},
            headers=headers,
            timeout=10
        )
        
        assert update_response.status_code == 200
        result = update_response.json()
        assert result["data"]["name"] == "Updated Name"
    
    def test_update_quote_configuration(self, test_base_url, authenticated_session):
        """Test updating quote configuration."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a quote
        create_url = f"{test_base_url}/api/quotes"
        create_response = requests.post(
            create_url,
            json={"name": "Test Quote"},
            headers=headers,
            timeout=10
        )
        quote_id = create_response.json()["data"]["quote_id"]
        
        # Update configuration
        update_url = f"{test_base_url}/api/quotes/{quote_id}"
        update_data = {
            "duration": 200,
            "duration_unit": "hours",
            "commitment_period": "1year",
            "global_discount_percent": 10.0
        }
        update_response = requests.put(
            update_url,
            json=update_data,
            headers=headers,
            timeout=10
        )
        
        assert update_response.status_code == 200
        result = update_response.json()
        assert result["data"]["duration"] == 200
        assert result["data"]["duration_unit"] == "hours"
        assert result["data"]["commitment_period"] == "1year"
        assert result["data"]["global_discount_percent"] == 10.0
    
    def test_update_quote_status(self, test_base_url, authenticated_session):
        """Test updating quote status (active/saved)."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a quote
        create_url = f"{test_base_url}/api/quotes"
        create_response = requests.post(
            create_url,
            json={"name": "Test Quote"},
            headers=headers,
            timeout=10
        )
        quote_id = create_response.json()["data"]["quote_id"]
        
        # Update status to saved
        update_url = f"{test_base_url}/api/quotes/{quote_id}"
        update_response = requests.put(
            update_url,
            json={"status": "saved"},
            headers=headers,
            timeout=10
        )
        
        assert update_response.status_code == 200
        result = update_response.json()
        assert result["data"]["status"] == "saved"
    
    def test_update_quote_not_found(self, test_base_url, authenticated_session):
        """Test updating a non-existent quote."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        url = f"{test_base_url}/api/quotes/{fake_id}"
        response = requests.put(
            url,
            json={"name": "Updated"},
            headers=headers,
            timeout=10
        )
        
        assert response.status_code == 404
    
    def test_update_quote_requires_auth(self, test_base_url):
        """Test that updating a quote requires authentication."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{test_base_url}/api/quotes/{fake_id}"
        
        response = requests.put(url, json={"name": "Updated"}, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestDeleteQuote:
    """Tests for DELETE /api/quotes/:id endpoint."""
    
    def test_delete_quote_success(self, test_base_url, authenticated_session):
        """Test deleting a quote successfully."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a quote
        create_url = f"{test_base_url}/api/quotes"
        create_response = requests.post(
            create_url,
            json={"name": "To Delete"},
            headers=headers,
            timeout=10
        )
        quote_id = create_response.json()["data"]["quote_id"]
        
        # Delete it
        delete_url = f"{test_base_url}/api/quotes/{quote_id}"
        delete_response = requests.delete(delete_url, headers=headers, timeout=10)
        
        assert delete_response.status_code == 200
        result = delete_response.json()
        assert result["success"] is True
        
        # Verify it's deleted
        get_url = f"{test_base_url}/api/quotes/{quote_id}"
        get_response = requests.get(get_url, headers=headers, timeout=10)
        assert get_response.status_code == 404
    
    def test_delete_quote_not_found(self, test_base_url, authenticated_session):
        """Test deleting a non-existent quote."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        url = f"{test_base_url}/api/quotes/{fake_id}"
        response = requests.delete(url, headers=headers, timeout=10)
        
        # Should return 500 or appropriate error
        assert response.status_code in [404, 500]
    
    def test_delete_quote_requires_auth(self, test_base_url):
        """Test that deleting a quote requires authentication."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{test_base_url}/api/quotes/{fake_id}"
        
        response = requests.delete(url, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestAddQuoteItem:
    """Tests for POST /api/quotes/:id/items endpoint."""
    
    def test_add_quote_item_success(self, test_base_url, authenticated_session):
        """Test adding an item to a quote."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a quote
        create_url = f"{test_base_url}/api/quotes"
        create_response = requests.post(
            create_url,
            json={"name": "Test Quote"},
            headers=headers,
            timeout=10
        )
        quote_id = create_response.json()["data"]["quote_id"]
        
        # Add an item
        item_data = {
            "resource_name": "t2.micro",
            "quantity": 2.0,
            "unit_price": 0.10,
            "resource_data": {
                "Category": "compute",
                "Flags": ""
            }
        }
        add_url = f"{test_base_url}/api/quotes/{quote_id}/items"
        add_response = requests.post(
            add_url,
            json=item_data,
            headers=headers,
            timeout=10
        )
        
        assert add_response.status_code == 200
        result = add_response.json()
        assert result["success"] is True
        assert len(result["data"]["items"]) > 0
    
    def test_add_quote_item_auto_generates_id(self, test_base_url, authenticated_session):
        """Test that item ID is auto-generated if not provided."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a quote
        create_url = f"{test_base_url}/api/quotes"
        create_response = requests.post(
            create_url,
            json={"name": "Test Quote"},
            headers=headers,
            timeout=10
        )
        quote_id = create_response.json()["data"]["quote_id"]
        
        # Add item without ID
        item_data = {
            "resource_name": "t2.micro",
            "quantity": 1.0,
            "unit_price": 0.10,
            "resource_data": {"Category": "compute", "Flags": ""}
        }
        add_url = f"{test_base_url}/api/quotes/{quote_id}/items"
        add_response = requests.post(
            add_url,
            json=item_data,
            headers=headers,
            timeout=10
        )
        
        assert add_response.status_code == 200
        result = add_response.json()
        items = result["data"]["items"]
        assert len(items) > 0
        assert "id" in items[0]
    
    def test_add_quote_item_not_found(self, test_base_url, authenticated_session):
        """Test adding item to non-existent quote."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        url = f"{test_base_url}/api/quotes/{fake_id}/items"
        response = requests.post(
            url,
            json={"resource_name": "test"},
            headers=headers,
            timeout=10
        )
        
        assert response.status_code == 404
    
    def test_add_quote_item_requires_auth(self, test_base_url):
        """Test that adding an item requires authentication."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{test_base_url}/api/quotes/{fake_id}/items"
        
        response = requests.post(url, json={"resource_name": "test"}, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestRemoveQuoteItem:
    """Tests for DELETE /api/quotes/:id/items/:item_id endpoint."""
    
    def test_remove_quote_item_success(self, test_base_url, authenticated_session):
        """Test removing an item from a quote."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a quote
        create_url = f"{test_base_url}/api/quotes"
        create_response = requests.post(
            create_url,
            json={"name": "Test Quote"},
            headers=headers,
            timeout=10
        )
        quote_id = create_response.json()["data"]["quote_id"]
        
        # Add an item
        item_data = {
            "id": "item-123",
            "resource_name": "t2.micro",
            "quantity": 1.0,
            "unit_price": 0.10,
            "resource_data": {"Category": "compute", "Flags": ""}
        }
        add_url = f"{test_base_url}/api/quotes/{quote_id}/items"
        add_response = requests.post(
            add_url,
            json=item_data,
            headers=headers,
            timeout=10
        )
        items = add_response.json()["data"]["items"]
        item_id = items[0]["id"]
        
        # Remove the item
        remove_url = f"{test_base_url}/api/quotes/{quote_id}/items/{item_id}"
        remove_response = requests.delete(remove_url, headers=headers, timeout=10)
        
        assert remove_response.status_code == 200
        result = remove_response.json()
        assert len(result["data"]["items"]) == 0
    
    def test_remove_quote_item_not_found(self, test_base_url, authenticated_session):
        """Test removing a non-existent item."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a quote
        create_url = f"{test_base_url}/api/quotes"
        create_response = requests.post(
            create_url,
            json={"name": "Test Quote"},
            headers=headers,
            timeout=10
        )
        quote_id = create_response.json()["data"]["quote_id"]
        
        # Try to remove non-existent item
        remove_url = f"{test_base_url}/api/quotes/{quote_id}/items/nonexistent-item"
        remove_response = requests.delete(remove_url, headers=headers, timeout=10)
        
        assert remove_response.status_code == 404
    
    def test_remove_quote_item_requires_auth(self, test_base_url):
        """Test that removing an item requires authentication."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{test_base_url}/api/quotes/{fake_id}/items/item-123"
        
        response = requests.delete(url, timeout=10)
        
        assert response.status_code == 401


@pytest.mark.requires_credentials
class TestExportQuoteCSV:
    """Tests for GET /api/quotes/:id/export/csv endpoint."""
    
    def test_export_quote_csv_success(self, test_base_url, authenticated_session):
        """Test exporting a quote to CSV."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # Create a quote with an item
        create_url = f"{test_base_url}/api/quotes"
        create_response = requests.post(
            create_url,
            json={"name": "Test Quote"},
            headers=headers,
            timeout=10
        )
        quote_id = create_response.json()["data"]["quote_id"]
        
        # Add an item
        item_data = {
            "resource_name": "t2.micro",
            "quantity": 2.0,
            "unit_price": 0.10,
            "resource_data": {"Category": "compute", "Flags": ""}
        }
        add_url = f"{test_base_url}/api/quotes/{quote_id}/items"
        requests.post(add_url, json=item_data, headers=headers, timeout=10)
        
        # Export to CSV
        export_url = f"{test_base_url}/api/quotes/{quote_id}/export/csv"
        export_response = requests.get(export_url, headers=headers, timeout=10)
        
        assert export_response.status_code == 200
        assert export_response.headers["Content-Type"] == "text/csv; charset=utf-8"
        
        # Verify CSV content
        csv_content = export_response.text
        assert "OSC-FinOps Quote Export" in csv_content
        assert "Test Quote" in csv_content
        assert "t2.micro" in csv_content
    
    def test_export_quote_csv_not_found(self, test_base_url, authenticated_session):
        """Test exporting a non-existent quote."""
        session_id = authenticated_session["session_id"]
        headers = {"X-Session-ID": session_id}
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        url = f"{test_base_url}/api/quotes/{fake_id}/export/csv"
        response = requests.get(url, headers=headers, timeout=10)
        
        assert response.status_code == 404
    
    def test_export_quote_csv_requires_auth(self, test_base_url):
        """Test that exporting a quote requires authentication."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{test_base_url}/api/quotes/{fake_id}/export/csv"
        
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 401
