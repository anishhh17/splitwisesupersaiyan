"""
Database service layer for Supabase operations.
Provides centralized database access and common query patterns.
"""

from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from app.core.config import settings


class DatabaseService:
    """Service for interacting with Supabase database."""
    
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # User operations
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            response = self.client.table("users").select("*").eq("id", user_id).single().execute()
            return response.data
        except Exception:
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        try:
            response = self.client.table("users").select("*").eq("email", email).execute()
            return response.data[0] if response.data else None
        except Exception:
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        response = self.client.table("users").insert(user_data).execute()
        if not response.data:
            raise Exception("Failed to create user")
        return response.data[0]
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data."""
        response = self.client.table("users").update(update_data).eq("id", user_id).execute()
        if not response.data:
            raise Exception("Failed to update user")
        return response.data[0]
    
    async def search_users(self, email: Optional[str] = None, name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search users by email or name."""
        query = self.client.table("users").select("id, name, email")
        
        if email:
            query = query.ilike("email", f"%{email}%")
        if name:
            query = query.ilike("name", f"%{name}%")
        
        response = query.limit(limit).execute()
        return response.data
    
    # Group operations
    async def create_group(self, group_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new group."""
        response = self.client.table("groups").insert(group_data).execute()
        if not response.data:
            raise Exception("Failed to create group")
        return response.data[0]
    
    async def get_group_by_id(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get group by ID."""
        try:
            response = self.client.table("groups").select("*").eq("id", group_id).single().execute()
            return response.data
        except Exception:
            return None
    
    async def get_group_members(self, group_id: str) -> List[Dict[str, Any]]:
        """Get all members of a group with user details."""
        response = self.client.table("group_members").select(
            "*, users(id, name, email)"
        ).eq("group_id", group_id).execute()
        
        members = []
        for member in response.data:
            user_data = member["users"]
            members.append({
                "membership_id": member["id"],
                "user_id": user_data["id"],
                "name": user_data["name"],
                "email": user_data["email"]
            })
        return members
    
    async def add_user_to_group(self, membership_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add user to group."""
        response = self.client.table("group_members").insert(membership_data).execute()
        if not response.data:
            raise Exception("Failed to add user to group")
        return response.data[0]
    
    async def remove_user_from_group(self, membership_id: str) -> bool:
        """Remove user from group."""
        # Check if membership exists first
        response = self.client.table("group_members").select("*").eq("id", membership_id).single().execute()
        if not response.data:
            return False
        
        # Delete the membership
        self.client.table("group_members").delete().eq("id", membership_id).execute()
        return True
    
    async def get_user_groups(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all groups a user belongs to."""
        response = self.client.table("group_members").select(
            "group_id, groups(*)"
        ).eq("user_id", user_id).execute()
        
        groups = []
        for membership in response.data:
            group_data = membership["groups"]
            if group_data:
                groups.append({
                    "id": group_data["id"],
                    "name": group_data["name"]
                })
        return groups
    
    # Bill operations
    async def create_bill(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new bill."""
        response = self.client.table("bills").insert(bill_data).execute()
        if not response.data:
            raise Exception("Failed to create bill")
        return response.data[0]
    
    async def get_bill_by_id(self, bill_id: str) -> Optional[Dict[str, Any]]:
        """Get bill by ID."""
        try:
            response = self.client.table("bills").select("*").eq("id", bill_id).single().execute()
            return response.data
        except Exception:
            return None
    
    async def update_bill(self, bill_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update bill data."""
        response = self.client.table("bills").update(update_data).eq("id", bill_id).execute()
        if not response.data:
            raise Exception("Failed to update bill")
        return response.data[0]
    
    async def delete_bill(self, bill_id: str) -> bool:
        """Delete a bill and all associated items/votes."""
        # Get all items associated with this bill
        items_response = self.client.table("items").select("id").eq("bill_id", bill_id).execute()
        item_ids = [item["id"] for item in items_response.data]
        
        # Delete votes for each item
        if item_ids:
            for item_id in item_ids:
                self.client.table("votes").delete().eq("item_id", item_id).execute()
        
        # Delete the items
        if item_ids:
            self.client.table("items").delete().eq("bill_id", bill_id).execute()
        
        # Delete the bill
        self.client.table("bills").delete().eq("id", bill_id).execute()
        return True
    
    async def get_group_bills(self, group_id: str) -> List[Dict[str, Any]]:
        """Get all bills for a group."""
        response = self.client.table("bills").select("*").eq("group_id", group_id).order("bill_date", desc=True).execute()
        return response.data
    
    # Item operations
    async def create_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item."""
        response = self.client.table("items").insert(item_data).execute()
        if not response.data:
            raise Exception("Failed to create item")
        return response.data[0]
    
    async def create_items_bulk(self, items_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple items at once."""
        response = self.client.table("items").insert(items_data).execute()
        if not response.data:
            raise Exception("Failed to create items")
        return response.data
    
    async def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item by ID."""
        try:
            response = self.client.table("items").select("*").eq("id", item_id).single().execute()
            return response.data
        except Exception:
            return None
    
    async def update_item(self, item_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update item data."""
        response = self.client.table("items").update(update_data).eq("id", item_id).execute()
        if not response.data:
            raise Exception("Failed to update item")
        return response.data[0]
    
    async def delete_item(self, item_id: str) -> bool:
        """Delete an item and all its votes."""
        # Delete votes associated with this item first
        self.client.table("votes").delete().eq("item_id", item_id).execute()
        
        # Delete the item
        self.client.table("items").delete().eq("id", item_id).execute()
        return True
    
    async def get_bill_items(self, bill_id: str) -> List[Dict[str, Any]]:
        """Get all items for a bill with vote information."""
        items_response = self.client.table("items").select("*").eq("bill_id", bill_id).execute()
        items = items_response.data
        
        # Get votes for each item
        for item in items:
            votes_response = self.client.table("votes").select("user_id, ate").eq("item_id", item["id"]).execute()
            item["votes"] = votes_response.data
        
        return items
    
    # Vote operations
    async def create_vote(self, vote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new vote."""
        response = self.client.table("votes").insert(vote_data).execute()
        if not response.data:
            raise Exception("Failed to create vote")
        return response.data[0]
    
    async def get_vote_by_id(self, vote_id: str) -> Optional[Dict[str, Any]]:
        """Get vote by ID."""
        try:
            response = self.client.table("votes").select("*").eq("id", vote_id).single().execute()
            return response.data
        except Exception:
            return None
    
    async def delete_vote(self, vote_id: str) -> bool:
        """Delete a vote."""
        # Check if vote exists first
        response = self.client.table("votes").select("*").eq("id", vote_id).single().execute()
        if not response.data:
            return False
        
        # Delete the vote
        self.client.table("votes").delete().eq("id", vote_id).execute()
        return True
    
    async def toggle_item_vote(self, item_id: str, user_id: str, ate: bool) -> Dict[str, str]:
        """Toggle a user's vote on an item."""
        # Check if vote already exists
        existing_vote = self.client.table("votes").select("*").eq("item_id", item_id).eq("user_id", user_id).execute()
        
        if existing_vote.data:
            # Update existing vote
            self.client.table("votes").update({"ate": ate}).eq("item_id", item_id).eq("user_id", user_id).execute()
            return {"status": "vote_updated", "ate": str(ate)}
        else:
            # Create new vote
            import uuid
            vote_data = {
                "id": str(uuid.uuid4()),
                "item_id": item_id,
                "user_id": user_id,
                "ate": ate
            }
            self.client.table("votes").insert(vote_data).execute()
            return {"status": "vote_created", "ate": str(ate)}
    
    async def get_item_votes(self, item_id: str) -> List[Dict[str, Any]]:
        """Get all votes for an item."""
        response = self.client.table("votes").select("user_id").eq("item_id", item_id).eq("ate", True).execute()
        return [vote["user_id"] for vote in response.data]


# Global database service instance
db_service = DatabaseService()