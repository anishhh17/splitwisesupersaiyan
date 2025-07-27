#!/usr/bin/env python3
"""
Comprehensive test script for bill splitting workflow
Tests the complete user journey from creating users to calculating splits
"""

import requests
import json
from datetime import date, datetime
import uuid

# Configure your FastAPI server URL
BASE_URL = "http://localhost:8000"  # Change this to your server URL

class BillSplitTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.users = {}
        self.group_id = None
        self.bill_id = None
        self.items = []
        # Add a random suffix for this test run
        self.rand_suffix = str(uuid.uuid4())[:8]
    
    def log(self, message, data=None):
        """Helper to log test results"""
        print(f"✅ {message}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2, default=str)}")
        print()
    
    def test_request(self, method, endpoint, data=None, expected_status=200):
        """Helper to make API requests and handle responses"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code != expected_status:
                print(f"❌ Request failed: {method} {endpoint}")
                print(f"   Expected status: {expected_status}, Got: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return None
    
    def test_1_create_users(self):
        """Test 1: Create test users"""
        print("🧪 Test 1: Creating Users")
        
        # Add randomness to emails
        users_data = [
            {"name": "Alice", "email": f"alice_{self.rand_suffix}@example.com"},
            {"name": "Bob", "email": f"bob_{self.rand_suffix}@example.com"},
            {"name": "Charlie", "email": f"charlie_{self.rand_suffix}@example.com"},
        ]
        
        for user_data in users_data:
            response = self.test_request("POST", "/users", user_data)
            if response:
                self.users[user_data["name"]] = response["id"]
                self.log(f"Created user {user_data['name']}", response)
            else:
                print(f"❌ Failed to create user {user_data['name']}")
                return False
        
        return True
    
    def test_2_create_group(self):
        """Test 2: Create a group and add members"""
        print("🧪 Test 2: Creating Group and Adding Members")
        
        # Create group with random name
        group_data = {"name": f"Dinner Friends {self.rand_suffix}"}
        response = self.test_request("POST", "/groups", group_data)
        if not response:
            return False
        
        self.group_id = response["id"]
        self.log("Created group", response)
        
        # Add all users to the group
        for name, user_id in self.users.items():
            membership_data = {
                "group_id": self.group_id,
                "user_id": user_id
            }
            response = self.test_request("POST", "/group_members", membership_data)
            if response:
                self.log(f"Added {name} to group", response)
            else:
                print(f"❌ Failed to add {name} to group")
                return False
        
        # Verify group members
        response = self.test_request("GET", f"/groups/{self.group_id}/members")
        if response:
            self.log("Group members retrieved", response)
        
        return True
    
    def test_3_create_bill(self):
        """Test 3: Create a bill"""
        print("🧪 Test 3: Creating Bill")
        
        bill_data = {
            "group_id": self.group_id,
            "payer_id": self.users["Alice"],  # Alice pays initially
            "uploaded_by": self.users["Alice"],
            "bill_date": date.today().isoformat()
        }
        
        response = self.test_request("POST", "/bills", bill_data)
        if not response:
            return False
        
        self.bill_id = response["id"]
        self.log("Created bill", response)
        return True
    
    def test_4_create_items(self):
        """Test 4: Create bill items (simulating OCR results)"""
        print("🧪 Test 4: Creating Bill Items")
        
        items_data = [
            {"bill_id": self.bill_id, "name": "Margherita Pizza", "price": 18.99, "is_tax_or_tip": False},
            {"bill_id": self.bill_id, "name": "Caesar Salad", "price": 12.50, "is_tax_or_tip": False},
            {"bill_id": self.bill_id, "name": "Spaghetti Carbonara", "price": 16.75, "is_tax_or_tip": False},
            {"bill_id": self.bill_id, "name": "Garlic Bread", "price": 6.25, "is_tax_or_tip": False},
            {"bill_id": self.bill_id, "name": "Tiramisu", "price": 8.50, "is_tax_or_tip": False},
            {"bill_id": self.bill_id, "name": "Tax", "price": 5.20, "is_tax_or_tip": True},
            {"bill_id": self.bill_id, "name": "Tip", "price": 13.60, "is_tax_or_tip": True},
        ]
        
        for item_data in items_data:
            response = self.test_request("POST", "/items", item_data)
            if response:
                self.items.append(response)
                self.log(f"Created item: {item_data['name']}", response)
            else:
                print(f"❌ Failed to create item: {item_data['name']}")
                return False
        
        # Verify items were created
        response = self.test_request("GET", f"/bills/{self.bill_id}/items")
        if response:
            self.log("All bill items retrieved", response)
        
        return True
    
    def test_5_user_voting(self):
        """Test 5: Users vote on items they consumed"""
        print("🧪 Test 5: User Voting on Items")
        
        # Define what each user ate
        voting_scenario = {
            "Alice": ["Margherita Pizza", "Caesar Salad", "Garlic Bread", "Tiramisu"],  # Alice ate 4 items
            "Bob": ["Margherita Pizza", "Spaghetti Carbonara", "Garlic Bread"],         # Bob ate 3 items
            "Charlie": ["Caesar Salad", "Spaghetti Carbonara", "Tiramisu"]              # Charlie ate 3 items
        }
        
        # Create a mapping of item names to IDs
        item_name_to_id = {item["name"]: item["id"] for item in self.items}
        
        # Process votes for each user
        for user_name, consumed_items in voting_scenario.items():
            user_id = self.users[user_name]
            
            for item_name in consumed_items:
                item_id = item_name_to_id.get(item_name)
                if not item_id:
                    print(f"❌ Item '{item_name}' not found")
                    continue
                
                vote_data = {
                    "user_id": user_id,
                    "ate": True
                }
                
                response = self.test_request("POST", f"/items/{item_id}/vote", vote_data)
                if response:
                    self.log(f"{user_name} voted for {item_name}", response)
                else:
                    print(f"❌ Failed to record vote: {user_name} -> {item_name}")
                    return False
        
        return True
    
    def test_6_calculate_split(self):
        """Test 6: Calculate bill split"""
        print("🧪 Test 6: Calculating Bill Split")
        
        response = self.test_request("GET", f"/bills/{self.bill_id}/split")
        if not response:
            return False
        
        self.log("Bill split calculated", response)
        
        # Verify the split makes sense
        totals = response.get("totals", {})
        payer_id = response.get("payer_id")

        # --- Assertions for split correctness ---
        # 1. Sum of non-payer amounts equals abs(payer amount) (balances to zero)
        payer_amount = totals.get(payer_id, 0)
        non_payer_amounts = [amt for uid, amt in totals.items() if uid != payer_id]
        sum_non_payers = sum(non_payer_amounts)
        # Allow small floating point tolerance
        assert abs(abs(payer_amount) - sum_non_payers) < 1e-2, f"Sum of non-payer amounts ({sum_non_payers}) does not match abs(payer amount) ({abs(payer_amount)})"
        # 2. Payer's amount is negative
        assert payer_amount < 0, f"Payer's amount should be negative, got {payer_amount}"
        # 3. Non-payers have positive amounts
        for uid, amt in totals.items():
            if uid != payer_id:
                assert amt > 0, f"Non-payer {uid} has non-positive amount: {amt}"
        # --- End assertions ---
        
        print("📊 Split Summary:")
        total_owed = 0
        for user_name, user_id in self.users.items():
            amount = totals.get(user_id, 0)
            if user_id == payer_id:
                print(f"   {user_name} (PAYER): ${amount:.2f} (receives from others)")
                total_owed += abs(amount)
            else:
                print(f"   {user_name}: ${amount:.2f} (owes to payer)")
        
        print(f"   Total bill amount: ${sum(float(item['price']) for item in self.items):.2f}")
        print()
        
        return True
    
    def test_7_edit_scenarios(self):
        """Test 7: Test editing scenarios"""
        print("🧪 Test 7: Testing Edit Scenarios")
        
        # Test 7a: Change payer
        new_payer_data = {"payer_id": self.users["Bob"]}
        response = self.test_request("PUT", f"/bills/{self.bill_id}", new_payer_data)
        if response:
            self.log("Changed payer to Bob", response)
            
            # Recalculate split with new payer
            response = self.test_request("GET", f"/bills/{self.bill_id}/split")
            if response:
                self.log("Split recalculated with new payer", response)
        
        # Test 7b: Edit an item price
        pizza_item = next((item for item in self.items if item["name"] == "Margherita Pizza"), None)
        if pizza_item:
            new_price_data = {"price": 22.99}  # Increase pizza price
            response = self.test_request("PUT", f"/items/{pizza_item['id']}", new_price_data)
            if response:
                self.log("Updated pizza price", response)
                
                # Recalculate split after price change
                response = self.test_request("GET", f"/bills/{self.bill_id}/split")
                if response:
                    self.log("Split recalculated after price change", response)
        
        # Test 7c: Change a vote (Alice decides she didn't have tiramisu)
        tiramisu_item = next((item for item in self.items if item["name"] == "Tiramisu"), None)
        if tiramisu_item:
            vote_data = {"user_id": self.users["Alice"], "ate": False}
            response = self.test_request("POST", f"/items/{tiramisu_item['id']}/vote", vote_data)
            if response:
                self.log("Alice changed vote for Tiramisu", response)
                
                # Recalculate split after vote change
                response = self.test_request("GET", f"/bills/{self.bill_id}/split")
                if response:
                    self.log("Split recalculated after vote change", response)
        
        return True
    
    def test_8_edge_cases(self):
        """Test 8: Edge cases"""
        print("🧪 Test 8: Testing Edge Cases")
        
        # Create a new bill with no votes
        bill_data = {
            "group_id": self.group_id,
            "payer_id": self.users["Charlie"],
            "uploaded_by": self.users["Charlie"],
            "bill_date": date.today().isoformat()
        }
        
        response = self.test_request("POST", "/bills", bill_data)
        if not response:
            return False
        
        empty_bill_id = response["id"]
        
        # Add one item
        item_data = {"bill_id": empty_bill_id, "name": "Coffee", "price": 5.00, "is_tax_or_tip": False}
        response = self.test_request("POST", "/items", item_data)
        if not response:
            return False
        
        # Calculate split with no votes
        response = self.test_request("GET", f"/bills/{empty_bill_id}/split")
        if response:
            self.log("Split for bill with no votes", response)
        
        return True
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Bill Splitting Tests")
        print("=" * 50)
        
        tests = [
            self.test_1_create_users,
            self.test_2_create_group,
            self.test_3_create_bill,
            self.test_4_create_items,
            self.test_5_user_voting,
            self.test_6_calculate_split,
            self.test_7_edit_scenarios,
            self.test_8_edge_cases,
        ]
        
        passed = 0
        for i, test in enumerate(tests, 1):
            try:
                if test():
                    passed += 1
                    print(f"✅ Test {i} PASSED")
                else:
                    print(f"❌ Test {i} FAILED")
            except Exception as e:
                print(f"❌ Test {i} ERROR: {e}")
            
            print("-" * 30)
        
        print(f"\n🏁 Test Results: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("🎉 All tests passed! Your bill splitting workflow is working correctly!")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")


def main():
    """Main function to run the test suite"""
    print("Bill Splitting App - Test Suite")
    print("Make sure your FastAPI server is running!")
    print()
    
    # Test connection first
    try:
        response = requests.get(f"{BASE_URL}/test-supabase", timeout=5)
        if response.status_code == 200:
            print("✅ Server connection successful!")
        else:
            print("❌ Server responded with error:", response.status_code)
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"Error: {e}")
        print("Please make sure your FastAPI server is running and the URL is correct.")
        return
    
    # Run the test suite
    tester = BillSplitTester(BASE_URL)
    tester.run_all_tests()


if __name__ == "__main__":
    main()