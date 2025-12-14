#!/bin/bash
# Production startup script for OSC-FinOps
# Uses gunicorn WSGI server for production deployment

set -e

# Check if virtual environment exists
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "WARNING: No virtual environment found. Using system Python."
    echo "Make sure production dependencies are installed: pip install -r requirements.txt"
fi

# Check if gunicorn is installed
if ! python3 -c "import gunicorn" 2>/dev/null; then
    echo "ERROR: gunicorn is not installed."
    echo "Install it with: pip install -r requirements.txt"
    exit 1
fi

# Set production environment variables if not already set
export FLASK_ENV=${FLASK_ENV:-production}
export FLASK_DEBUG=${FLASK_DEBUG:-0}

# Validate SECRET_KEY is set in production
if [ "$FLASK_ENV" = "production" ] && [ -z "$SECRET_KEY" ]; then
    echo "WARNING: SECRET_KEY is not set. Using default (INSECURE for production)."
    echo "Set SECRET_KEY environment variable for production deployment."
fi

# Get configuration from environment or use defaults
WORKERS=${GUNICORN_WORKERS:-4}
THREADS=${GUNICORN_THREADS:-2}
TIMEOUT=${GUNICORN_TIMEOUT:-120}
BIND_ADDRESS=${BIND_ADDRESS:-0.0.0.0:8000}

echo "=========================================="
echo "OSC-FinOps Production Server"
echo "=========================================="
echo "Environment: $FLASK_ENV"
echo "Workers: $WORKERS"
echo "Threads: $THREADS"
echo "Timeout: $TIMEOUT seconds"
echo "Bind: $BIND_ADDRESS"
echo "=========================================="
echo ""

# Start gunicorn
exec gunicorn \
    --bind "$BIND_ADDRESS" \
    --workers "$WORKERS" \
    --threads "$THREADS" \
    --timeout "$TIMEOUT" \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload \
    "backend.app:create_app()"
