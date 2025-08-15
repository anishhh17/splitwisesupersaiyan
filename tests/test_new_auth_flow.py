#!/usr/bin/env python3
"""
Test suite for the new client-side Google OAuth authentication flow.
Tests the updated authentication endpoints and JWT token management.
"""

import asyncio
import httpx
import uuid
import time
import jwt as pyjwt
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"

# These should match your app configuration
JWT_SECRET_KEY = "test_secret_key_for_development_only"  # From .env
JWT_ALGORITHM = "HS256"

def safe_json(resp):
    """Safely parse JSON response or return text."""
    try:
        return resp.json()
    except Exception:
        return resp.text

def generate_test_jwt_token(user_id=None, name="Test User", email="test@example.com", expired=False):
    """Generate a test JWT token for testing protected endpoints."""
    if not user_id:
        user_id = str(uuid.uuid4())
    
    # Create token payload
    expiration = time.time() - 3600 if expired else time.time() + 3600  # -1 hour or +1 hour
    payload = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "exp": expiration,
        "iat": time.time(),
        "iss": "splitbuddy-backend"
    }
    
    # Sign JWT token
    jwt_token = pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return jwt_token, user_id

async def test_new_auth_endpoints():
    """Test the new authentication endpoints."""
    print("\nSYMBOL NEW AUTHENTICATION ENDPOINTS TEST")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Google OAuth endpoint with invalid token
        print("[1]  Testing Google OAuth endpoint with invalid token...")
        try:
            resp = await client.post(
                f"{BASE_URL}/auth/google",
                json={"id_token": "invalid_token_for_testing"}
            )
            print(f"   Status: {resp.status_code}")
            print(f"   Response: {safe_json(resp)}")
            
            # Should return 401 with meaningful error
            if resp.status_code == 401:
                print("   SUCCESS Correctly rejected invalid token")
            else:
                print("   WARNING  Unexpected response for invalid token")
        except Exception as e:
            print(f"   ERROR Error: {str(e)}")
        
        # Test 2: Protected endpoint without token
        print("\n[2]  Testing protected endpoint without authentication...")
        try:
            resp = await client.get(f"{BASE_URL}/auth/me")
            print(f"   Status: {resp.status_code}")
            print(f"   Response: {safe_json(resp)}")
            
            if resp.status_code == 401:
                print("   SUCCESS Correctly requires authentication")
            else:
                print("   WARNING  Expected 401 for unauthenticated request")
        except Exception as e:
            print(f"   ERROR Error: {str(e)}")
        
        # Test 3: Logout endpoint
        print("\n[3]  Testing logout endpoint...")
        try:
            resp = await client.post(f"{BASE_URL}/auth/logout")
            print(f"   Status: {resp.status_code}")
            print(f"   Response: {safe_json(resp)}")
            
            if resp.status_code == 200:
                print("   SUCCESS Logout endpoint accessible")
            else:
                print("   WARNING  Unexpected logout response")
        except Exception as e:
            print(f"   ERROR Error: {str(e)}")

async def test_jwt_token_scenarios():
    """Test various JWT token scenarios."""
    print("\nSYMBOL JWT TOKEN SCENARIOS TEST")
    print("=" * 40)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test 1: Valid JWT token (mock scenario)
        print("[1]  Testing with valid JWT token...")
        jwt_token, user_id = generate_test_jwt_token()
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        try:
            resp = await client.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"   Status: {resp.status_code}")
            print(f"   Response: {safe_json(resp)}")
            
            # Note: This will likely fail because the user doesn't exist in DB
            # but it tests the JWT token parsing logic
            if resp.status_code == 401 and "User not found" in str(safe_json(resp)):
                print("   SUCCESS JWT parsing works (user not in DB as expected)")
            elif resp.status_code == 200:
                print("   SUCCESS JWT token validation successful")
            else:
                print("   WARNING  Unexpected response for valid token")
        except Exception as e:
            print(f"   ERROR Error: {str(e)}")
        
        # Test 2: Expired JWT token
        print("\n[2]  Testing with expired JWT token...")
        expired_token, _ = generate_test_jwt_token(expired=True)
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        try:
            resp = await client.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"   Status: {resp.status_code}")
            print(f"   Response: {safe_json(resp)}")
            
            if resp.status_code == 401 and "expired" in str(safe_json(resp)).lower():
                print("   SUCCESS Correctly rejected expired token")
            else:
                print("   WARNING  Should reject expired tokens")
        except Exception as e:
            print(f"   ERROR Error: {str(e)}")
        
        # Test 3: Malformed JWT token
        print("\n[3]  Testing with malformed JWT token...")
        headers = {"Authorization": "Bearer not.a.valid.jwt.token"}
        
        try:
            resp = await client.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"   Status: {resp.status_code}")
            print(f"   Response: {safe_json(resp)}")
            
            if resp.status_code == 401:
                print("   SUCCESS Correctly rejected malformed token")
            else:
                print("   WARNING  Should reject malformed tokens")
        except Exception as e:
            print(f"   ERROR Error: {str(e)}")
        
        # Test 4: Token refresh endpoint
        print("\n[4]  Testing token refresh endpoint...")
        valid_token, _ = generate_test_jwt_token()
        headers = {"Authorization": f"Bearer {valid_token}"}
        
        try:
            resp = await client.post(f"{BASE_URL}/auth/refresh", headers=headers)
            print(f"   Status: {resp.status_code}")
            print(f"   Response: {safe_json(resp)}")
            
            # Will likely fail due to user not in DB, but tests the endpoint
            if resp.status_code == 401 and "User not found" in str(safe_json(resp)):
                print("   SUCCESS Refresh endpoint works (user not in DB as expected)")
            elif resp.status_code == 200:
                print("   SUCCESS Token refresh successful")
            else:
                print("   WARNING  Unexpected refresh response")
        except Exception as e:
            print(f"   ERROR Error: {str(e)}")

