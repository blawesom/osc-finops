#!/bin/bash
# Test script for OSC-FinOps setup verification
# Run from project root: ./tests/scripts/test_setup.sh

cd "$(dirname "$0")/../.." || exit 1

echo "Testing OSC-FinOps setup..."
echo ""

# Check Python
echo "Python version:"
python3 --version
echo ""

# Check if Flask is available
echo "Checking Flask..."
if python3 -c "import flask" 2>/dev/null; then
    python3 -c "import flask; print(f'✓ Flask {flask.__version__} is installed')"
else
    echo "✗ Flask is not installed"
    echo "  Run: pip install -r requirements.txt"
fi
echo ""

# Check if osc-sdk-python is available
echo "Checking osc-sdk-python..."
if python3 -c "from osc_sdk_python import Gateway" 2>/dev/null; then
    echo "✓ osc-sdk-python is installed"
else
    echo "✗ osc-sdk-python is not installed"
    echo "  Run: pip install osc-sdk-python"
fi
echo ""

# Test imports
echo "Testing backend imports..."
if python3 -c "import sys; sys.path.insert(0, '.'); from backend.app import create_app" 2>/dev/null; then
    echo "✓ Backend imports work"
else
    echo "✗ Backend imports failed"
    python3 -c "import sys; sys.path.insert(0, '.'); from backend.app import create_app" 2>&1 | head -3
fi
echo ""

echo "Setup test complete!"
