"""Pytest configuration and fixtures for OSC-FinOps tests."""
import os
import pytest
import uuid
from typing import Dict, Optional
from unittest.mock import Mock
from datetime import datetime, timedelta
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


@pytest.fixture
def mock_session():
    """
    Fixture providing a mock session object for unit tests.
    
    Returns:
        Mock session object with common attributes
    """
    session = Mock()
    session.session_id = str(uuid.uuid4())
    session.user_id = str(uuid.uuid4())
    session.region = "eu-west-2"
    session.access_key = "test-access-key"
    session.secret_key = "test-secret-key"
    session.created_at = datetime.utcnow()
    session.last_activity = datetime.utcnow()
    session.expires_at = datetime.utcnow() + timedelta(hours=1)
    session.is_expired = Mock(return_value=False)
    session.to_dict = Mock(return_value={
        "session_id": session.session_id,
        "user_id": session.user_id,
        "region": session.region,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "expires_at": session.expires_at.isoformat(),
    })
    return session


@pytest.fixture
def mock_user():
    """
    Fixture providing a mock user object for unit tests.
    
    Returns:
        Mock user object with common attributes
    """
    user = Mock()
    user.user_id = str(uuid.uuid4())
    user.account_id = "test-account-123"
    user.access_key = "test-access-key"
    user.is_active = True
    user.created_at = datetime.utcnow()
    user.last_login_at = datetime.utcnow()
    user.to_dict = Mock(return_value={
        "user_id": user.user_id,
        "account_id": user.account_id,
        "created_at": user.created_at.isoformat(),
        "last_login_at": user.last_login_at.isoformat(),
        "is_active": user.is_active,
    })
    return user


@pytest.fixture
def mock_catalog_response():
    """
    Fixture providing a mock catalog API response.
    
    Returns:
        Dictionary representing a catalog response
    """
    return {
        "region": "eu-west-2",
        "currency": "EUR",
        "fetched_at": datetime.utcnow().isoformat(),
        "entry_count": 2,
        "entries": [
            {
                "Service": "Compute",
                "Category": "compute",
                "Operation": "RunInstances",
                "ResourceType": "t2.micro",
                "Price": "0.10",
                "Unit": "Hour",
                "Flags": ""
            },
            {
                "Service": "Storage",
                "Category": "storage",
                "Operation": "CreateVolume",
                "ResourceType": "io1",
                "Price": "0.15",
                "Unit": "GB-Month",
                "Flags": "PER_MONTH"
            }
        ]
    }


@pytest.fixture
def mock_consumption_response():
    """
    Fixture providing a mock consumption API response.
    
    Returns:
        Dictionary representing a consumption response
    """
    return {
        "region": "eu-west-2",
        "currency": "EUR",
        "fetched_at": datetime.utcnow().isoformat(),
        "from_date": "2024-01-01",
        "to_date": "2024-01-02",
        "entry_count": 2,
        "entries": [
            {
                "Date": "2024-01-01",
                "Service": "Compute",
                "ResourceType": "t2.micro",
                "Quantity": "24.0",
                "Unit": "Hour",
                "Cost": "2.40"
            },
            {
                "Date": "2024-01-01",
                "Service": "Storage",
                "ResourceType": "io1",
                "Quantity": "100.0",
                "Unit": "GB-Month",
                "Cost": "15.00"
            }
        ]
    }


@pytest.fixture
def mock_cost_response():
    """
    Fixture providing a mock cost API response.
    
    Returns:
        Dictionary representing a cost response
    """
    return {
        "region": "eu-west-2",
        "currency": "EUR",
        "fetched_at": datetime.utcnow().isoformat(),
        "resources": [
            {
                "resource_id": "i-1234567890abcdef0",
                "resource_type": "vm",
                "region": "eu-west-2",
                "zone": "eu-west-2a",
                "cost_per_hour": 0.10,
                "cost_per_month": 72.00,
                "cost_per_year": 876.00,
                "specs": {
                    "vm_type": "t2.micro",
                    "tenancy": "default"
                }
            }
        ],
        "totals": {
            "resource_count": 1,
            "resource_type_count": 1,
            "cost_per_hour": 0.10,
            "cost_per_month": 72.00,
            "cost_per_year": 876.00
        },
        "breakdown": {
            "by_resource_type": {
                "vm": {
                    "count": 1,
                    "cost_per_hour": 0.10,
                    "cost_per_month": 72.00
                }
            },
            "by_category": {
                "compute": {
                    "count": 1,
                    "cost_per_hour": 0.10,
                    "cost_per_month": 72.00
                }
            }
        }
    }


@pytest.fixture
def mock_flask_app():
    """
    Fixture providing a Flask test application.
    
    Returns:
        Flask application instance for testing
    """
    from backend.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def db_session():
    """
    Fixture providing a database session for testing.
    
    Note: This fixture should be used with care to ensure proper cleanup.
    For integration tests, prefer using the actual database with transaction rollback.
    
    Yields:
        Database session
    """
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_quote_data():
    """
    Fixture providing sample quote data for testing.
    
    Returns:
        Dictionary with sample quote data
    """
    return {
        "name": "Test Quote",
        "duration": 100,
        "duration_unit": "hours",
        "commitment_period": None,
        "global_discount_percent": 0.0,
        "items": [
            {
                "id": str(uuid.uuid4()),
                "resource_name": "t2.micro",
                "quantity": 2.0,
                "unit_price": 0.10,
                "resource_data": {
                    "Category": "compute",
                    "Flags": ""
                }
            }
        ]
    }


@pytest.fixture
def sample_budget_data():
    """
    Fixture providing sample budget data for testing.
    
    Returns:
        Dictionary with sample budget data
    """
    return {
        "name": "Test Budget",
        "amount": 1000.0,
        "period_type": "monthly",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }

