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

### Run Health Check Tests

```bash
# Make sure server is running first
python3 run_dev.py

# In another terminal, run health tests
python3 tests/integration/test_health.py
```

### Run All Tests

```bash
# Using pytest (when unit tests are added)
pytest tests/

# With timeout (as per user rules)
pytest --timeout=30 tests/
```

## Test Files

### Integration Tests

- **test_health.py**: Tests health endpoint and API endpoint existence
  - Health check endpoint
  - Authentication endpoints (login, logout, session)

### Test Scripts

- **test_setup.sh**: Verifies environment setup
  - Python version check
  - Dependency verification
  - Import testing

## Documentation

- **TESTING.md**: Comprehensive testing guide with all test scenarios
- **QUICK_START.md**: Quick start instructions for running tests
- **SETUP_COMPLETE.md**: Setup completion summary and verification

## Running Tests

### Prerequisites

1. Install dependencies: `pip install -r requirements.txt`
2. Start the server: `python3 run_dev.py` (in one terminal)
3. Run tests: `python3 tests/integration/test_health.py` (in another terminal)

### Environment Variables

```bash
# Set test server URL (default: http://localhost:5000)
export TEST_BASE_URL=http://localhost:5000

# Run tests
python3 tests/integration/test_health.py
```

## Test Coverage

### Phase 1 Tests (Current)

- ✅ Health check endpoint
- ✅ Authentication endpoints existence
- ✅ Setup verification

### Future Tests

- Unit tests for backend modules
- Integration tests for all API endpoints
- End-to-end tests for user workflows
- Performance tests
- Security tests

## Contributing Tests

When adding new tests:

1. **Unit tests**: Add to `tests/unit/`
2. **Integration tests**: Add to `tests/integration/`
3. **E2E tests**: Add to `tests/e2e/`
4. **Test scripts**: Add to `tests/scripts/`

Follow naming convention: `test_*.py` for Python tests, `test_*.sh` for shell scripts.

