#!/bin/bash
# Setup script for OSC-FinOps development environment

set -e

echo "Setting up OSC-FinOps development environment..."

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    if ! python3 -m venv venv 2>/dev/null; then
        echo "ERROR: python3-venv package is not installed."
        echo "Please install it with: sudo apt install python3-venv"
        echo "Or on Ubuntu/Debian: sudo apt install python3.12-venv"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start the development server, run:"
echo "  python -m flask --app backend.app run --host=0.0.0.0 --port=5000 --debug"
echo ""
echo "Or use the start script:"
echo "  ./start.sh"

