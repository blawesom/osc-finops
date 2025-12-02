#!/usr/bin/env python3
"""
Development server runner for OSC-FinOps.
Can be used without virtual environment if dependencies are installed system-wide.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ.setdefault("FLASK_APP", "backend.app")
os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault("FLASK_DEBUG", "1")

if __name__ == "__main__":
    try:
        from backend.app import create_app
        
        app = create_app()
        
        print("=" * 60)
        print("OSC-FinOps Development Server")
        print("=" * 60)
        print(f"Server starting at: http://localhost:5000")
        print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
        print(f"Debug mode: {os.getenv('FLASK_DEBUG', '0')}")
        print("=" * 60)
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        print()
        
        app.run(host="0.0.0.0", port=5000, debug=True)
    
    except ImportError as e:
        print(f"ERROR: Missing dependency - {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        print("\nOr use the setup script:")
        print("  ./setup.sh")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

