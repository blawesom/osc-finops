"""Pytest configuration and fixtures for OSC-FinOps tests."""
import os
import pytest
from typing import Dict, Optional
from tests.utils.credential_helpers import (
    get_test_credentials,
    validate_credential_format
)


@pytest.fixture(scope="session")
def test_base_url() -> str:
    """Fixture providing the base URL for API testing."""
    return os.getenv("TEST_BASE_URL", "http://localhost:5000")


@pytest.fixture(scope="function")
def test_credentials() -> Dict[str, str]:
    """
    Fixture providing test credentials from environment variables.
    
    Skips the test with a clear warning if credentials are missing or invalid.
    Only use this fixture in tests that require real API calls.
    
    Returns:
        Dictionary with 'access_key', 'secret_key', and 'region'
    
    Raises:
        pytest.skip: If credentials are missing or invalid
    """
    credentials = get_test_credentials()
    
    if not credentials:
        pytest.skip(
            "Skipping test: OSC_ACCESS_KEY, OSC_SECRET_KEY, and OSC_REGION "
            "environment variables required. Set these to run integration/e2e tests."
        )
    
    is_valid, error_msg = validate_credential_format(credentials)
    if not is_valid:
        pytest.skip(
            f"Skipping test: Invalid credentials format. {error_msg}"
        )
    
    return credentials


@pytest.fixture(scope="function")
def authenticated_session(test_base_url: str, test_credentials: Dict[str, str]) -> Dict[str, str]:
    """
    Fixture providing an authenticated session for API tests.
    
    Creates a session by logging in with test credentials.
    Returns session information including session_id.
    
    Returns:
        Dictionary with session information including 'session_id', 'region', 'expires_at'
    
    Raises:
        pytest.skip: If credentials are missing or login fails
    """
    import requests
    
    login_url = f"{test_base_url}/api/auth/login"
    login_data = {
        "access_key": test_credentials["access_key"],
        "secret_key": test_credentials["secret_key"],
        "region": test_credentials["region"]
    }
    
    try:
        response = requests.post(login_url, json=login_data, timeout=10)
        if response.status_code == 200:
            session_data = response.json()
            if session_data.get("success") and session_data.get("data"):
                return session_data["data"]
            else:
                pytest.skip(
                    f"Skipping test: Login failed. Response: {session_data}"
                )
        else:
            pytest.skip(
                f"Skipping test: Login failed with status {response.status_code}. "
                f"Response: {response.text}"
            )
    except requests.exceptions.ConnectionError:
        pytest.skip(
            f"Skipping test: Cannot connect to server. "
            f"Make sure the server is running at {test_base_url}"
        )
    except Exception as e:
        pytest.skip(
            f"Skipping test: Failed to create authenticated session. Error: {e}"
        )

