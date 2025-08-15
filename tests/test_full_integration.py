#!/usr/bin/env python3
"""
Full Integration Test Suite with Real Test Data

This test suite uses the real test data created by setup_test_data.py
to test complete workflows end-to-end with actual database operations.

Prerequisites:
    1. Run: python setup_test_data.py --setup
    2. Ensure FastAPI server is running: uvicorn main:app --reload
"""

import asyncio
import httpx
from tests.test_config import *

class FullIntegrationTester:
    """Comprehensive integration tests using real test data."""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.success_count = 0
        self.total_tests = 0
    
    def log(self, message, status="INFO"):
        """Log test results."""
        symbols = {"INFO": "INFO", "SUCCESS": "SUCCESS", "ERROR": "ERROR", "WARNING": "WARNING"}
        symbol = symbols.get(status, "•")
        print(f"{symbol} {message}")
    
    async def test_user_operations(self):
        """Test user-related operations with real users."""
        self.log("Testing User Operations", "INFO")
        
        # Use Alice's token for testing
        jwt_token, user_id = generate_test_jwt_token("alice")
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            self.total_tests += 3
            
            # Test 1: Get current user (Alice)
            try:
                resp = await client.get(f"{self.base_url}/auth/me", headers=headers)
                if resp.status_code == 200:
                    user_data = safe_json(resp)
                    if user_data.get("email") == "alice@test.com":
                        self.log("Get current user - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"Get current user - Wrong user returned: {user_data}", "ERROR")
                else:
                    self.log(f"Get current user - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Get current user - Error: {str(e)}", "ERROR")
            
            # Test 2: Search for Bob
            try:
                resp = await client.get(f"{self.base_url}/users/search?email=bob", headers=headers)
                if resp.status_code == 200:
                    result = safe_json(resp)
                    users = result.get("users", [])
                    if any(u.get("email") == "bob@test.com" for u in users):
                        self.log("User search - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"User search - Bob not found in results: {users}", "ERROR")
                else:
                    self.log(f"User search - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"User search - Error: {str(e)}", "ERROR")
            
            # Test 3: Get Alice's groups
            try:
                alice_id = get_user_id("alice")
                resp = await client.get(f"{self.base_url}/users/{alice_id}/groups", headers=headers)
                if resp.status_code == 200:
                    result = safe_json(resp)
                    groups = result.get("groups", [])
                    # Alice should be in "trip" and "lunch" groups
                    group_names = [g.get("name") for g in groups]
                    if "Test Trip Group" in group_names and "Office Lunch Squad" in group_names:
                        self.log("Get user groups - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"Get user groups - Expected groups not found: {group_names}", "ERROR")
                else:
                    self.log(f"Get user groups - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Get user groups - Error: {str(e)}", "ERROR")
    
    async def test_group_operations(self):
        """Test group-related operations with real groups."""
        self.log("Testing Group Operations", "INFO")
        
        jwt_token, user_id = generate_test_jwt_token("admin")
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            self.total_tests += 3
            
            # Test 1: Get trip group details
            try:
                trip_group_id = get_group_id("trip")
                resp = await client.get(f"{self.base_url}/groups/{trip_group_id}", headers=headers)
                if resp.status_code == 200:
                    group_data = safe_json(resp)
                    if group_data.get("name") == "Test Trip Group":
                        self.log("Get group details - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"Get group details - Wrong group: {group_data}", "ERROR")
                else:
                    self.log(f"Get group details - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Get group details - Error: {str(e)}", "ERROR")
            
            # Test 2: Get group members
            try:
                trip_group_id = get_group_id("trip")
                resp = await client.get(f"{self.base_url}/groups/{trip_group_id}/members", headers=headers)
                if resp.status_code == 200:
                    result = safe_json(resp)
                    members = result.get("members", [])
                    member_emails = [m.get("email") for m in members]
                    # Should have admin, alice, bob, charlie
                    expected_emails = ["admin@test.com", "alice@test.com", "bob@test.com", "charlie@test.com"]
                    if all(email in member_emails for email in expected_emails):
                        self.log("Get group members - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"Get group members - Expected members not found: {member_emails}", "ERROR")
                else:
                    self.log(f"Get group members - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Get group members - Error: {str(e)}", "ERROR")
            
            # Test 3: Get group bills
            try:
                trip_group_id = get_group_id("trip")
                resp = await client.get(f"{self.base_url}/groups/{trip_group_id}/bills", headers=headers)
                if resp.status_code == 200:
                    result = safe_json(resp)
                    bills = result.get("bills", [])
                    # Should have pizza bill and grocery bill
                    if len(bills) >= 2:
                        self.log("Get group bills - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"Get group bills - Expected at least 2 bills, got: {len(bills)}", "ERROR")
                else:
                    self.log(f"Get group bills - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Get group bills - Error: {str(e)}", "ERROR")
    
    async def test_bill_operations(self):
        """Test bill-related operations with real bills."""
        self.log("Testing Bill Operations", "INFO")
        
        jwt_token, user_id = generate_test_jwt_token("alice")
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            self.total_tests += 3
            
            # Test 1: Get pizza bill details
            try:
                pizza_bill_id = get_bill_id("pizza")
                resp = await client.get(f"{self.base_url}/bills/{pizza_bill_id}", headers=headers)
                if resp.status_code == 200:
                    bill_data = safe_json(resp)
                    # Check that Alice is the payer
                    alice_id = get_user_id("alice")
                    if bill_data.get("payer_id") == alice_id:
                        self.log("Get bill details - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"Get bill details - Wrong payer: {bill_data}", "ERROR")
                else:
                    self.log(f"Get bill details - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Get bill details - Error: {str(e)}", "ERROR")
            
            # Test 2: Get bill items
            try:
                pizza_bill_id = get_bill_id("pizza")
                resp = await client.get(f"{self.base_url}/bills/{pizza_bill_id}/items", headers=headers)
                if resp.status_code == 200:
                    result = safe_json(resp)
                    items = result.get("items", [])
                    # Should have 5 items: pizza, bread, cola, tax, tip
                    item_names = [item.get("name") for item in items]
                    expected_items = ["Margherita Pizza", "Garlic Bread", "Coca Cola", "Tax", "Tip"]
                    if all(item in item_names for item in expected_items):
                        self.log("Get bill items - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"Get bill items - Expected items not found: {item_names}", "ERROR")
                else:
                    self.log(f"Get bill items - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Get bill items - Error: {str(e)}", "ERROR")
            
            # Test 3: Calculate bill split
            try:
                pizza_bill_id = get_bill_id("pizza")
                resp = await client.get(f"{self.base_url}/bills/{pizza_bill_id}/split", headers=headers)
                if resp.status_code == 200:
                    split_data = safe_json(resp)
                    # Check that we get split results
                    if "splits" in split_data or "total_bill" in split_data:
                        self.log("Calculate bill split - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"Calculate bill split - Invalid split format: {split_data}", "ERROR")
                else:
                    self.log(f"Calculate bill split - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Calculate bill split - Error: {str(e)}", "ERROR")
    
    async def test_item_operations(self):
        """Test item-related operations with real items."""
        self.log("Testing Item Operations", "INFO")
        
        jwt_token, user_id = generate_test_jwt_token("bob")
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            self.total_tests += 2
            
            # Test 1: Get item details
            try:
                pizza_item_id = get_item_id("margherita")
                resp = await client.get(f"{self.base_url}/items/{pizza_item_id}", headers=headers)
                if resp.status_code == 200:
                    item_data = safe_json(resp)
                    if item_data.get("name") == "Margherita Pizza" and item_data.get("price") == 18.99:
                        self.log("Get item details - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"Get item details - Wrong item data: {item_data}", "ERROR")
                else:
                    self.log(f"Get item details - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Get item details - Error: {str(e)}", "ERROR")
            
            # Test 2: Toggle item vote
            try:
                coffee_item_id = get_item_id("coffee")
                bob_id = get_user_id("bob")
                vote_data = {"user_id": bob_id, "ate": True}
                
                resp = await client.post(f"{self.base_url}/items/{coffee_item_id}/vote", 
                                       json=vote_data, headers=headers)
                if resp.status_code == 200:
                    result = safe_json(resp)
                    if "status" in result:
                        self.log("Toggle item vote - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"Toggle item vote - Invalid response: {result}", "ERROR")
                else:
                    self.log(f"Toggle item vote - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Toggle item vote - Error: {str(e)}", "ERROR")
    
    async def test_authentication_edge_cases(self):
        """Test authentication edge cases with real users."""
        self.log("Testing Authentication Edge Cases", "INFO")
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            self.total_tests += 3
            
            # Test 1: Expired token
            try:
                expired_token, _ = generate_test_jwt_token("alice", expired=True)
                headers = {"Authorization": f"Bearer {expired_token}"}
                resp = await client.get(f"{self.base_url}/auth/me", headers=headers)
                
                if resp.status_code == 401:
                    self.log("Expired token rejection - SUCCESS", "SUCCESS")
                    self.success_count += 1
                else:
                    self.log(f"Expired token rejection - Should be 401, got: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Expired token test - Error: {str(e)}", "ERROR")
            
            # Test 2: Token refresh
            try:
                valid_token, _ = generate_test_jwt_token("charlie")
                headers = {"Authorization": f"Bearer {valid_token}"}
                resp = await client.post(f"{self.base_url}/auth/refresh", headers=headers)
                
                if resp.status_code == 200:
                    result = safe_json(resp)
                    if "access_token" in result:
                        self.log("Token refresh - SUCCESS", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.log(f"Token refresh - No access_token in response: {result}", "ERROR")
                else:
                    self.log(f"Token refresh - Failed: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Token refresh test - Error: {str(e)}", "ERROR")
            
            # Test 3: Invalid user token (user not in DB)
            try:
                # Create token for non-existent user
                fake_payload = {
                    "user_id": "99999999-9999-9999-9999-999999999999",
                    "email": "fake@test.com",
                    "name": "Fake User",
                    "exp": time.time() + 3600,
                    "iat": time.time(),
                    "iss": "splitbuddy-backend"
                }
                fake_token = pyjwt.encode(fake_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
                headers = {"Authorization": f"Bearer {fake_token}"}
                
                resp = await client.get(f"{self.base_url}/auth/me", headers=headers)
                if resp.status_code == 401:
                    self.log("Non-existent user rejection - SUCCESS", "SUCCESS")
                    self.success_count += 1
                else:
                    self.log(f"Non-existent user rejection - Should be 401, got: {resp.status_code}", "ERROR")
            except Exception as e:
                self.log(f"Non-existent user test - Error: {str(e)}", "ERROR")
    
    async def run_all_tests(self):
        """Run all integration tests."""
        self.log("Starting Full Integration Tests with Real Data", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            await self.test_user_operations()
            print()
            await self.test_group_operations() 
            print()
            await self.test_bill_operations()
            print()
            await self.test_item_operations()
            print()
            await self.test_authentication_edge_cases()
            
            # Print final results
            print()
            self.log("=" * 60, "INFO")
            self.log("FULL INTEGRATION TEST RESULTS", "INFO")
            self.log("=" * 60, "INFO")
            
            success_rate = (self.success_count / self.total_tests) * 100 if self.total_tests > 0 else 0
            self.log(f"Tests Passed: {self.success_count}/{self.total_tests} ({success_rate:.1f}%)", "INFO")
            
            if success_rate >= 90:
                self.log("EXCELLENT: Your API is working perfectly!", "SUCCESS")
            elif success_rate >= 75:
                self.log("GOOD: Most functionality is working correctly", "SUCCESS")
            elif success_rate >= 50:
                self.log("MODERATE: Some issues need attention", "WARNING")
            else:
                self.log("NEEDS WORK: Multiple issues detected", "ERROR")
            
        except Exception as e:
            self.log(f"Test suite failed: {str(e)}", "ERROR")

async def main():
    """Main test runner."""
    print("Full Integration Test Suite")
    print("=" * 60)
    print("Prerequisites:")
    print("1. Run: python setup_test_data.py --setup")
    print("2. Start server: uvicorn main:app --reload")
    print()
    
    # Quick check for server
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BASE_URL}/health")
            if resp.status_code != 200:
                print("ERROR Server health check failed")
                return
    except:
        print("ERROR Server is not running or not accessible")
        print("TIP Start with: uvicorn main:app --reload")
        return
    
    print("SUCCESS Server is running")
    print()
    
    tester = FullIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())