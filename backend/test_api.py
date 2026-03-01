"""
Test script to verify API endpoints
"""
import httpx
import sys

BASE_URL = "http://localhost:9090"

def test_endpoints():
    print("Testing Career Planning AI Agent API")
    print("=" * 50)

    try:
        # Test root endpoint
        print("\n1. Testing GET /")
        response = httpx.get(f"{BASE_URL}/", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        # Test health endpoint
        print("\n2. Testing GET /health")
        response = httpx.get(f"{BASE_URL}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        # Test database health endpoint
        print("\n3. Testing GET /health/db")
        response = httpx.get(f"{BASE_URL}/health/db", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        print("\n" + "=" * 50)
        print("All tests passed!")
        return 0

    except httpx.ConnectError as e:
        print(f"\nError: Could not connect to server at {BASE_URL}")
        print(f"Make sure the server is running: uvicorn app.main:app --reload")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_endpoints())
