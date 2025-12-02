#!/usr/bin/env python3
"""Simple health check test for OSC-FinOps API."""
import os
import sys
import requests

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:5000")

def test_health():
    """Test health check endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health check passed")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ Health check failed: Status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Is it running?")
        print(f"  Try: ./start.sh or python -m flask --app backend.app run")
        return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_auth_endpoints():
    """Test authentication endpoints exist."""
    endpoints = [
        ("POST", "/api/auth/login"),
        ("POST", "/api/auth/logout"),
        ("GET", "/api/auth/session"),
    ]
    
    all_passed = True
    for method, endpoint in endpoints:
        try:
            # Just check if endpoint exists (will get 400/401, not 404)
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            
            # 404 means endpoint doesn't exist, anything else means it exists
            if response.status_code == 404:
                print(f"✗ {method} {endpoint} - Endpoint not found")
                all_passed = False
            else:
                print(f"✓ {method} {endpoint} - Endpoint exists (status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"✗ {method} {endpoint} - Cannot connect to server")
            all_passed = False
        except Exception as e:
            print(f"✗ {method} {endpoint} - Error: {e}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("Testing OSC-FinOps API...")
    print("=" * 50)
    
    health_ok = test_health()
    print()
    
    if health_ok:
        endpoints_ok = test_auth_endpoints()
        print()
        print("=" * 50)
        if endpoints_ok:
            print("All tests passed!")
            sys.exit(0)
        else:
            print("Some endpoint tests failed")
            sys.exit(1)
    else:
        print("=" * 50)
        print("Health check failed. Please start the server first.")
        sys.exit(1)

