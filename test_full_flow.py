import httpx
import uuid
from datetime import date
import asyncio

BASE_URL = "http://127.0.0.1:8000"

async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Create users
        users = [
            {"name": "Alice", "email": f"alice_{uuid.uuid4()}@example.com"},
            {"name": "Bob", "email": f"bob_{uuid.uuid4()}@example.com"},
            {"name": "Charlie", "email": f"charlie_{uuid.uuid4()}@example.com"}
        ]
        user_ids = []
        for user in users:
            resp = await client.post(f"{BASE_URL}/users", json=user)
            print("Create user:", resp.status_code, resp.json())
            user_ids.append(resp.json()["id"])

        # 2. Create group
        group = {"name": "Test Group"}
        resp = await client.post(f"{BASE_URL}/groups", json=group)
        print("Create group:", resp.status_code, resp.json())
        group_id = resp.json()["id"]

        # 3. Add users to group
        for uid in user_ids:
            membership = {"group_id": group_id, "user_id": uid}
            resp = await client.post(f"{BASE_URL}/group_members", json=membership)
            print("Add user to group:", resp.status_code, resp.json())

        # 4. Upload bill image and create bill/items
        with open("test_bill.jpg", "rb") as f:
            files = {"file": ("test_bill.jpg", f, "image/jpeg")}
            data = {"group_id": group_id, "uploaded_by": user_ids[0]}
            resp = await client.post(f"{BASE_URL}/process-bill-image", files=files, data=data)
            print("Process bill image:", resp.status_code, resp.json())
            bill = resp.json()["bill"]
            items = resp.json()["items"]
            bill_id = bill["id"]

        # 5. Users vote for items (simulate each user votes for all items except tax/tip)
        for item in items:
            if not item["is_tax_or_tip"]:
                for uid in user_ids:
                    vote = {"item_id": item["id"], "user_id": uid, "ate": True}
                    resp = await client.post(f"{BASE_URL}/votes", json=vote)
                    print(f"User {uid} votes for item {item['name']}:", resp.status_code, resp.json())

        # 6. Get bill split
        resp = await client.get(f"{BASE_URL}/bills/{bill_id}/split")
        print("Bill split:", resp.status_code, resp.json())

if __name__ == "__main__":
    asyncio.run(main())
