# OSC-FinOps Tests

This directory contains all testing-related files for OSC-FinOps.

## Directory Structure

```
tests/
├── unit/              # Unit tests (to be implemented)
├── integration/       # Integration tests
│   └── test_health.py # Health check and API endpoint tests
├── e2e/              # End-to-end tests (to be implemented)
├── scripts/          # Test utility scripts
│   └── test_setup.sh # Setup verification script
├── utils/            # Test utilities
│   └── credential_helpers.py # Credential validation helpers
├── conftest.py       # Pytest configuration and fixtures
├── TESTING.md        # Comprehensive testing guide
├── QUICK_START.md    # Quick start instructions
└── SETUP_COMPLETE.md # Setup completion summary
```

## Quick Start

### Run Setup Verification

```bash
# From project root
./tests/scripts/test_setup.sh
```

### Run Tests with pytest

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests (unit tests run, integration/e2e skip if no credentials)
pytest tests/ --timeout=30

# Run only unit tests (no credentials needed)
pytest tests/unit/ --timeout=30

# Run only integration tests
pytest tests/integration/ --timeout=30

# Run only tests requiring credentials
pytest tests/ -m requires_credentials --timeout=30

# Run tests excluding those requiring credentials
pytest tests/ -m "not requires_credentials" --timeout=30
```

## Environment Variables

### Required for Integration/E2E Tests

Integration and end-to-end tests that make real API calls require Outscale credentials:

```bash
# Set credentials (required only for integration/e2e tests)
export OSC_ACCESS_KEY="your_outscale_access_key"
export OSC_SECRET_KEY="your_outscale_secret_key"
export OSC_REGION="eu-west-2"  # or cloudgouv-eu-west-1, us-west-1, us-east-2
```

### Optional Configuration

```bash
# Set test server URL (default: http://localhost:8000)
export TEST_BASE_URL=http://localhost:8000
```

## Test Behavior

- **Unit tests**: Run without credentials - no environment variables needed
- **Integration/e2e tests**: 
  - If credentials are missing: Tests are skipped with a clear warning message
  - If credentials are present: Tests run normally
  - Warning message: "Skipping test: OSC_ACCESS_KEY, OSC_SECRET_KEY, and OSC_REGION environment variables required"

## Prerequisites

1. Install dependencies: `pip install -r requirements.txt`
2. Start the server (for integration tests): `python3 run_dev.py` (in one terminal)
3. Set credentials (for tests marked with `@pytest.mark.requires_credentials`)
4. Run tests: `pytest tests/ --timeout=30` (in another terminal)

## Test Files

### Integration Tests

- **test_health.py**: Tests health endpoint and API endpoints
  - `test_health()` - Health check endpoint (no credentials needed)
  - `test_auth_endpoints()` - Authentication endpoints existence (no credentials needed)
  - `test_login_with_valid_credentials()` - Login with valid credentials (requires credentials)
  - `test_session_check()` - Session check endpoint (requires credentials)
  - `test_logout()` - Logout endpoint (requires credentials)

### Test Scripts

- **test_setup.sh**: Verifies environment setup
  - Python version check
  - Dependency verification
  - Import testing

## Pytest Fixtures

The following fixtures are available in `conftest.py`:

- `test_base_url`: Base URL for API testing (from `TEST_BASE_URL` env var, default: `http://localhost:8000`)
- `test_credentials`: Dictionary with credentials from environment variables
  - Automatically skips test if credentials are missing
  - Returns: `{"access_key": "...", "secret_key": "...", "region": "..."}`
- `authenticated_session`: Authenticated session for API tests
  - Creates a session by logging in with test credentials
  - Returns: Session information including `session_id`, `region`, `expires_at`
  - Automatically skips test if credentials are missing or login fails

## Pytest Markers

- `@pytest.mark.requires_credentials`: Marks tests that require valid Outscale credentials
  - Use this marker for integration/e2e tests that make real API calls
  - Tests without this marker can run without credentials

## Documentation

- **TESTING.md**: Comprehensive testing guide with all test scenarios
- **QUICK_START.md**: Quick start instructions for running tests
- **SETUP_COMPLETE.md**: Setup completion summary and verification

## Test Coverage

### Phase 1 Tests (Current)

- ✅ Health check endpoint
- ✅ Authentication endpoints existence
- ✅ Login with valid credentials (requires credentials)
- ✅ Session check (requires credentials)
- ✅ Logout (requires credentials)
- ✅ Setup verification

### Future Tests

- Unit tests for backend modules
- Integration tests for all API endpoints
- End-to-end tests for user workflows
- Performance tests
- Security tests

## Contributing Tests

When adding new tests:

1. **Unit tests**: Add to `tests/unit/` - No credentials needed
2. **Integration tests**: Add to `tests/integration/` - Use `@pytest.mark.requires_credentials` if real API calls are needed
3. **E2E tests**: Add to `tests/e2e/` - Use `@pytest.mark.requires_credentials` for real API calls
4. **Test scripts**: Add to `tests/scripts/`

Follow naming convention: `test_*.py` for Python tests, `test_*.sh` for shell scripts.

## Example: Running Tests

```bash
# Example 1: Run all tests (unit tests run, integration skip if no credentials)
pytest tests/ --timeout=30

# Example 2: Run only tests that don't require credentials
pytest tests/ -m "not requires_credentials" --timeout=30

# Example 3: Run integration tests with credentials set
export OSC_ACCESS_KEY="your_key"
export OSC_SECRET_KEY="your_secret"
export OSC_REGION="eu-west-2"
pytest tests/integration/ --timeout=30

# Example 4: Run with verbose output
pytest tests/ -v --timeout=30

# Example 5: Run specific test file
pytest tests/integration/test_health.py --timeout=30
```
