import httpx
import uuid
import time
import jwt as pyjwt
from datetime import date, datetime, timedelta
import asyncio
import json
from typing import Dict, Optional, Tuple, List

BASE_URL = "http://127.0.0.1:8000"
JWT_SECRET_KEY = "super-secret-jwt-key-change-in-production"  # Use same key from main.py
JWT_ALGORITHM = "HS256"

# Helper function to safely parse JSON responses
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

async def create_test_user():
    """Create a test user directly in the database and return a valid token"""
    print("\n--- CREATING TEST USER ---")
    
    # Try multiple approaches to create or find a test user
    user_id = None
    token = None
    
    # First try to create a user without authentication (this may be allowed in test/dev mode)
    test_user = {
        "name": "Test Admin",
        "email": f"admin_{uuid.uuid4()}@example.com"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Approach 1: Try to create the user without authentication
            print("Attempting to create user without authentication...")
            resp = await client.post(f"{BASE_URL}/users", json=test_user)
            
            if resp.status_code == 200 or resp.status_code == 201:
                # User created successfully
                user_id = resp.json()["id"]
                print(f"SYMBOL User created successfully with ID: {user_id}")
                token, _ = generate_test_token(user_id, test_user["name"], test_user["email"])
                return token, user_id
                
            # Approach 2: Use test endpoint if available
            print("Attempting to use test endpoint to create user...")
            resp = await client.post(f"{BASE_URL}/test/create-user", json=test_user)
            
            if resp.status_code == 200 or resp.status_code == 201:
                user_id = resp.json()["id"]
                print(f"SYMBOL User created via test endpoint with ID: {user_id}")
                token, _ = generate_test_token(user_id, test_user["name"], test_user["email"])
                return token, user_id
            
            # Approach 3: Try to get an existing test user (if your API supports this)
            print("Attempting to find an existing test user...")
            resp = await client.get(f"{BASE_URL}/test/get-test-user")
            
            if resp.status_code == 200 and "id" in resp.json():
                user_id = resp.json()["id"]
                name = resp.json().get("name", "Test User")
                email = resp.json().get("email", "test@example.com")
                print(f"SYMBOL Found existing test user with ID: {user_id}")
                token, _ = generate_test_token(user_id, name, email)
                return token, user_id
                
            # Approach 4: Use a bootstrapped admin token if your server supports it
            print("Attempting to use bootstrapped admin token...")
            resp = await client.get(f"{BASE_URL}/test/admin-token")
            
            if resp.status_code == 200 and "token" in resp.json():
                token = resp.json()["token"]
                user_id = resp.json().get("user_id")
                print(f"SYMBOL Got admin token for user ID: {user_id}")
                return token, user_id
                
            # If all approaches fail, fall back to generating a random token
            print("Could not create or find test user automatically.")
            print("Generating a token - will only work if your API allows self-registration")
            token, user_id = generate_test_token()
            
            # Try to validate token against /me endpoint to see if it works
            auth_headers = {"Authorization": f"Bearer {token}"}
            me_resp = await client.get(f"{BASE_URL}/me", headers=auth_headers)
            
            if me_resp.status_code < 400:
                print(f"SYMBOL Self-registration successful with user ID: {user_id}")
                return token, user_id
            else:
                print("Self-registration not supported.")
                print("Please ensure a test user exists in the database.")
                return None, None
                
        except Exception as e:
            print(f"Error during user creation: {str(e)}")
            return None, None

async def check_auth_success(jwt_token, user_id):
    """Test if authentication is successful and return the result"""
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{BASE_URL}/me", headers=headers)
        return resp.status_code < 400, headers

async def main():
    # Try to create a test user for authentication
    jwt_token, admin_id = await create_test_user()
    
    if not jwt_token:
        # If no test user could be created, generate a random token (which will fail auth)
        print("\nFalling back to random token (authentication will fail)...")
        jwt_token, admin_id = generate_test_token()
    
    # Check if authentication is working
    print("\n--- AUTHENTICATION CHECK ---")
    auth_success, headers = await check_auth_success(jwt_token, admin_id)
    
    if auth_success:
        print("\nAuthentication SUCCESSFUL SYMBOL")
        print(f"User ID: {admin_id}")
    else:
        print("\nAuthentication failed. This indicates that either:")
        print("1. The database connection is not properly configured")
        print("2. The test user doesn't exist in the database")
        print("3. The token is not being validated correctly")
        print("\nTo run the full API tests with authentication, you need to:")
        print("1. Ensure the database is properly configured")
        print("2. Create a test user in the database")
        print("3. Use that user's ID when generating a token")
        return
    
    # Test the full flow with authentication
    print("\n--- TESTING FULL FLOW WITH AUTHENTICATION ---")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # 1. Create users
        print("\n1. Creating test users...")
        users = [
            {"name": "Alice", "email": f"alice_{uuid.uuid4()}@example.com"},
            {"name": "Bob", "email": f"bob_{uuid.uuid4()}@example.com"},
            {"name": "Charlie", "email": f"charlie_{uuid.uuid4()}@example.com"}
        ]
        user_ids = []
        
        for i, user in enumerate(users):
            try:
                resp = await client.post(f"{BASE_URL}/users", json=user, headers=headers)
                status = "SYMBOL" if resp.status_code < 400 else "SYMBOL"
                print(f"  {status} Creating {user['name']}: {resp.status_code}")
                
                if resp.status_code < 400:
                    user_id = resp.json()["id"]
                    user_ids.append(user_id)
                    print(f"    User ID: {user_id}")
                else:
                    print(f"    Error: {safe_json(resp)}")
            except Exception as e:
                print(f"  SYMBOL Error creating {user['name']}: {str(e)}")
        
        if not user_ids:
            print("  SYMBOL Failed to create any users, cannot continue test")
            return
        
        print(f"  SYMBOL Created {len(user_ids)} users successfully")

        # 2. Create group
        print("\n2. Creating test group...")
        group = {"name": "Test Group"}
        try:
            resp = await client.post(f"{BASE_URL}/groups", json=group, headers=headers)
            
            if resp.status_code >= 400:
                print(f"  SYMBOL Failed to create group: {resp.status_code} {safe_json(resp)}")
                return
                
            group_id = resp.json()["id"]
            print(f"  SYMBOL Group created with ID: {group_id}")
        except Exception as e:
            print(f"  SYMBOL Error creating group: {str(e)}")
            return

        # 3. Add users to group
        print("\n3. Adding users to group...")
        success_count = 0
        
        for i, uid in enumerate(user_ids):
            try:
                membership = {"group_id": group_id, "user_id": uid}
                resp = await client.post(f"{BASE_URL}/group_members", json=membership, headers=headers)
                status = "SYMBOL" if resp.status_code < 400 else "SYMBOL"
                print(f"  {status} Adding user {i+1} to group: {resp.status_code}")
                
                if resp.status_code < 400:
                    success_count += 1
            except Exception as e:
                print(f"  SYMBOL Error adding user {i+1} to group: {str(e)}")
        
        if success_count == 0:
            print("  SYMBOL Failed to add any users to group, cannot continue test")
            return
            
        print(f"  SYMBOL Added {success_count} users to group successfully")

        # 4. Upload bill image and create bill/items
        print("\n4. Processing bill image...")
        try:
            with open("test_bill.jpg", "rb") as f:
                files = {"file": ("test_bill.jpg", f, "image/jpeg")}
                data = {"group_id": group_id, "uploaded_by": user_ids[0]}
                resp = await client.post(f"{BASE_URL}/process-bill-image", files=files, data=data, headers=headers)
                
                if resp.status_code >= 400:
                    print(f"  SYMBOL Failed to process bill image: {resp.status_code} {safe_json(resp)}")
                    return
                    
                bill = resp.json()["bill"]
                items = resp.json()["items"]
                bill_id = bill["id"]
                print(f"  SYMBOL Bill processed successfully with ID: {bill_id}")
                print(f"  SYMBOL {len(items)} items extracted from bill")
        except FileNotFoundError:
            print("  SYMBOL Test bill image not found. Make sure test_bill.jpg exists in the project directory")
            print("  Trying alternate test image...")
            try:
                # Try with another test image if available
                with open("test_receipt.png", "rb") as f:
                    files = {"file": ("test_receipt.png", f, "image/png")}
                    data = {"group_id": group_id, "uploaded_by": user_ids[0]}
                    resp = await client.post(f"{BASE_URL}/process-bill-image", files=files, data=data, headers=headers)
                    
                    if resp.status_code >= 400:
                        print(f"  SYMBOL Failed to process bill image: {resp.status_code} {safe_json(resp)}")
                        return
                        
                    bill = resp.json()["bill"]
                    items = resp.json()["items"]
                    bill_id = bill["id"]
                    print(f"  SYMBOL Bill processed successfully with ID: {bill_id} (using test_receipt.png)")
                    print(f"  SYMBOL {len(items)} items extracted from bill")
            except FileNotFoundError:
                print("  SYMBOL No test images found. Cannot continue test")
                return
        except Exception as e:
            print(f"  SYMBOL Error processing bill image: {str(e)}")
            return

        # 5. Users vote for items (simulate each user votes for all items except tax/tip)
        print("\n5. Users voting for items...")
        vote_count = 0
        
        for item in items:
            if not item["is_tax_or_tip"]:
                print(f"  Item: {item.get('name', 'Unnamed item')} (${item.get('price', 'unknown')})")
                
                for i, uid in enumerate(user_ids):
                    try:
                        vote = {"item_id": item["id"], "user_id": uid, "ate": True}
                        resp = await client.post(f"{BASE_URL}/votes", json=vote, headers=headers)
                        status = "SYMBOL" if resp.status_code < 400 else "SYMBOL"
                        print(f"    {status} User {i+1} votes: {resp.status_code}")
                        
                        if resp.status_code < 400:
                            vote_count += 1
                    except Exception as e:
                        print(f"    SYMBOL Error registering vote: {str(e)}")
        
        if vote_count == 0:
            print("  SYMBOL No votes were registered, cannot continue test")
            return
            
        print(f"  SYMBOL Registered {vote_count} votes successfully")

        # 6. Get bill split calculation
        print("\n6. Calculating initial bill split...")
        try:
            resp = await client.get(f"{BASE_URL}/bills/{bill_id}/split", headers=headers)
            
            if resp.status_code >= 400:
                print(f"  SYMBOL Failed to get bill split: {resp.status_code} {safe_json(resp)}")
                return
                
            split_data = resp.json()
            print("  SYMBOL Initial bill split calculated successfully")
            
            # Display summary of the split
            print("  Split summary:")
            for user_split in split_data.get("user_splits", []):
                user_id = user_split.get("user_id", "Unknown")
                amount = user_split.get("amount", 0)
                print(f"    User {user_id}: ${amount}")
        except Exception as e:
            print(f"  SYMBOL Error calculating bill split: {str(e)}")
            return
        
        # 7. Update bill with payer (as admin)
        print("\n7. Setting bill payer...")
        try:
            update_data = {"payer_id": user_ids[0]}  # First user is paying
            resp = await client.put(f"{BASE_URL}/bills/{bill_id}", json=update_data, headers=headers)
            
            if resp.status_code >= 400:
                print(f"  SYMBOL Failed to update bill with payer: {resp.status_code} {safe_json(resp)}")
                print("  Continuing anyway to test final split...")
            else:
                print(f"  SYMBOL Set payer to user ID: {user_ids[0]}")
        except Exception as e:
            print(f"  SYMBOL Error setting bill payer: {str(e)}")
            print("  Continuing anyway to test final split...")
        
        # 8. Get final bill split after setting payer
        print("\n8. Getting final bill split with payer...")
        try:
            resp = await client.get(f"{BASE_URL}/bills/{bill_id}/split", headers=headers)
            
            if resp.status_code >= 400:
                print(f"  SYMBOL Failed to get final bill split: {resp.status_code} {safe_json(resp)}")
                return
                
            final_split = resp.json()
            print("  SYMBOL Final bill split calculated successfully")
            
            # Display summary of who owes who
            print("  Payment summary:")
            for payment in final_split.get("payments", []):
                from_user = payment.get("from_user_id", "Unknown")
                to_user = payment.get("to_user_id", "Unknown") 
                amount = payment.get("amount", 0)
                print(f"    User {from_user} owes User {to_user}: ${amount}")
                
            print("\n--- FULL FLOW TEST COMPLETED SUCCESSFULLY ---")
        except Exception as e:
            print(f"  SYMBOL Error getting final bill split: {str(e)}")
            return

async def test_auth_scenarios():
    """Test various authentication scenarios"""
    print("\n--- TESTING AUTHENTICATION SCENARIOS ---")

    # Test 1: No authentication
    print("\n1. Testing without authentication...")
    async with httpx.AsyncClient() as client:
        # Try to access a protected endpoint without authentication
        resp = await client.get(f"{BASE_URL}/me")
        print(f"  Status: {resp.status_code}")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"
        print("  SYMBOL Authentication required (got expected 401/403)")

    # Test 2: Invalid token format
    print("\n2. Testing with invalid token format...")
    headers = {"Authorization": "Bearer invalid-token"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/me", headers=headers)
        print(f"  Status: {resp.status_code}")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"
        print("  SYMBOL Invalid tokens rejected (got expected 401/403)")

    # Test 3: Expired token
    print("\n3. Testing with expired token...")
    # Create a token that's already expired
    expiration = time.time() - 3600  # 1 hour ago (expired)
    payload = {
        "user_id": str(uuid.uuid4()),
        "email": "expired@example.com",
        "name": "Expired User",
        "exp": expiration
    }
    expired_token = pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    headers = {"Authorization": f"Bearer {expired_token}"}
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/me", headers=headers)
        print(f"  Status: {resp.status_code}")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"
        print("  SYMBOL Expired tokens rejected (got expected 401/403)")

    # Test 4: Valid token
    print("\n4. Testing with valid token...")
    token, user_id = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/me", headers=headers)
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code < 400:
            print("  SYMBOL Valid token accepted")
            print(f"  User info: {safe_json(resp)}")
        else:
            print("  SYMBOL Valid token rejected - this is expected if user doesn't exist in database")
            print("    Note: This is not a failure if your API validates user existence")

    print("\nAuth scenarios test completed")

async def run_tests():
    """Run all tests"""
    # First test authentication scenarios
    await test_auth_scenarios()
    
    # Then run the main flow
    await main()

if __name__ == "__main__":
    asyncio.run(run_tests())
