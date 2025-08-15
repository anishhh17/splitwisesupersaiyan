#!/usr/bin/env python3
"""
Test script to verify API endpoint structure for the modular FastAPI application.
Tests endpoint availability without authentication to ensure routes are properly registered.
"""

import asyncio
import httpx
import uuid

# Configuration
BASE_URL = "http://127.0.0.1:8000"

def safe_json(resp):
    """Safely parse JSON response or return text."""
    try:
        return resp.json()
    except Exception:
        return resp.text

async def test_api_structure():
    """
    Test the structure of the API endpoints without authentication.
    This verifies that endpoints exist and are accessible.
    """
    print("\nAPI STRUCTURE TEST")
    print("=" * 50)
    
    # Generate test IDs for parameterized routes
    user_id = str(uuid.uuid4())
    group_id = str(uuid.uuid4())
    bill_id = str(uuid.uuid4())
    item_id = str(uuid.uuid4())
    vote_id = str(uuid.uuid4())
    membership_id = str(uuid.uuid4())
    
    # Define endpoints to check (updated for modular structure)
    endpoints = [
        # Root and Health
        ("GET", f"{BASE_URL}/", "Root endpoint"),
        ("GET", f"{BASE_URL}/health", "Health check"),
        ("GET", f"{BASE_URL}/test-supabase", "Supabase connection test"),
        
        # Authentication (new endpoints)
        ("POST", f"{BASE_URL}/auth/google", "Google OAuth authentication"),
        ("POST", f"{BASE_URL}/auth/refresh", "Token refresh"),
        ("POST", f"{BASE_URL}/auth/logout", "Logout"),
        ("GET", f"{BASE_URL}/auth/me", "Get current user"),
        
        # Users
        ("POST", f"{BASE_URL}/users", "Create user"),
        ("GET", f"{BASE_URL}/users/{user_id}", "Get user by ID"),
        ("GET", f"{BASE_URL}/users/search", "Search users"),
        ("GET", f"{BASE_URL}/users/{user_id}/groups", "Get user groups"),
        
        # Groups
        ("POST", f"{BASE_URL}/groups", "Create group"),
        ("GET", f"{BASE_URL}/groups/{group_id}", "Get group by ID"),
        ("GET", f"{BASE_URL}/groups/{group_id}/members", "Get group members"),
        ("GET", f"{BASE_URL}/groups/{group_id}/bills", "Get group bills"),
        ("POST", f"{BASE_URL}/groups/members", "Add user to group"),
        ("GET", f"{BASE_URL}/groups/members/{membership_id}", "Get group member"),
        ("DELETE", f"{BASE_URL}/groups/members/{membership_id}", "Remove user from group"),
        
        # Bills
        ("POST", f"{BASE_URL}/bills", "Create bill"),
        ("GET", f"{BASE_URL}/bills/{bill_id}", "Get bill by ID"),
        ("PUT", f"{BASE_URL}/bills/{bill_id}", "Update bill"),
        ("DELETE", f"{BASE_URL}/bills/{bill_id}", "Delete bill"),
        ("GET", f"{BASE_URL}/bills/{bill_id}/items", "Get bill items"),
        ("GET", f"{BASE_URL}/bills/{bill_id}/split", "Get bill split calculation"),
        ("POST", f"{BASE_URL}/bills/process-image", "Process bill image"),
        
        # Items
        ("POST", f"{BASE_URL}/items", "Create item"),
        ("GET", f"{BASE_URL}/items/{item_id}", "Get item by ID"),
        ("PUT", f"{BASE_URL}/items/{item_id}", "Update item"),
        ("DELETE", f"{BASE_URL}/items/{item_id}", "Delete item"),
        ("POST", f"{BASE_URL}/items/{item_id}/vote", "Toggle item vote"),
        
        # Votes
        ("POST", f"{BASE_URL}/votes", "Create vote"),
        ("GET", f"{BASE_URL}/votes/{vote_id}", "Get vote by ID"),
        ("DELETE", f"{BASE_URL}/votes/{vote_id}", "Delete vote"),
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        print(f"Testing {len(endpoints)} endpoints...")
        print()
        
        success_count = 0
        
        for method, endpoint, description in endpoints:
            try:
                if method == "GET":
                    resp = await client.get(endpoint)
                elif method == "POST":
                    resp = await client.post(endpoint, json={})
                elif method == "PUT":
                    resp = await client.put(endpoint, json={})
                elif method == "DELETE":
                    resp = await client.delete(endpoint)
                
                # We consider these status codes as "endpoint exists":
                # 200: OK
                # 401: Unauthorized (expected for protected endpoints)
                # 422: Validation Error (expected for endpoints requiring specific data)
                # 400: Bad Request (expected for endpoints with missing required data)
                # 404: Not Found (might indicate endpoint doesn't exist)
                
                if resp.status_code in [200, 401, 422, 400]:
                    status = "PASS"
                    success_count += 1
                elif resp.status_code == 404:
                    status = "FAIL"
                else:
                    status = "WARN"
                
                print(f"{status:4} {method:6} {resp.status_code:3} | {description}")
                
            except Exception as e:
                print(f"ERR  {method:6} ERR | {description} - Error: {str(e)[:50]}")
        
        print()
        print(f"Results: {success_count}/{len(endpoints)} endpoints accessible")
        
        if success_count >= len(endpoints) * 0.8:  # 80% success rate
            print("SUCCESS: API structure looks good!")
            return True
        else:
            print("WARNING: Some endpoints may have issues")
            return False

async def test_docs_endpoints():
    """Test that FastAPI documentation endpoints are available."""
    print("\nDOCUMENTATION ENDPOINTS TEST")
    print("=" * 30)
    
    docs_endpoints = [
        ("GET", f"{BASE_URL}/docs", "Swagger UI documentation"),
        ("GET", f"{BASE_URL}/redoc", "ReDoc documentation"),
        ("GET", f"{BASE_URL}/openapi.json", "OpenAPI schema"),
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for method, endpoint, description in docs_endpoints:
            try:
                resp = await client.get(endpoint)
                if resp.status_code == 200:
                    print(f"PASS {description} - Available")
                else:
                    print(f"WARN {description} - Status {resp.status_code}")
            except Exception as e:
                print(f"FAIL {description} - Error: {str(e)[:50]}")

async def main():
    """Run all API structure tests."""
    print("FastAPI Modular Structure Tester")
    print("=" * 50)
    
    try:
        # Test main API endpoints
        api_success = await test_api_structure()
        
        # Test documentation endpoints
        await test_docs_endpoints()
        
        print("\n" + "=" * 50)
        if api_success:
            print("API structure test completed successfully!")
            print("Your modular FastAPI application is properly structured.")
        else:
            print("API structure test completed with some issues.")
            print("Check the endpoint implementations and routes.")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    # Note: Make sure your FastAPI server is running on localhost:8000
    print("Make sure your FastAPI server is running:")
    print("   uvicorn main:app --reload")
    print()
    asyncio.run(main())