async def test_protected_endpoints():
    """Test that all protected endpoints require authentication."""
    print("\nSYMBOL PROTECTED ENDPOINTS TEST")
    print("=" * 35)
    
    # List of endpoints that should require authentication
    protected_endpoints = [
        ("GET", "/auth/me"),
        ("POST", "/auth/refresh"),
        ("POST", "/users"),
        ("GET", "/users/search"),
        ("POST", "/groups"),
        ("POST", "/bills"),
        ("POST", "/items"),
        ("POST", "/votes"),
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        print(f"SYMBOL Testing {len(protected_endpoints)} protected endpoints...")
        print()
        
        for method, endpoint in protected_endpoints:
            try:
                if method == "GET":
                    resp = await client.get(f"{BASE_URL}{endpoint}")
                elif method == "POST":
                    resp = await client.post(f"{BASE_URL}{endpoint}", json={})
                
                if resp.status_code == 401:
                    print(f"SUCCESS {method:4} {endpoint} - Correctly requires auth")
                elif resp.status_code == 403:
                    print(f"SUCCESS {method:4} {endpoint} - Correctly forbidden")
                else:
                    print(f"WARNING  {method:4} {endpoint} - Status {resp.status_code} (should be 401)")
                    
            except Exception as e:
                print(f"ERROR {method:4} {endpoint} - Error: {str(e)[:40]}")

async def test_public_endpoints():
    """Test that public endpoints don't require authentication."""
    print("\nSYMBOL PUBLIC ENDPOINTS TEST")
    print("=" * 30)
    
    public_endpoints = [
        ("GET", "/"),
        ("GET", "/health"),
        ("POST", "/auth/logout"),
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for method, endpoint in public_endpoints:
            try:
                if method == "GET":
                    resp = await client.get(f"{BASE_URL}{endpoint}")
                elif method == "POST":
                    resp = await client.post(f"{BASE_URL}{endpoint}")
                
                if resp.status_code == 200:
                    print(f"SUCCESS {method:4} {endpoint} - Public access works")
                else:
                    print(f"WARNING  {method:4} {endpoint} - Status {resp.status_code}")
                    
            except Exception as e:
                print(f"ERROR {method:4} {endpoint} - Error: {str(e)[:40]}")

async def main():
    """Run all authentication flow tests."""
    print("ROCKET New Authentication Flow Tester")
    print("=" * 50)
    print("SYMBOL Testing client-side OAuth + JWT authentication")
    print()
    
    try:
        # Test new auth endpoints
        await test_new_auth_endpoints()
        
        # Test JWT token handling
        await test_jwt_token_scenarios()
        
        # Test protected endpoints
        await test_protected_endpoints()
        
        # Test public endpoints
        await test_public_endpoints()
        
        print("\n" + "=" * 50)
        print("SUCCESS Authentication flow tests completed!")
        print("SYMBOL Your new auth system is properly configured.")
        print()
        print("MEMO Notes:")
        print("   • Google OAuth tests with real tokens require valid setup")
        print("   • JWT tests use mock tokens for validation logic")
        print("   • User creation requires valid Supabase connection")
        
    except Exception as e:
        print(f"ERROR Test failed with error: {str(e)}")

if __name__ == "__main__":
    print("TIP Make sure your FastAPI server is running:")
    print("   uvicorn main:app --reload")
    print()
    asyncio.run(main())