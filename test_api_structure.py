import asyncio
import httpx
import uuid
from datetime import date

# Configuration
BASE_URL = "http://127.0.0.1:8000"

def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return resp.text

async def test_api_structure():
    """
    Test the structure of the API endpoints without authentication.
    This won't test actual functionality but ensures endpoints exist.
    """
    print("\n--- API STRUCTURE TEST ---")
    
    # Generate some test IDs
    user_id = str(uuid.uuid4())
    group_id = str(uuid.uuid4())
    bill_id = str(uuid.uuid4())
    item_id = str(uuid.uuid4())
    vote_id = str(uuid.uuid4())
    
    # Define endpoints to check
    endpoints = [
        # Users
        f"{BASE_URL}/users",
        f"{BASE_URL}/users/{user_id}",
        f"{BASE_URL}/me",
        
        # Groups
        f"{BASE_URL}/groups",
        f"{BASE_URL}/groups/{group_id}",
        f"{BASE_URL}/groups/{group_id}/members",
        f"{BASE_URL}/group_members",
        
        # Bills
        f"{BASE_URL}/bills",
        f"{BASE_URL}/bills/{bill_id}",
        f"{BASE_URL}/bills/{bill_id}/items",
        f"{BASE_URL}/bills/{bill_id}/split",
        
        # Items
        f"{BASE_URL}/items",
        f"{BASE_URL}/items/{item_id}",
        f"{BASE_URL}/items/{item_id}/vote",
        
        # Votes
        f"{BASE_URL}/votes",
        f"{BASE_URL}/votes/{vote_id}",
        
        # Auth
        f"{BASE_URL}/login",
        f"{BASE_URL}/logout"
    ]
    
    async with httpx.AsyncClient() as client:
        for endpoint in endpoints:
            # We're just checking the endpoint structure, not the response
            # So we don't care if it's a 401, 404, or 200, just that it responds
            try:
                resp = await client.get(endpoint)
                print(f"GET {endpoint}: {resp.status_code}")
            except Exception as e:
                print(f"GET {endpoint}: ERROR - {str(e)}")

async def test_api_route_methods():
    """
    Test that API endpoints accept the correct HTTP methods.
    This checks the structure of the API without checking functionality.
    """
    print("\n--- API METHODS TEST ---")
    
    # Define test resources
    resources = {
        "users": {
            "methods": ["GET", "POST"],
            "id": str(uuid.uuid4()),
            "has_id_endpoint": True,
        },
        "groups": {
            "methods": ["GET", "POST"],
            "id": str(uuid.uuid4()),
            "has_id_endpoint": True,
            "sub_resources": ["members"]
        },
        "bills": {
            "methods": ["GET", "POST"],
            "id": str(uuid.uuid4()),
            "has_id_endpoint": True,
            "sub_resources": ["items", "split"]
        },
        "items": {
            "methods": ["GET", "POST"],
            "id": str(uuid.uuid4()),
            "has_id_endpoint": True,
            "sub_resources": ["vote"]
        },
        "votes": {
            "methods": ["GET", "POST"],
            "id": str(uuid.uuid4()),
            "has_id_endpoint": True,
        },
    }
    
    async with httpx.AsyncClient() as client:
        for resource, config in resources.items():
            # Test collection endpoint
            for method in config["methods"]:
                if method == "GET":
                    try:
                        resp = await client.get(f"{BASE_URL}/{resource}")
                        print(f"GET {BASE_URL}/{resource}: {resp.status_code}")
                    except Exception as e:
                        print(f"GET {BASE_URL}/{resource}: ERROR - {str(e)}")
                elif method == "POST":
                    try:
                        resp = await client.post(f"{BASE_URL}/{resource}", json={})
                        print(f"POST {BASE_URL}/{resource}: {resp.status_code}")
                    except Exception as e:
                        print(f"POST {BASE_URL}/{resource}: ERROR - {str(e)}")
            
            # Test ID endpoint if applicable
            if config.get("has_id_endpoint", False):
                try:
                    resp = await client.get(f"{BASE_URL}/{resource}/{config['id']}")
                    print(f"GET {BASE_URL}/{resource}/{config['id']}: {resp.status_code}")
                except Exception as e:
                    print(f"GET {BASE_URL}/{resource}/{config['id']}: ERROR - {str(e)}")
                
                # Test PUT for ID endpoint
                try:
                    resp = await client.put(f"{BASE_URL}/{resource}/{config['id']}", json={})
                    print(f"PUT {BASE_URL}/{resource}/{config['id']}: {resp.status_code}")
                except Exception as e:
                    print(f"PUT {BASE_URL}/{resource}/{config['id']}: ERROR - {str(e)}")
            
            # Test sub-resources if applicable
            for sub_resource in config.get("sub_resources", []):
                try:
                    resp = await client.get(f"{BASE_URL}/{resource}/{config['id']}/{sub_resource}")
                    print(f"GET {BASE_URL}/{resource}/{config['id']}/{sub_resource}: {resp.status_code}")
                except Exception as e:
                    print(f"GET {BASE_URL}/{resource}/{config['id']}/{sub_resource}: ERROR - {str(e)}")

async def main():
    # Test API endpoint structure
    await test_api_structure()
    
    # Test API HTTP methods
    await test_api_route_methods()

if __name__ == "__main__":
    asyncio.run(main())
