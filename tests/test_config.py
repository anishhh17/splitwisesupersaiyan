"""
Test Configuration for Splitwise Super Saiyan Tests

This module provides consistent test data IDs and configuration
that can be used across all test files.
"""

import time
import jwt as pyjwt

# Base URL for API testing
BASE_URL = "http://127.0.0.1:8000"

# Import real JWT settings from app configuration
import os
from dotenv import load_dotenv

# Load environment variables to get real JWT settings
load_dotenv()

# JWT Configuration (using same settings as the app)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "test_secret_key_for_development_only")
JWT_ALGORITHM = "HS256"

# Test User IDs (created by setup_test_data.py)
TEST_USERS = {
    "admin": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Test Admin",
        "email": "admin@test.com"
    },
    "alice": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Alice Johnson", 
        "email": "alice@test.com"
    },
    "bob": {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "Bob Smith",
        "email": "bob@test.com"
    },
    "charlie": {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "name": "Charlie Brown",
        "email": "charlie@test.com"
    },
    "diana": {
        "id": "550e8400-e29b-41d4-a716-446655440004",
        "name": "Diana Prince",
        "email": "diana@test.com"
    }
}

# Test Group IDs
TEST_GROUPS = {
    "trip": {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "name": "Test Trip Group",
        "members": ["admin", "alice", "bob", "charlie"]
    },
    "lunch": {
        "id": "660e8400-e29b-41d4-a716-446655440001", 
        "name": "Office Lunch Squad",
        "members": ["alice", "bob", "diana"]
    },
    "roommates": {
        "id": "660e8400-e29b-41d4-a716-446655440002",
        "name": "Roommates", 
        "members": ["admin", "charlie"]
    }
}

# Test Bill IDs
TEST_BILLS = {
    "pizza": {
        "id": "770e8400-e29b-41d4-a716-446655440000",
        "group_id": "660e8400-e29b-41d4-a716-446655440000",  # trip
        "payer_id": "550e8400-e29b-41d4-a716-446655440001",   # alice
        "items": ["margherita", "garlic_bread", "coca_cola", "tax", "tip"]
    },
    "lunch": {
        "id": "770e8400-e29b-41d4-a716-446655440001",
        "group_id": "660e8400-e29b-41d4-a716-446655440001",  # lunch
        "payer_id": "550e8400-e29b-41d4-a716-446655440002",   # bob  
        "items": ["caesar_salad", "grilled_chicken", "coffee"]
    },
    "grocery": {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "group_id": "660e8400-e29b-41d4-a716-446655440000",  # trip
        "payer_id": "550e8400-e29b-41d4-a716-446655440003",   # charlie
        "items": ["groceries", "cleaning_supplies"]
    }
}

# Test Item IDs
TEST_ITEMS = {
    "margherita": {
        "id": "880e8400-e29b-41d4-a716-446655440000",
        "bill_id": "770e8400-e29b-41d4-a716-446655440000",
        "name": "Margherita Pizza",
        "price": 18.99,
        "voters": ["alice", "bob"]
    },
    "garlic_bread": {
        "id": "880e8400-e29b-41d4-a716-446655440001",
        "bill_id": "770e8400-e29b-41d4-a716-446655440000",
        "name": "Garlic Bread",
        "price": 6.50,
        "voters": ["alice", "bob", "charlie"]
    },
    "coca_cola": {
        "id": "880e8400-e29b-41d4-a716-446655440002",
        "bill_id": "770e8400-e29b-41d4-a716-446655440000",
        "name": "Coca Cola", 
        "price": 3.99,
        "voters": ["bob"]
    },
    "tax": {
        "id": "880e8400-e29b-41d4-a716-446655440003",
        "bill_id": "770e8400-e29b-41d4-a716-446655440000",
        "name": "Tax",
        "price": 2.51,
        "voters": []
    },
    "tip": {
        "id": "880e8400-e29b-41d4-a716-446655440004",
        "bill_id": "770e8400-e29b-41d4-a716-446655440000",
        "name": "Tip",
        "price": 5.76,
        "voters": []
    },
    "caesar_salad": {
        "id": "880e8400-e29b-41d4-a716-446655440005",
        "bill_id": "770e8400-e29b-41d4-a716-446655440001",
        "name": "Caesar Salad",
        "price": 12.50,
        "voters": ["alice", "diana"]
    },
    "grilled_chicken": {
        "id": "880e8400-e29b-41d4-a716-446655440006",
        "bill_id": "770e8400-e29b-41d4-a716-446655440001",
        "name": "Grilled Chicken",
        "price": 16.00,
        "voters": ["bob"]
    },
    "coffee": {
        "id": "880e8400-e29b-41d4-a716-446655440007", 
        "bill_id": "770e8400-e29b-41d4-a716-446655440001",
        "name": "Coffee",
        "price": 4.50,
        "voters": ["alice", "bob", "diana"]
    },
    "groceries": {
        "id": "880e8400-e29b-41d4-a716-446655440008",
        "bill_id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "Groceries",
        "price": 45.67,
        "voters": []
    },
    "cleaning_supplies": {
        "id": "880e8400-e29b-41d4-a716-446655440009",
        "bill_id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "Cleaning Supplies",
        "price": 23.45,
        "voters": []
    }
}

def generate_test_jwt_token(user_key="admin", expired=False):
    """
    Generate a JWT token for testing using real test user data.
    
    Args:
        user_key: Key from TEST_USERS dict (admin, alice, bob, charlie, diana)
        expired: Whether to create an expired token
        
    Returns:
        Tuple of (jwt_token, user_id)
    """
    if user_key not in TEST_USERS:
        raise ValueError(f"Unknown user key: {user_key}. Use one of: {list(TEST_USERS.keys())}")
    
    user = TEST_USERS[user_key]
    
    # Create token payload
    expiration = time.time() - 3600 if expired else time.time() + 3600  # -1 hour or +1 hour
    payload = {
        "user_id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "exp": expiration,
        "iat": time.time(),
        "iss": "splitbuddy-backend"
    }
    
    # Sign JWT token
    jwt_token = pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return jwt_token, user["id"]

def get_user_id(user_key):
    """Get user ID by key."""
    return TEST_USERS[user_key]["id"]

def get_group_id(group_key):
    """Get group ID by key."""
    return TEST_GROUPS[group_key]["id"] 

def get_bill_id(bill_key):
    """Get bill ID by key."""
    return TEST_BILLS[bill_key]["id"]

def get_item_id(item_key):
    """Get item ID by key."""
    return TEST_ITEMS[item_key]["id"]

def safe_json(resp):
    """Safely parse JSON response or return text."""
    try:
        return resp.json()
    except Exception:
        return resp.text

# Expected bill split results for testing
EXPECTED_SPLITS = {
    "pizza": {
        # Based on Mario's Pizza receipt with voting pattern
        "total": 37.75,
        "payer": "alice",  # Alice paid
        "splits": {
            "alice": -7.08,   # Alice gets money back (she paid and ate less)
            "bob": 14.16,     # Bob owes (ate pizza + bread + drink) 
            "charlie": 2.17,  # Charlie owes (ate bread only)
            "admin": 0.0      # Admin didn't eat anything
        }
    }
}