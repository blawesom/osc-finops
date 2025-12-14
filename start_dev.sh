#!/bin/bash
# Start script for OSC-FinOps development server

set -e

# Check if virtual environment exists, if so use it
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "Using virtual environment..."
    source venv/bin/activate
else
    echo "No virtual environment found. Using system Python."
    echo "Make sure dependencies are installed: pip install -r requirements.txt"
fi

# Set Flask environment variables
export FLASK_APP=backend.app
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start Flask development server
echo "Starting OSC-FinOps development server..."
echo "Server will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""
echo "To test the server, run in another terminal:"
echo "  python3 tests/integration/test_health.py"
echo ""

# Try using run_dev.py first (works without venv)
if [ -f "run_dev.py" ]; then
    python3 run_dev.py
else
    # Fallback to flask command
    export FLASK_APP=backend.app
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    python -m flask run --host=0.0.0.0 --port=8000 --debug
fi

