import asyncio
import httpx
import uuid
import time
import jwt as pyjwt
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

BASE_URL = "http://127.0.0.1:8000"
JWT_SECRET_KEY = "super-secret-jwt-key-change-in-production"  # Use same key from main.py
JWT_ALGORITHM = "HS256"

def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return resp.text

def generate_test_token(user_id=None, name="Test User", email="test@example.com", expired=False):
    """Generate a test JWT token"""
    if not user_id:
        user_id = str(uuid.uuid4())
    
    # Create token payload
    expiration = time.time() - 3600 if expired else time.time() + 3600  # -1 hour or +1 hour
    payload = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "exp": expiration
    }
    
    # Sign JWT token
    jwt_token = pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return jwt_token, user_id

async def test_auth_endpoints():
    """Test the authentication endpoints (login, auth, logout)"""
    async with httpx.AsyncClient(follow_redirects=False) as client:
        print("\n--- TESTING AUTH ENDPOINTS ---")
        
        # Test login endpoint - should redirect to Google OAuth
        resp = await client.get(f"{BASE_URL}/login")
        print(f"Login endpoint: {resp.status_code}")
        
        assert resp.status_code == 307, "Expected redirect from login endpoint"
        redirect_url = resp.headers.get("location", "")
        assert "accounts.google.com" in redirect_url, f"Expected Google OAuth URL, got: {redirect_url}"
        
        # Test logout endpoint - should clear cookie
        resp = await client.get(f"{BASE_URL}/logout")
        print(f"Logout endpoint: {resp.status_code}")
        
        assert resp.status_code == 200, "Expected 200 OK from logout endpoint"
        assert "auth_token" in resp.headers.get("set-cookie", ""), "Expected auth_token cookie to be cleared"
        
        print("Auth endpoint flow cannot be fully tested without Google OAuth credentials")

async def test_token_validation():
    """Test various token validation scenarios"""
    print("\n--- TESTING TOKEN VALIDATION ---")
    
    # 1. Valid token format (but not in DB)
    valid_token, _ = generate_test_token()
    headers = {"Authorization": f"Bearer {valid_token}"}
    
    # 2. Expired token
    expired_token, _ = generate_test_token(expired=True)
    expired_headers = {"Authorization": f"Bearer {expired_token}"}
    
    # 3. Invalid token format
    invalid_token = "invalid.token.format"
    invalid_headers = {"Authorization": f"Bearer {invalid_token}"}
    
    # No headers for missing token test
    
    async with httpx.AsyncClient() as client:
        # Test with valid token format (but not in DB)
        resp = await client.get(f"{BASE_URL}/me", headers=headers)
        print(f"Valid token format: {resp.status_code}")
        print(f"Response: {safe_json(resp)}")
        # In a test environment without DB setup, we expect 401 even with valid token format
        assert resp.status_code in (401, 403), f"Expected auth error with token not in DB, got {resp.status_code}"
        
        # Test with expired token
        resp = await client.get(f"{BASE_URL}/me", headers=expired_headers)
        print(f"Expired token: {resp.status_code}")
        print(f"Response: {safe_json(resp)}")
        assert resp.status_code in (401, 403), f"Expected auth error with expired token, got {resp.status_code}"
        
        # Test with invalid token
        resp = await client.get(f"{BASE_URL}/me", headers=invalid_headers)
        print(f"Invalid token: {resp.status_code}")
        print(f"Response: {safe_json(resp)}")
        assert resp.status_code in (401, 403), f"Expected auth error with invalid token, got {resp.status_code}"
        
        # Test with missing token (no Authorization header)
        resp = await client.get(f"{BASE_URL}/me")
        print(f"Missing token: {resp.status_code}")
        print(f"Response: {safe_json(resp)}")
        assert resp.status_code in (401, 403), f"Expected auth error with missing token, got {resp.status_code}"
        
        # Test with cookie auth
        cookies = {"auth_token": valid_token}
        resp = await client.get(f"{BASE_URL}/me", cookies=cookies)
        print(f"Cookie auth: {resp.status_code}")
        print(f"Response: {safe_json(resp)}")
        assert resp.status_code in (401, 403), f"Expected auth error with cookie auth, got {resp.status_code}"

async def test_public_endpoints():
    """Test that public endpoints work without authentication"""
    print("\n--- TESTING PUBLIC ENDPOINTS ---")
    
    public_endpoints = [
        f"{BASE_URL}/login", 
        f"{BASE_URL}/logout",
        f"{BASE_URL}/test-supabase"
    ]
    
    async with httpx.AsyncClient() as client:
        for endpoint in public_endpoints:
            resp = await client.get(endpoint)
            print(f"{endpoint}: {resp.status_code}")
            # Just checking that these don't return 401
            assert resp.status_code != 401, f"Public endpoint {endpoint} shouldn't require auth"

async def main():
    # Test auth endpoints
    await test_auth_endpoints()
    
    # Test token validation
    await test_token_validation()
    
    # Test public endpoints
    await test_public_endpoints()

if __name__ == "__main__":
    asyncio.run(main())
