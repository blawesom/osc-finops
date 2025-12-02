# OSC-FinOps Live Test Environment Setup

> **Note**: This file is located in `tests/` directory. Run commands from project root.

## ✅ Setup Complete!

The live test environment has been configured. Here's what was created:

### Files Created

1. **setup.sh** - Automated setup script (creates venv, installs dependencies)
2. **start.sh** - Server startup script
3. **run_dev.py** - Alternative Python-based server runner
4. **test_health.py** - Health check test script
5. **TESTING.md** - Comprehensive testing guide
6. **QUICK_START.md** - Quick start instructions

### Next Steps to Run the Server

#### Option 1: Automated Setup (Recommended)

```bash
# Install python3-venv if needed (one-time)
sudo apt install python3-venv

# Run setup
./setup.sh

# Start server
./start.sh
```

#### Option 2: Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python3 run_dev.py
```

#### Option 3: Using Flask CLI

```bash
# Install dependencies first
pip install -r requirements.txt

# Set environment
export FLASK_APP=backend.app
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run
python -m flask run --host=0.0.0.0 --port=5000 --debug
```

### Verify Installation

After installing dependencies, test the setup:

```bash
# Test imports
python3 -c "from backend.app import create_app; print('✓ App imports OK')"

# Test health endpoint (after starting server)
python3 tests/integration/test_health.py
```

### Access Points

Once the server is running:

- **Frontend UI**: http://localhost:5000
- **Health Check**: http://localhost:5000/health
- **API Base**: http://localhost:5000/api
- **Login Endpoint**: http://localhost:5000/api/auth/login

### Testing the Application

1. **Start the server** using one of the methods above
2. **Open browser** to http://localhost:5000
3. **Test login**:
   - Enter Outscale Access Key
   - Enter Outscale Secret Key
   - Select region (cloudgouv-eu-west-1, eu-west-2, us-west-1, or us-east-2)
   - Click "Login"
4. **Verify**:
   - Main application interface appears
   - Session info shows in header
   - Tabs are functional

### API Testing

Test the API endpoints with curl:

```bash
# Health check
curl http://localhost:5000/health

# Login (replace with your credentials)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "access_key": "YOUR_ACCESS_KEY",
    "secret_key": "YOUR_SECRET_KEY",
    "region": "eu-west-2"
  }'
```

### Project Structure

```
osc-finops/
├── backend/              # Python backend
│   ├── api/             # API endpoints
│   ├── auth/            # Authentication module
│   ├── config/           # Configuration
│   ├── middleware/       # Middleware (auth decorators)
│   ├── utils/            # Utilities
│   └── app.py           # Flask application
├── frontend/            # Frontend files
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript modules
│   └── index.html       # Main HTML
├── setup.sh                    # Setup script
├── start.sh                    # Start script
├── run_dev.py                  # Python server runner
└── tests/                      # Test files
    ├── integration/
    │   └── test_health.py     # Health check test
    └── scripts/
        └── test_setup.sh      # Setup verification
```

### Environment Configuration

Configuration is in `backend/config/settings.py`. Key settings:

- **Supported Regions**: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2
- **Session Timeout**: 30 minutes (1800 seconds)
- **Server Port**: 5000
- **CORS**: Enabled for all origins in development

### Troubleshooting

**Dependencies not installed?**
```bash
pip install -r requirements.txt
```

**Virtual environment issues?**
```bash
sudo apt install python3-venv
./setup.sh
```

**Port 5000 in use?**
```bash
# Use different port
export SERVER_PORT=5001
python3 run_dev.py
```

**Import errors?**
- Make sure you're in project root: `/home/outscale/osc-finops`
- Verify dependencies: `pip list | grep flask`
- Check Python path: `python3 -c "import sys; print(sys.path)"`

### Phase 1 Features Ready

✅ Backend authentication module
✅ Session management (in-memory, 30min timeout)
✅ Region validation (4 supported regions)
✅ Credential validation via Outscale API
✅ Frontend login UI
✅ Session persistence
✅ Logout functionality
✅ API endpoints: /api/auth/login, /api/auth/logout, /api/auth/session

### Ready for Testing!

The application is ready for Phase 1 validation. See [tests/TESTING.md](TESTING.md) for detailed test scenarios.

