"""Integration tests for OSC-FinOps API health and endpoint checks."""
import pytest
import requests


def test_health(test_base_url):
    """Test health check endpoint."""
    try:
        response = requests.get(f"{test_base_url}/health", timeout=5)
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        data = response.json()
        assert data is not None, "Response should contain JSON data"
    except requests.exceptions.ConnectionError:
        pytest.fail(
            "Cannot connect to server. Is it running? "
            "Try: ./start.sh or python -m flask --app backend.app run"
        )
    except Exception as e:
        pytest.fail(f"Health check error: {e}")


def test_auth_endpoints(test_base_url):
    """Test authentication endpoints exist."""
    endpoints = [
        ("POST", "/api/auth/login"),
        ("POST", "/api/auth/logout"),
        ("GET", "/api/auth/session"),
    ]
    
    for method, endpoint in endpoints:
        try:
            # Just check if endpoint exists (will get 400/401, not 404)
            if method == "GET":
                response = requests.get(f"{test_base_url}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{test_base_url}{endpoint}", json={}, timeout=5)
            
            # 404 means endpoint doesn't exist, anything else means it exists
            assert response.status_code != 404, (
                f"{method} {endpoint} - Endpoint not found (404)"
            )
        except requests.exceptions.ConnectionError:
            pytest.fail(
                f"{method} {endpoint} - Cannot connect to server. "
                "Make sure the server is running."
            )
        except Exception as e:
            pytest.fail(f"{method} {endpoint} - Error: {e}")


@pytest.mark.requires_credentials
def test_login_with_valid_credentials(test_base_url, test_credentials):
    """Test login with valid credentials."""
    login_url = f"{test_base_url}/api/auth/login"
    login_data = {
        "access_key": test_credentials["access_key"],
        "secret_key": test_credentials["secret_key"],
        "region": test_credentials["region"]
    }
    
    response = requests.post(login_url, json=login_data, timeout=10)
    assert response.status_code == 200, (
        f"Expected status 200, got {response.status_code}. Response: {response.text}"
    )
    
    data = response.json()
    assert data.get("success") is True, "Login should be successful"
    assert "data" in data, "Response should contain 'data' field"
    assert "session_id" in data["data"], "Response should contain 'session_id'"
    assert data["data"]["region"] == test_credentials["region"], (
        f"Region should match. Expected {test_credentials['region']}, "
        f"got {data['data']['region']}"
    )


@pytest.mark.requires_credentials
def test_session_check(test_base_url, authenticated_session):
    """Test session check endpoint with authenticated session."""
    session_id = authenticated_session["session_id"]
    session_url = f"{test_base_url}/api/auth/session"
    
    response = requests.get(
        session_url,
        params={"session_id": session_id},
        timeout=10
    )
    assert response.status_code == 200, (
        f"Expected status 200, got {response.status_code}. Response: {response.text}"
    )
    
    data = response.json()
    assert data.get("success") is True, "Session check should be successful"
    assert "data" in data, "Response should contain 'data' field"
    assert data["data"]["session_id"] == session_id, "Session ID should match"


@pytest.mark.requires_credentials
def test_logout(test_base_url, authenticated_session):
    """Test logout endpoint with authenticated session."""
    session_id = authenticated_session["session_id"]
    logout_url = f"{test_base_url}/api/auth/logout"
    
    response = requests.post(
        logout_url,
        json={"session_id": session_id},
        headers={"X-Session-ID": session_id},
        timeout=10
    )
    assert response.status_code == 200, (
        f"Expected status 200, got {response.status_code}. Response: {response.text}"
    )
    
    data = response.json()
    assert data.get("success") is True, "Logout should be successful"
    
    # Verify session is deleted by checking it again
    session_url = f"{test_base_url}/api/auth/session"
    check_response = requests.get(
        session_url,
        params={"session_id": session_id},
        timeout=10
    )
    assert check_response.status_code == 401, (
        "Session should be deleted and return 401"
    )
