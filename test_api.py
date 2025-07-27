import asyncio
import httpx
import uuid
from datetime import date

BASE_URL = "http://127.0.0.1:8000"

def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return resp.text

async def main():
    async with httpx.AsyncClient() as client:
        # --- USERS ---
        print("\n--- USERS ---")
        user1 = {"name": "Alice", "email": f"alice_{uuid.uuid4()}@example.com"}
        user2 = {"name": "Bob", "email": f"bob_{uuid.uuid4()}@example.com"}
        # Create user
        resp = await client.post(f"{BASE_URL}/users", json=user1)
        print("Create user1:", resp.status_code, safe_json(resp))
        user1_id = resp.json()["id"]
        # Duplicate user
        resp = await client.post(f"{BASE_URL}/users", json=user1)
        print("Duplicate user1:", resp.status_code, safe_json(resp))
        # Create another user
        resp = await client.post(f"{BASE_URL}/users", json=user2)
        print("Create user2:", resp.status_code, safe_json(resp))
        user2_id = resp.json()["id"]
        # Get user
        resp = await client.get(f"{BASE_URL}/users/{user1_id}")
        print("Get user1:", resp.status_code, safe_json(resp))
        # Get not found
        resp = await client.get(f"{BASE_URL}/users/{uuid.uuid4()}")
        print("Get user not found:", resp.status_code, safe_json(resp))

        # --- GROUPS ---
        print("\n--- GROUPS ---")
        group = {"name": "Test Group"}
        resp = await client.post(f"{BASE_URL}/groups", json=group)
        print("Create group:", resp.status_code, safe_json(resp))
        group_id = resp.json()["id"]
        # Duplicate group (same name allowed, but same id not possible)
        # Get group
        resp = await client.get(f"{BASE_URL}/groups/{group_id}")
        print("Get group:", resp.status_code, safe_json(resp))
        # Get not found
        resp = await client.get(f"{BASE_URL}/groups/{uuid.uuid4()}")
        print("Get group not found:", resp.status_code, safe_json(resp))

        # --- GROUP MEMBERS ---
        print("\n--- GROUP MEMBERS ---")
        membership = {"group_id": group_id, "user_id": user1_id}
        resp = await client.post(f"{BASE_URL}/group_members", json=membership)
        print("Add user1 to group:", resp.status_code, safe_json(resp))
        membership_id = resp.json()["id"]
        # Duplicate membership
        resp = await client.post(f"{BASE_URL}/group_members", json=membership)
        print("Duplicate group member:", resp.status_code, safe_json(resp))
        # Get group member
        resp = await client.get(f"{BASE_URL}/group_members/{membership_id}")
        print("Get group member:", resp.status_code, safe_json(resp))
        # Get not found
        resp = await client.get(f"{BASE_URL}/group_members/{uuid.uuid4()}")
        print("Get group member not found:", resp.status_code, safe_json(resp))

        # --- BILLS ---
        print("\n--- BILLS ---")
        bill = {
            "group_id": group_id,
            "bill_date": str(date.today())
        }
        resp = await client.post(f"{BASE_URL}/bills", json=bill)
        print("Create bill:", resp.status_code, safe_json(resp))
        bill_id = resp.json()["id"]
        # Duplicate bill (same id not possible)
        # Get bill
        resp = await client.get(f"{BASE_URL}/bills/{bill_id}")
        print("Get bill:", resp.status_code, safe_json(resp))
        # Get not found
        resp = await client.get(f"{BASE_URL}/bills/{uuid.uuid4()}")
        print("Get bill not found:", resp.status_code, safe_json(resp))

        # --- ITEMS ---
        print("\n--- ITEMS ---")
        item = {
            "bill_id": bill_id,
            "name": "Test Item",
            "price": 123.45,
            "is_tax_or_tip": False
        }
        resp = await client.post(f"{BASE_URL}/items", json=item)
        print("Create item:", resp.status_code, safe_json(resp))
        item_id = resp.json()["id"]
        # Duplicate item (same id not possible)
        # Get item
        resp = await client.get(f"{BASE_URL}/items/{item_id}")
        print("Get item:", resp.status_code, safe_json(resp))
        # Get not found
        resp = await client.get(f"{BASE_URL}/items/{uuid.uuid4()}")
        print("Get item not found:", resp.status_code, safe_json(resp))

        # --- VOTES ---
        print("\n--- VOTES ---")
        vote = {
            "item_id": item_id,
            "user_id": user1_id,
            "ate": True
        }
        resp = await client.post(f"{BASE_URL}/votes", json=vote)
        print("Create vote:", resp.status_code, safe_json(resp))
        vote_id = resp.json()["id"]
        # Duplicate vote (same id not possible)
        # Get vote
        resp = await client.get(f"{BASE_URL}/votes/{vote_id}")
        print("Get vote:", resp.status_code, safe_json(resp))
        # Get not found
        resp = await client.get(f"{BASE_URL}/votes/{uuid.uuid4()}")
        print("Get vote not found:", resp.status_code, safe_json(resp))

if __name__ == "__main__":
    asyncio.run(main()) 