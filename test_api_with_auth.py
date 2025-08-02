import asyncio
import httpx
import uuid
import time
import jwt as pyjwt
from datetime import date, datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"
JWT_SECRET_KEY = "super-secret-jwt-key-change-in-production"  # Use same key from main.py
JWT_ALGORITHM = "HS256"

def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return resp.text

def generate_test_token(user_id=None, name="Test User", email="test@example.com"):
    """Generate a test JWT token"""
    if not user_id:
        user_id = str(uuid.uuid4())
    
    # Create token payload
    expiration = time.time() + 3600  # 1 hour from now
    payload = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "exp": expiration
    }
    
    # Sign JWT token
    jwt_token = pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return jwt_token, user_id

async def test_unauthorized_access():
    """Test that protected endpoints return 401 without a token"""
    async with httpx.AsyncClient() as client:
        # Try to access a protected endpoint without authentication
        print("\n--- UNAUTHORIZED ACCESS TESTS ---")
        
        # Define endpoints with their appropriate HTTP methods
        endpoint_methods = [
            ("get", f"{BASE_URL}/me"),
            ("post", f"{BASE_URL}/users"),
            ("get", f"{BASE_URL}/users/{uuid.uuid4()}"),
            ("post", f"{BASE_URL}/groups"),
            ("get", f"{BASE_URL}/groups/{uuid.uuid4()}"),
            # Add more protected endpoints here
        ]
        
        for method, endpoint in endpoint_methods:
            if method == "get":
                resp = await client.get(endpoint)
            else:
                resp = await client.post(endpoint, json={})
            
            print(f"{method.upper()} {endpoint}: {resp.status_code}")
            assert resp.status_code in (401, 403), f"Expected 401 or 403, got {resp.status_code} for {endpoint}"

async def main():
    # Generate a test token to use for authentication
    jwt_token, user_id = generate_test_token()
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    # Test unauthorized access (should fail with 401 or 403)
    await test_unauthorized_access()
    
    async with httpx.AsyncClient() as client:
        # --- USERS ---
        print("\n--- USERS ---")
        # Test the /me endpoint first (should return our test user)
        resp = await client.get(f"{BASE_URL}/me", headers=headers)
        print("Get me:", resp.status_code, safe_json(resp))
        
        # Check if authentication is successful before continuing
        if resp.status_code >= 400:
            print("\nAuthentication failed. This is expected if no user exists in the database.")
            print("To run the full API tests, you need to:")
            print("1. Set up a proper database connection")
            print("2. Create a test user in the database")
            print("3. Generate a token for that specific user")
            return
            
        # Create a new user
        new_user = {"name": "Alice", "email": f"alice_{uuid.uuid4()}@example.com"}
        resp = await client.post(f"{BASE_URL}/users", json=new_user, headers=headers)
        print("Create user:", resp.status_code, safe_json(resp))
        new_user_id = resp.json()["id"]
        
        # Get user details
        resp = await client.get(f"{BASE_URL}/users/{new_user_id}", headers=headers)
        print("Get user:", resp.status_code, safe_json(resp))
        
        # Get user not found
        resp = await client.get(f"{BASE_URL}/users/{uuid.uuid4()}", headers=headers)
        print("Get user not found:", resp.status_code, safe_json(resp))

        # --- GROUPS ---
        print("\n--- GROUPS ---")
        group = {"name": "Test Group"}
        resp = await client.post(f"{BASE_URL}/groups", json=group, headers=headers)
        print("Create group:", resp.status_code, safe_json(resp))
        group_id = resp.json()["id"]
        
        # Get group
        resp = await client.get(f"{BASE_URL}/groups/{group_id}", headers=headers)
        print("Get group:", resp.status_code, safe_json(resp))
        
        # --- GROUP MEMBERS ---
        print("\n--- GROUP MEMBERS ---")
        membership = {"group_id": group_id, "user_id": new_user_id}
        resp = await client.post(f"{BASE_URL}/group_members", json=membership, headers=headers)
        print("Add user to group:", resp.status_code, safe_json(resp))
        membership_id = resp.json()["id"]
        
        # Get group members
        resp = await client.get(f"{BASE_URL}/groups/{group_id}/members", headers=headers)
        print("Get group members:", resp.status_code, safe_json(resp))
        
        # --- BILLS ---
        print("\n--- BILLS ---")
        bill = {
            "group_id": group_id,
            "payer_id": new_user_id,
            "bill_date": str(date.today())
        }
        resp = await client.post(f"{BASE_URL}/bills", json=bill, headers=headers)
        print("Create bill:", resp.status_code, safe_json(resp))
        bill_id = resp.json()["id"]
        
        # Get bill
        resp = await client.get(f"{BASE_URL}/bills/{bill_id}", headers=headers)
        print("Get bill:", resp.status_code, safe_json(resp))
        
        # Get bill items
        resp = await client.get(f"{BASE_URL}/bills/{bill_id}/items", headers=headers)
        print("Get bill items:", resp.status_code, safe_json(resp))
        
        # Update bill
        update_data = {"payer_id": user_id}  # Change payer to test user
        resp = await client.put(f"{BASE_URL}/bills/{bill_id}", json=update_data, headers=headers)
        print("Update bill:", resp.status_code, safe_json(resp))
        
        # --- ITEMS ---
        print("\n--- ITEMS ---")
        item = {
            "bill_id": bill_id,
            "name": "Test Item",
            "price": 123.45,
            "is_tax_or_tip": False
        }
        resp = await client.post(f"{BASE_URL}/items", json=item, headers=headers)
        print("Create item:", resp.status_code, safe_json(resp))
        item_id = resp.json()["id"]
        
        # Get item
        resp = await client.get(f"{BASE_URL}/items/{item_id}", headers=headers)
        print("Get item:", resp.status_code, safe_json(resp))
        
        # Update item
        item_update = {"price": 150.00}
        resp = await client.put(f"{BASE_URL}/items/{item_id}", json=item_update, headers=headers)
        print("Update item:", resp.status_code, safe_json(resp))
        
        # Vote on item
        vote_data = {"user_id": user_id, "ate": True}
        resp = await client.post(f"{BASE_URL}/items/{item_id}/vote", json=vote_data, headers=headers)
        print("Vote on item:", resp.status_code, safe_json(resp))
        
        # --- VOTES ---
        print("\n--- VOTES ---")
        vote = {
            "item_id": item_id,
            "user_id": new_user_id,
            "ate": True
        }
        resp = await client.post(f"{BASE_URL}/votes", json=vote, headers=headers)
        print("Create vote:", resp.status_code, safe_json(resp))
        vote_id = resp.json()["id"]
        
        # Get vote
        resp = await client.get(f"{BASE_URL}/votes/{vote_id}", headers=headers)
        print("Get vote:", resp.status_code, safe_json(resp))
        
        # Calculate bill split
        resp = await client.get(f"{BASE_URL}/bills/{bill_id}/split", headers=headers)
        print("Calculate bill split:", resp.status_code, safe_json(resp))
        
        # --- TEST COOKIE AUTHENTICATION ---
        print("\n--- COOKIE AUTHENTICATION TEST ---")
        # Create a client that handles cookies automatically
        cookie_client = httpx.AsyncClient(cookies={"auth_token": jwt_token})
        
        # Try accessing an endpoint with cookie auth
        resp = await cookie_client.get(f"{BASE_URL}/me")
        print("Cookie auth - Get me:", resp.status_code, safe_json(resp))

if __name__ == "__main__":
    asyncio.run(main())
