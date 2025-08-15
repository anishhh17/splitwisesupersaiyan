#!/usr/bin/env python3
"""
Test Data Setup Script for Splitwise Super Saiyan

This script creates realistic test data in your Supabase database to enable
full testing of all API endpoints and workflows.

Usage:
    python setup_test_data.py --setup    # Create test data
    python setup_test_data.py --cleanup  # Remove test data
    python setup_test_data.py --status   # Check test data status
"""

import os
import argparse
import uuid
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test data configuration
TEST_DATA_CONFIG = {
    "users": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Test Admin",
            "email": "admin@test.com"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001", 
            "name": "Alice Johnson",
            "email": "alice@test.com"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "name": "Bob Smith", 
            "email": "bob@test.com"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440003",
            "name": "Charlie Brown",
            "email": "charlie@test.com"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440004",
            "name": "Diana Prince",
            "email": "diana@test.com"
        }
    ],
    "groups": [
        {
            "id": "660e8400-e29b-41d4-a716-446655440000",
            "name": "Test Trip Group"
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "name": "Office Lunch Squad"
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440002", 
            "name": "Roommates"
        }
    ]
}

class TestDataManager:
    """Manages test data creation, cleanup, and status checking."""
    
    def __init__(self):
        self.supabase = supabase
        self.test_data = TEST_DATA_CONFIG
    
    def log(self, message, status="INFO"):
        """Log messages with status."""
        symbols = {"INFO": "INFO", "SUCCESS": "SUCCESS", "ERROR": "ERROR", "WARNING": "WARNING"}
        symbol = symbols.get(status, "•")
        print(f"{symbol} {message}")
    
    def check_connection(self):
        """Verify Supabase connection."""
        try:
            # Try a simple query
            resp = self.supabase.table("users").select("id").limit(1).execute()
            self.log("Supabase connection successful", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Supabase connection failed: {str(e)}", "ERROR")
            return False
    
    def create_users(self):
        """Create test users."""
        self.log("Creating test users...")
        
        created_count = 0
        for user in self.test_data["users"]:
            try:
                # Check if user already exists
                existing = self.supabase.table("users").select("id").eq("id", user["id"]).execute()
                
                if existing.data:
                    self.log(f"User {user['name']} already exists", "WARNING")
                    continue
                
                # Create user
                resp = self.supabase.table("users").insert(user).execute()
                if resp.data:
                    self.log(f"Created user: {user['name']} ({user['email']})", "SUCCESS")
                    created_count += 1
                else:
                    self.log(f"Failed to create user: {user['name']}", "ERROR")
                    
            except Exception as e:
                self.log(f"Error creating user {user['name']}: {str(e)}", "ERROR")
        
        self.log(f"Created {created_count} new users", "SUCCESS")
        return created_count
    
    def create_groups(self):
        """Create test groups."""
        self.log("Creating test groups...")
        
        created_count = 0
        for group in self.test_data["groups"]:
            try:
                # Check if group already exists
                existing = self.supabase.table("groups").select("id").eq("id", group["id"]).execute()
                
                if existing.data:
                    self.log(f"Group {group['name']} already exists", "WARNING")
                    continue
                
                # Create group
                resp = self.supabase.table("groups").insert(group).execute()
                if resp.data:
                    self.log(f"Created group: {group['name']}", "SUCCESS")
                    created_count += 1
                else:
                    self.log(f"Failed to create group: {group['name']}", "ERROR")
                    
            except Exception as e:
                self.log(f"Error creating group {group['name']}: {str(e)}", "ERROR")
        
        self.log(f"Created {created_count} new groups", "SUCCESS")
        return created_count
    
    def create_group_memberships(self):
        """Create group memberships."""
        self.log("Creating group memberships...")
        
        # Define memberships: group_id -> [user_ids]
        memberships = {
            "660e8400-e29b-41d4-a716-446655440000": [  # Test Trip Group
                "550e8400-e29b-41d4-a716-446655440000",  # Admin
                "550e8400-e29b-41d4-a716-446655440001",  # Alice
                "550e8400-e29b-41d4-a716-446655440002",  # Bob
                "550e8400-e29b-41d4-a716-446655440003",  # Charlie
            ],
            "660e8400-e29b-41d4-a716-446655440001": [  # Office Lunch Squad
                "550e8400-e29b-41d4-a716-446655440001",  # Alice
                "550e8400-e29b-41d4-a716-446655440002",  # Bob
                "550e8400-e29b-41d4-a716-446655440004",  # Diana
            ],
            "660e8400-e29b-41d4-a716-446655440002": [  # Roommates
                "550e8400-e29b-41d4-a716-446655440000",  # Admin
                "550e8400-e29b-41d4-a716-446655440003",  # Charlie
            ]
        }
        
        created_count = 0
        for group_id, user_ids in memberships.items():
            for user_id in user_ids:
                try:
                    membership_id = str(uuid.uuid4())
                    membership_data = {
                        "id": membership_id,
                        "group_id": group_id,
                        "user_id": user_id
                    }
                    
                    # Check if membership already exists
                    existing = self.supabase.table("group_members").select("id").eq("group_id", group_id).eq("user_id", user_id).execute()
                    
                    if existing.data:
                        continue  # Skip if already exists
                    
                    resp = self.supabase.table("group_members").insert(membership_data).execute()
                    if resp.data:
                        created_count += 1
                    
                except Exception as e:
                    self.log(f"Error creating membership: {str(e)}", "ERROR")
        
        self.log(f"Created {created_count} group memberships", "SUCCESS")
        return created_count
    
    def create_bills(self):
        """Create test bills."""
        self.log("Creating test bills...")
        
        bills = [
            {
                "id": "770e8400-e29b-41d4-a716-446655440000",
                "group_id": "660e8400-e29b-41d4-a716-446655440000",  # Test Trip Group
                "payer_id": "550e8400-e29b-41d4-a716-446655440001",   # Alice
                "uploaded_by": "550e8400-e29b-41d4-a716-446655440001",
                "bill_date": (date.today() - timedelta(days=2)).isoformat(),
                "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat()
            },
            {
                "id": "770e8400-e29b-41d4-a716-446655440001",
                "group_id": "660e8400-e29b-41d4-a716-446655440001",  # Office Lunch Squad
                "payer_id": "550e8400-e29b-41d4-a716-446655440002",   # Bob
                "uploaded_by": "550e8400-e29b-41d4-a716-446655440002",
                "bill_date": (date.today() - timedelta(days=1)).isoformat(),
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
            },
            {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "group_id": "660e8400-e29b-41d4-a716-446655440000",  # Test Trip Group
                "payer_id": "550e8400-e29b-41d4-a716-446655440003",   # Charlie
                "uploaded_by": "550e8400-e29b-41d4-a716-446655440000", # Admin
                "bill_date": date.today().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        created_count = 0
        for bill in bills:
            try:
                # Check if bill already exists
                existing = self.supabase.table("bills").select("id").eq("id", bill["id"]).execute()
                
                if existing.data:
                    continue
                
                resp = self.supabase.table("bills").insert(bill).execute()
                if resp.data:
                    self.log(f"Created bill: {bill['id']}", "SUCCESS")
                    created_count += 1
                    
            except Exception as e:
                self.log(f"Error creating bill: {str(e)}", "ERROR")
        
        self.log(f"Created {created_count} bills", "SUCCESS")
        return created_count
    
    def create_items(self):
        """Create test items for bills."""
        self.log("Creating test items...")
        
        items = [
            # Items for Bill 1 (Mario's Pizza scenario)
            {
                "id": "880e8400-e29b-41d4-a716-446655440000",
                "bill_id": "770e8400-e29b-41d4-a716-446655440000",
                "name": "Margherita Pizza",
                "price": 18.99,
                "is_tax_or_tip": False
            },
            {
                "id": "880e8400-e29b-41d4-a716-446655440001",
                "bill_id": "770e8400-e29b-41d4-a716-446655440000",
                "name": "Garlic Bread",
                "price": 6.50,
                "is_tax_or_tip": False
            },
            {
                "id": "880e8400-e29b-41d4-a716-446655440002",
                "bill_id": "770e8400-e29b-41d4-a716-446655440000",
                "name": "Coca Cola",
                "price": 3.99,
                "is_tax_or_tip": False
            },
            {
                "id": "880e8400-e29b-41d4-a716-446655440003",
                "bill_id": "770e8400-e29b-41d4-a716-446655440000",
                "name": "Tax",
                "price": 2.51,
                "is_tax_or_tip": True
            },
            {
                "id": "880e8400-e29b-41d4-a716-446655440004",
                "bill_id": "770e8400-e29b-41d4-a716-446655440000",
                "name": "Tip",
                "price": 5.76,
                "is_tax_or_tip": True
            },
            # Items for Bill 2 (Lunch)
            {
                "id": "880e8400-e29b-41d4-a716-446655440005",
                "bill_id": "770e8400-e29b-41d4-a716-446655440001",
                "name": "Caesar Salad",
                "price": 12.50,
                "is_tax_or_tip": False
            },
            {
                "id": "880e8400-e29b-41d4-a716-446655440006",
                "bill_id": "770e8400-e29b-41d4-a716-446655440001",
                "name": "Grilled Chicken",
                "price": 16.00,
                "is_tax_or_tip": False
            },
            {
                "id": "880e8400-e29b-41d4-a716-446655440007",
                "bill_id": "770e8400-e29b-41d4-a716-446655440001",
                "name": "Coffee",
                "price": 4.50,
                "is_tax_or_tip": False
            },
            # Items for Bill 3 (Grocery)
            {
                "id": "880e8400-e29b-41d4-a716-446655440008",
                "bill_id": "770e8400-e29b-41d4-a716-446655440002",
                "name": "Groceries",
                "price": 45.67,
                "is_tax_or_tip": False
            },
            {
                "id": "880e8400-e29b-41d4-a716-446655440009",
                "bill_id": "770e8400-e29b-41d4-a716-446655440002",
                "name": "Cleaning Supplies",
                "price": 23.45,
                "is_tax_or_tip": False
            }
        ]
        
        created_count = 0
        for item in items:
            try:
                # Check if item already exists
                existing = self.supabase.table("items").select("id").eq("id", item["id"]).execute()
                
                if existing.data:
                    continue
                
                resp = self.supabase.table("items").insert(item).execute()
                if resp.data:
                    created_count += 1
                    
            except Exception as e:
                self.log(f"Error creating item: {str(e)}", "ERROR")
        
        self.log(f"Created {created_count} items", "SUCCESS")
        return created_count
    
    def create_votes(self):
        """Create test votes for items."""
        self.log("Creating test votes...")
        
        # Define voting patterns: item_id -> [user_ids who ate it]
        votes = {
            "880e8400-e29b-41d4-a716-446655440000": [  # Margherita Pizza
                "550e8400-e29b-41d4-a716-446655440001",  # Alice
                "550e8400-e29b-41d4-a716-446655440002",  # Bob
            ],
            "880e8400-e29b-41d4-a716-446655440001": [  # Garlic Bread
                "550e8400-e29b-41d4-a716-446655440001",  # Alice
                "550e8400-e29b-41d4-a716-446655440002",  # Bob
                "550e8400-e29b-41d4-a716-446655440003",  # Charlie
            ],
            "880e8400-e29b-41d4-a716-446655440002": [  # Coca Cola
                "550e8400-e29b-41d4-a716-446655440002",  # Bob
            ],
            "880e8400-e29b-41d4-a716-446655440005": [  # Caesar Salad
                "550e8400-e29b-41d4-a716-446655440001",  # Alice
                "550e8400-e29b-41d4-a716-446655440004",  # Diana
            ],
            "880e8400-e29b-41d4-a716-446655440006": [  # Grilled Chicken
                "550e8400-e29b-41d4-a716-446655440002",  # Bob
            ],
            "880e8400-e29b-41d4-a716-446655440007": [  # Coffee
                "550e8400-e29b-41d4-a716-446655440001",  # Alice
                "550e8400-e29b-41d4-a716-446655440002",  # Bob
                "550e8400-e29b-41d4-a716-446655440004",  # Diana
            ]
        }
        
        created_count = 0
        for item_id, user_ids in votes.items():
            for user_id in user_ids:
                try:
                    vote_id = str(uuid.uuid4())
                    vote_data = {
                        "id": vote_id,
                        "item_id": item_id,
                        "user_id": user_id,
                        "ate": True
                    }
                    
                    # Check if vote already exists
                    existing = self.supabase.table("votes").select("id").eq("item_id", item_id).eq("user_id", user_id).execute()
                    
                    if existing.data:
                        continue
                    
                    resp = self.supabase.table("votes").insert(vote_data).execute()
                    if resp.data:
                        created_count += 1
                        
                except Exception as e:
                    self.log(f"Error creating vote: {str(e)}", "ERROR")
        
        self.log(f"Created {created_count} votes", "SUCCESS")
        return created_count
    
    def setup_all_data(self):
        """Create all test data."""
        self.log("Setting up complete test data...", "INFO")
        
        if not self.check_connection():
            return False
        
        try:
            # Create data in order (dependencies)
            users = self.create_users()
            groups = self.create_groups()
            memberships = self.create_group_memberships()
            bills = self.create_bills()
            items = self.create_items()
            votes = self.create_votes()
            
            self.log("", "INFO")
            self.log("=== TEST DATA SETUP COMPLETE ===", "SUCCESS")
            self.log(f"Users: {users} created", "INFO")
            self.log(f"Groups: {groups} created", "INFO")
            self.log(f"Memberships: {memberships} created", "INFO")
            self.log(f"Bills: {bills} created", "INFO")
            self.log(f"Items: {items} created", "INFO")
            self.log(f"Votes: {votes} created", "INFO")
            self.log("", "INFO")
            self.log("READY Your database is now ready for full testing!", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"Setup failed: {str(e)}", "ERROR")
            return False
    
    def cleanup_all_data(self):
        """Remove all test data."""
        self.log("Cleaning up test data...", "INFO")
        
        if not self.check_connection():
            return False
        
        try:
            # Delete in reverse order (dependencies)
            deleted_counts = {}
            
            # Delete votes
            for user in self.test_data["users"]:
                resp = self.supabase.table("votes").delete().eq("user_id", user["id"]).execute()
            
            # Delete items  
            for group in self.test_data["groups"]:
                bills = self.supabase.table("bills").select("id").eq("group_id", group["id"]).execute()
                for bill in bills.data:
                    self.supabase.table("items").delete().eq("bill_id", bill["id"]).execute()
            
            # Delete bills
            for group in self.test_data["groups"]:
                self.supabase.table("bills").delete().eq("group_id", group["id"]).execute()
            
            # Delete group memberships
            for group in self.test_data["groups"]:
                self.supabase.table("group_members").delete().eq("group_id", group["id"]).execute()
            
            # Delete groups
            for group in self.test_data["groups"]:
                resp = self.supabase.table("groups").delete().eq("id", group["id"]).execute()
            
            # Delete users
            for user in self.test_data["users"]:
                resp = self.supabase.table("users").delete().eq("id", user["id"]).execute()
            
            self.log("Test data cleanup completed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Cleanup failed: {str(e)}", "ERROR")
            return False
    
    def check_status(self):
        """Check the status of test data."""
        self.log("Checking test data status...", "INFO")
        
        if not self.check_connection():
            return False
        
        try:
            # Check users
            user_count = 0
            for user in self.test_data["users"]:
                resp = self.supabase.table("users").select("id").eq("id", user["id"]).execute()
                if resp.data:
                    user_count += 1
            
            # Check groups
            group_count = 0
            for group in self.test_data["groups"]:
                resp = self.supabase.table("groups").select("id").eq("id", group["id"]).execute()
                if resp.data:
                    group_count += 1
            
            # Check bills
            bill_resp = self.supabase.table("bills").select("id").execute()
            bill_count = len([b for b in bill_resp.data if b["id"].startswith("770e8400")])
            
            self.log("", "INFO")
            self.log("=== TEST DATA STATUS ===", "INFO")
            self.log(f"Test Users: {user_count}/{len(self.test_data['users'])}", "INFO")
            self.log(f"Test Groups: {group_count}/{len(self.test_data['groups'])}", "INFO")
            self.log(f"Test Bills: {bill_count}/3", "INFO")
            
            if user_count == len(self.test_data["users"]) and group_count == len(self.test_data["groups"]):
                self.log("SUCCESS Test data is ready for testing!", "SUCCESS")
                return True
            else:
                self.log("WARNING Test data is incomplete. Run --setup to create missing data.", "WARNING")
                return False
            
        except Exception as e:
            self.log(f"Status check failed: {str(e)}", "ERROR")
            return False

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Manage test data for Splitwise Super Saiyan")
    parser.add_argument("--setup", action="store_true", help="Create test data")
    parser.add_argument("--cleanup", action="store_true", help="Remove test data")
    parser.add_argument("--status", action="store_true", help="Check test data status")
    
    args = parser.parse_args()
    
    if not any([args.setup, args.cleanup, args.status]):
        parser.print_help()
        return
    
    manager = TestDataManager()
    
    if args.setup:
        success = manager.setup_all_data()
        exit(0 if success else 1)
    elif args.cleanup:
        success = manager.cleanup_all_data()
        exit(0 if success else 1)
    elif args.status:
        success = manager.check_status()
        exit(0 if success else 1)

if __name__ == "__main__":
    main()