import uuid
from datetime import date, datetime

# Supabase usage examples for each table
# NOTE: These are reference examples. You must initialize 'supabase' elsewhere in your code:
# from supabase import create_client; supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

"""
User Table
----------
Schema: id (uuid), name (str), email (str)
"""
# Insert a user
user_data = {
    "name": "Alice",
    "email": "alice@example.com"
}
"""
supabase.table("users").insert(user_data).execute()

# Query a user by email
user = supabase.table("users").select("*").eq("email", "alice@example.com").execute().data
"""

"""
Group Table
-----------
Schema: id (uuid), name (str)
"""
# Insert a group
group_data = {
    "name": "Trip to Paris"
}
"""
supabase.table("groups").insert(group_data).execute()

# Query all groups
groups = supabase.table("groups").select("*").execute().data
"""

"""
GroupMembers Table
------------------
Schema: id (uuid), group_id (uuid), user_id (uuid)
"""
# Add a user to a group
group_member_data = {
    "group_id": "group-uuid",
    "user_id": "user-uuid"
}
"""
supabase.table("group_members").insert(group_member_data).execute()

# Query members of a group
members = supabase.table("group_members").select("*").eq("group_id", "group-uuid").execute().data
"""

"""
Bill Table
----------
Schema: id (uuid), group_id (uuid), payer_id (uuid, nullable), uploaded_by (uuid, nullable), bill_date (date), created_at (datetime)
"""
# Insert a bill
bill_data = {
    "group_id": "group-uuid",
    "payer_id": "user-uuid",
    "uploaded_by": "user-uuid",
    "bill_date": "2024-06-01",
    "created_at": "2024-06-01T12:00:00Z"
}
"""
supabase.table("bills").insert(bill_data).execute()

# Query bills by group
bills = supabase.table("bills").select("*").eq("group_id", "group-uuid").execute().data
"""

"""
Item Table
----------
Schema: id (uuid), bill_id (uuid), name (str), price (decimal), is_tax_or_tip (bool)
"""
# Insert an item
item_data = {
    "bill_id": "bill-uuid",
    "name": "Pizza",
    "price": 19.99,
    "is_tax_or_tip": False
}
"""
supabase.table("items").insert(item_data).execute()

# Query items for a bill
items = supabase.table("items").select("*").eq("bill_id", "bill-uuid").execute().data
"""

"""
Vote Table
----------
Schema: id (uuid), item_id (uuid), user_id (uuid), ate (bool)
"""
# Insert a vote
vote_data = {
    "item_id": "item-uuid",
    "user_id": "user-uuid",
    "ate": True
}
"""
supabase.table("votes").insert(vote_data).execute()

# Query votes for an item
votes = supabase.table("votes").select("*").eq("item_id", "item-uuid").execute().data
""" 