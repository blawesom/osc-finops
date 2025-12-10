# OSC-FinOps Quick Start Guide

> **Note**: This file is located in `tests/` directory. Run commands from project root.

## Option 1: Using Setup Scripts (Recommended)

```bash
# 1. Setup environment (creates venv, installs dependencies)
./setup.sh

# 2. Start server
./start.sh
```

## Option 2: Direct Python Execution

If you have dependencies installed system-wide or prefer not to use venv:

```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run development server
python3 run_dev.py
```

## Option 3: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export FLASK_APP=backend.app
export FLASK_ENV=development
export FLASK_DEBUG=1

# 4. Start server
python -m flask run --host=0.0.0.0 --port=8000 --debug
```

## Access the Application

Once the server is running:
- **Frontend**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Base**: http://localhost:8000/api

## Test the Setup

```bash
# Health check
curl http://localhost:8000/health

# Or use test script (from project root)
python3 tests/integration/test_health.py
```

## Troubleshooting

### Virtual Environment Issues

If `python3 -m venv` fails:
```bash
# Install python3-venv package
sudo apt install python3-venv
# Or for specific Python version:
sudo apt install python3.12-venv
```

### Port Already in Use

If port 8000 is busy:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process or use different port
export SERVER_PORT=8001
```

### Import Errors

If you see import errors:
```bash
# Make sure you're in project root
cd /home/outscale/osc-finops

# Reinstall dependencies
pip install -r requirements.txt
```

## Next Steps

1. Open http://localhost:8000 in your browser
2. Test login with valid Outscale credentials
3. Select a supported region
4. Verify session management works

For detailed testing scenarios, see [TESTING.md](TESTING.md).

