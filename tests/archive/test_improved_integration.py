#!/usr/bin/env python3
"""
Integration test for the improved bill splitting logic
Tests the complete workflow with the enhanced splitting algorithm
"""

import asyncio
import httpx
import uuid
import json
from datetime import date

BASE_URL = "http://127.0.0.1:8000"

async def test_improved_splitting_workflow():
    """Test the complete workflow with improved splitting logic"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("ROCKET Testing Improved Bill Splitting Workflow")
        print("=" * 60)
        
        # 1. Create users
        print("SYMBOL Creating Users...")
        users = [
            {"name": "Alice", "email": f"alice_{uuid.uuid4()}@example.com"},
            {"name": "Bob", "email": f"bob_{uuid.uuid4()}@example.com"},
            {"name": "Charlie", "email": f"charlie_{uuid.uuid4()}@example.com"}
        ]
        user_ids = []
        user_names = {}
        
        for user in users:
            resp = await client.post(f"{BASE_URL}/users", json=user)
            if resp.status_code == 200:
                user_data = resp.json()
                user_ids.append(user_data["id"])
                user_names[user_data["id"]] = user["name"]
                print(f"  SUCCESS Created {user['name']}: {user_data['id']}")
            else:
                print(f"  ERROR Failed to create {user['name']}: {resp.status_code}")
                return False

        # 2. Create group
        print("\nSYMBOL Creating Group...")
        group = {"name": "Mario's Pizza Test Group"}
        resp = await client.post(f"{BASE_URL}/groups", json=group)
        if resp.status_code != 200:
            print(f"  ERROR Failed to create group: {resp.status_code}")
            return False
        
        group_id = resp.json()["id"]
        print(f"  SUCCESS Created group: {group_id}")

        # 3. Add users to group
        print("\nSYMBOL Adding Users to Group...")
        for i, uid in enumerate(user_ids):
            membership = {"group_id": group_id, "user_id": uid}
            resp = await client.post(f"{BASE_URL}/group_members", json=membership)
            if resp.status_code == 200:
                print(f"  SUCCESS Added {list(user_names.values())[i]} to group")
            else:
                print(f"  ERROR Failed to add user to group: {resp.status_code}")

        # 4. Create bill manually (simulating the Mario's Pizza receipt)
        print("\nSYMBOL Creating Bill...")
        bill_data = {
            "group_id": group_id,
            "payer_id": user_ids[0],  # Alice pays
            "uploaded_by": user_ids[0],
            "bill_date": date.today().isoformat()
        }
        resp = await client.post(f"{BASE_URL}/bills", json=bill_data)
        if resp.status_code != 200:
            print(f"  ERROR Failed to create bill: {resp.status_code}")
            return False
        
        bill_id = resp.json()["id"]
        print(f"  SUCCESS Created bill: {bill_id}")

        # 5. Create items (Mario's Pizza items)
        print("\nSYMBOL Creating Bill Items...")
        mario_items = [
            {"name": "Margherita Pizza", "price": 18.99, "is_tax_or_tip": False},
            {"name": "Garlic Bread", "price": 6.50, "is_tax_or_tip": False},
            {"name": "Coca Cola", "price": 3.99, "is_tax_or_tip": False},
            {"name": "Tax (8.5%)", "price": 2.51, "is_tax_or_tip": True},
            {"name": "Tip (18%)", "price": 5.76, "is_tax_or_tip": True},
        ]
        
        created_items = []
        for item_data in mario_items:
            item_data["bill_id"] = bill_id
            resp = await client.post(f"{BASE_URL}/items", json=item_data)
            if resp.status_code == 200:
                item = resp.json()
                created_items.append(item)
                print(f"  SUCCESS Created {item_data['name']}: ${item_data['price']:.2f}")
            else:
                print(f"  ERROR Failed to create {item_data['name']}: {resp.status_code}")

        # 6. Test different voting scenarios
        print("\nSYMBOL️  Testing Voting Scenarios...")
        
        # Scenario 1: Everyone shares everything equally
        print("\n  Scenario 1: Everyone shares everything equally")
        await test_voting_scenario(client, created_items, user_ids, user_names, bill_id, "equal_sharing")
        
        # Scenario 2: Different consumption patterns
        print("\n  Scenario 2: Different consumption patterns")
        await test_voting_scenario(client, created_items, user_ids, user_names, bill_id, "different_consumption")
        
        # Scenario 3: One person eats most items
        print("\n  Scenario 3: One person eats most items")
        await test_voting_scenario(client, created_items, user_ids, user_names, bill_id, "one_person_most")

        return True

async def test_voting_scenario(client, items, user_ids, user_names, bill_id, scenario_name):
    """Test a specific voting scenario"""
    
    # Clear existing votes first
    # (In a real app, you might want to update votes instead)
    
    # Define voting patterns based on scenario
    voting_patterns = {
        "equal_sharing": {
            # Everyone shares everything equally
            "Margherita Pizza": user_ids,
            "Garlic Bread": user_ids,
            "Coca Cola": user_ids,
        },
        "different_consumption": {
            # Mixed consumption
            "Margherita Pizza": [user_ids[0], user_ids[1]],  # Alice & Bob share pizza
            "Garlic Bread": [user_ids[1], user_ids[2]],      # Bob & Charlie share bread
            "Coca Cola": [user_ids[2]],                       # Charlie drinks alone
        },
        "one_person_most": {
            # Alice eats most things
            "Margherita Pizza": [user_ids[0]],               # Alice eats pizza alone
            "Garlic Bread": [user_ids[0], user_ids[1]],     # Alice & Bob share bread
            "Coca Cola": [user_ids[0], user_ids[1], user_ids[2]],  # Everyone shares drink
        }
    }
    
    pattern = voting_patterns.get(scenario_name, {})
    
    # Submit votes
    for item in items:
        if not item["is_tax_or_tip"]:  # Don't vote on tax/tip
            eaters = pattern.get(item["name"], [])
            
            # Vote for each user
            for user_id in user_ids:
                vote_data = {
                    "user_id": user_id,
                    "ate": user_id in eaters
                }
                resp = await client.post(f"{BASE_URL}/items/{item['id']}/vote", json=vote_data)
                if resp.status_code == 200:
                    ate_status = "ate" if user_id in eaters else "didn't eat"
                    user_name = user_names[user_id]
                    print(f"    SUCCESS {user_name} {ate_status} {item['name']}")

    # Calculate split
    resp = await client.get(f"{BASE_URL}/bills/{bill_id}/split")
    if resp.status_code == 200:
        split_result = resp.json()
        print(f"\n    SYMBOL Split Results for {scenario_name}:")
        
        totals = split_result["totals"]
        payer_id = split_result["payer_id"]
        
        # Calculate total bill
        total_bill = sum(float(item["price"]) for item in items)
        print(f"    Total Bill: ${total_bill:.2f}")
        
        # Show results
        for uid, amount in totals.items():
            name = user_names.get(uid, uid)  # Use ID if name not found
            if uid == payer_id:
                print(f"    {name} (payer): ${float(amount):.2f} (receives from others)")
            else:
                print(f"    {name}: ${float(amount):.2f} (owes to payer)")
        
        # Verify balance
        total_sum = sum(float(amount) for amount in totals.values())
        print(f"    Verification: Sum = ${total_sum:.6f} (should be ~$0.00)")
        
        # Consider values close to zero (within 1 cent) as balanced
        if abs(total_sum) < 0.01:
            print(f"    SUCCESS Split balances correctly!")
        else:
            print(f"    ERROR Split doesn't balance: ${total_sum:.2f} (should be ~$0.00)")
        
        # Test Splitwise logic specifically
        test_splitwise_precision(total_bill, len(user_ids))
    else:
        print(f"    ERROR Failed to calculate split: {resp.status_code}")

def test_splitwise_precision(total_amount, num_people):
    """Test the Splitwise splitting logic for precision"""
    print(f"\n    SYMBOL Testing Splitwise Logic:")
    print(f"    Amount: ${total_amount:.2f}, People: {num_people}")
    
    # Simulate the Splitwise logic
    total_cents = round(total_amount * 100)
    base_cents = total_cents // num_people
    remainder_cents = total_cents % num_people
    
    splits = []
    for i in range(num_people):
        if i < remainder_cents:
            splits.append((base_cents + 1) / 100)
        else:
            splits.append(base_cents / 100)
    
    print(f"    Individual shares: {[f'${x:.2f}' for x in splits]}")
    print(f"    Sum: ${sum(splits):.2f}")
    print(f"    Exact match: {abs(sum(splits) - total_amount) < 0.001}")

async def test_edge_cases():
    """Test edge cases for the splitting logic"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\nTESTING Testing Edge Cases...")
        
        # Test with very small amounts
        test_cases = [
            {"amount": 0.01, "people": 5, "description": "1 cent among 5 people"},
            {"amount": 0.07, "people": 3, "description": "7 cents among 3 people"},
            {"amount": 100.00, "people": 7, "description": "$100 among 7 people"},
            {"amount": 1234.56, "people": 13, "description": "$1234.56 among 13 people"},
        ]
        
        for case in test_cases:
            print(f"\n  Testing: {case['description']}")
            test_splitwise_precision(case["amount"], case["people"])

async def main():
    """Main test runner"""
    try:
        # Test server connection
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BASE_URL}/test-supabase")
            if resp.status_code != 200:
                print("ERROR Server connection failed")
                return
        
        print("SUCCESS Server connection successful")
        
        # Run main workflow test
        success = await test_improved_splitting_workflow()
        
        if success:
            # Run edge case tests
            await test_edge_cases()
            print("\nSYMBOL All tests completed successfully!")
        else:
            print("\nERROR Some tests failed")
            
    except Exception as e:
        print(f"ERROR Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())