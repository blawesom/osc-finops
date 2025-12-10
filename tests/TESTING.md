# OSC-FinOps Testing Guide

> **Note**: This file is located in `tests/` directory. Run commands from project root.

## Quick Start

### 1. Setup Environment

```bash
# Run setup script (creates venv and installs dependencies)
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Development Server

```bash
# Using start script
./start.sh

# Or manually:
source venv/bin/activate
export FLASK_APP=backend.app
export FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=8000 --debug
```

The server will be available at: **http://localhost:8000**

### 3. Test the Application

#### Health Check
```bash
# In another terminal
curl http://localhost:8000/health

# Or use the test script (from project root)
python3 tests/integration/test_health.py
```

#### Manual Testing

1. **Open Browser**: Navigate to http://localhost:8000

2. **Test Login**:
   - Enter valid Outscale Access Key
   - Enter valid Outscale Secret Key
   - Select a region (cloudgouv-eu-west-1, eu-west-2, us-west-1, or us-east-2)
   - Click "Login"
   - Should see main application interface

3. **Test Session**:
   - After login, check session info in header
   - Session should show region and expiration time
   - Try refreshing page - should stay logged in

4. **Test Logout**:
   - Click "Logout" button
   - Should return to login screen
   - Session should be cleared

#### API Testing with curl

**Login**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "access_key": "YOUR_ACCESS_KEY",
    "secret_key": "YOUR_SECRET_KEY",
    "region": "eu-west-2"
  }'
```

**Check Session**:
```bash
curl http://localhost:8000/api/auth/session?session_id=YOUR_SESSION_ID
```

**Logout**:
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: YOUR_SESSION_ID" \
  -d '{"session_id": "YOUR_SESSION_ID"}'
```

## Test Scenarios

### TS-1.1: Login with Valid Credentials and Region
1. Use valid Outscale credentials
2. Select a supported region
3. Should receive session_id in response
4. Should be able to access main application

### TS-1.2: Login with Invalid Credentials
1. Use invalid credentials
2. Should receive 401 error
3. Should see error message
4. No session should be created

### TS-1.2a: Login without Region
1. Submit login form without selecting region
2. Should receive 400 error
3. Error should indicate region is required

### TS-1.2b: Login with Invalid Region
1. Try to login with region="invalid-region"
2. Should receive 400 error
3. Error should list supported regions

### TS-1.3: Session Expiration
1. Login successfully
2. Wait 30 minutes (or modify SESSION_TIMEOUT in settings)
3. Try to access protected endpoint
4. Should receive 401 error
5. Should be redirected to login

### TS-1.4: Logout
1. Login successfully
2. Call logout endpoint
3. Session should be deleted
4. Subsequent requests with same session_id should fail

### TS-1.5: Session Check
1. Login successfully
2. Call /api/auth/session endpoint
3. Should receive session information
4. Should include region and expiration time

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use: `lsof -i :8000`
- Make sure virtual environment is activated
- Check that all dependencies are installed: `pip list`

### Import errors
- Make sure you're in the project root directory
- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Authentication fails
- Verify credentials are valid for the selected region
- Check network connectivity to Outscale API
- Check browser console for errors
- Check server logs for detailed error messages

### CORS errors
- Make sure CORS is configured in `backend/app.py`
- Check browser console for CORS error details
- Verify frontend is being served from the same origin

## Development Tips

### Viewing Logs
Flask debug mode shows logs in the terminal where the server is running.

### Testing Different Regions
Make sure your credentials are valid for the region you're testing:
- cloudgouv-eu-west-1
- eu-west-2
- us-west-1
- us-east-2

### Session Management
Sessions are stored in-memory, so:
- Restarting the server clears all sessions
- Sessions expire after 30 minutes of inactivity
- Maximum session timeout is configurable in `backend/config/settings.py`

## Next Steps

After Phase 1 validation:
- Phase 2: Catalog Integration & Quote Building
- Phase 3: Consumption History
- Phase 4: Current Cost Evaluation

