import os
import uuid
from uuid import UUID
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from supabase import create_client, Client
from schemas import UserCreate, UserResponse, GroupCreate, GroupResponse, GroupMembersCreate, GroupMembersResponse, BillCreate, BillResponse, ItemCreate, ItemResponse, VoteCreate, VoteResponse
from typing import List
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from postgrest.exceptions import APIError
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from typing import Dict
from split_calculator import SplitCalculator

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

def parse_date(val):
    if isinstance(val, str):
        s = val.replace('Z', '+00:00')
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    return val

def parse_date_only(val):
    dt = parse_date(val)
    return dt.date() if dt else None

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    user_id = str(uuid.uuid4())
    data = {"id": user_id, "name": user.name, "email": user.email}
    try:
        resp = supabase.table("users").insert(data).execute()
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="User with this email already exists.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    # Return the actual user data, not the wrapper
    user_data = resp.data[0]  # Supabase returns an array
    return UserResponse(
        id=UUID(user_data["id"]), 
        name=user_data["name"], 
        email=user_data["email"]
    )

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    try:
        resp = supabase.table("users").select("*").eq("id", user_id).single().execute()
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="User not found")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    return UserResponse(id=UUID(resp.data["id"]), name=resp.data["name"], email=resp.data["email"])  # type: ignore[index]

@app.post("/groups", response_model=GroupResponse)
def create_group(group: GroupCreate):
    group_id = str(uuid.uuid4())
    data = {"id": group_id, "name": group.name}
    try:
        resp = supabase.table("groups").insert(data).execute()
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="Group with this ID already exists.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    # Return the actual group data, not the wrapper
    group_data = resp.data[0]
    return GroupResponse(
        id=UUID(group_data["id"]), 
        name=group_data["name"]
    )

@app.get("/groups/{group_id}", response_model=GroupResponse)
def get_group(group_id: str):
    try:
        resp = supabase.table("groups").select("*").eq("id", group_id).single().execute()
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Group not found")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    return GroupResponse(id=UUID(resp.data["id"]), name=resp.data["name"])  # type: ignore[index]

@app.post("/group_members", response_model=GroupMembersResponse)
def add_user_to_group(membership: GroupMembersCreate):
    membership_id = str(uuid.uuid4())
    data = {"id": membership_id, "group_id": str(membership.group_id), "user_id": str(membership.user_id)}
    try:
        resp = supabase.table("group_members").insert(data).execute()
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="User is already a member of this group.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    # Return the actual membership data, not the wrapper
    membership_data = resp.data[0]
    return GroupMembersResponse(
        id=UUID(membership_data["id"]), 
        group_id=UUID(membership_data["group_id"]), 
        user_id=UUID(membership_data["user_id"])
    )

@app.get("/group_members/{membership_id}", response_model=GroupMembersResponse)
def get_group_member(membership_id: str):
    try:
        resp = supabase.table("group_members").select("*").eq("id", membership_id).single().execute()
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Group member not found")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    return GroupMembersResponse(id=UUID(resp.data["id"]), group_id=UUID(resp.data["group_id"]), user_id=UUID(resp.data["user_id"]))  # type: ignore[index]

@app.post("/bills", response_model=BillResponse)
def create_bill(bill: BillCreate):
    bill_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    data = {
        "id": bill_id,
        "group_id": str(bill.group_id),
        "payer_id": str(bill.payer_id) if bill.payer_id else None,
        "uploaded_by": str(bill.uploaded_by) if bill.uploaded_by else None,
        "bill_date": bill.bill_date.isoformat(),
        "created_at": now
    }
    try:
        resp = supabase.table("bills").insert(data).execute()
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="Bill with this ID already exists.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    # Return the actual bill data, not the wrapper
    bill_data = resp.data[0]
    bill_date = parse_date_only(bill_data["bill_date"])
    created_at = parse_date(bill_data["created_at"])
    if bill_date is None or created_at is None:
        raise HTTPException(status_code=500, detail="Invalid date or datetime in bill record")
    
    return BillResponse(
        id=UUID(bill_data["id"]),
        group_id=UUID(bill_data["group_id"]),
        payer_id=UUID(bill_data["payer_id"]) if bill_data["payer_id"] else None,
        uploaded_by=UUID(bill_data["uploaded_by"]) if bill_data["uploaded_by"] else None,
        bill_date=bill_date,
        created_at=created_at
    )

@app.get("/bills/{bill_id}", response_model=BillResponse)
def get_bill(bill_id: str):
    try:
        resp = supabase.table("bills").select("*").eq("id", bill_id).single().execute()
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Bill not found")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    bill_date = parse_date_only(resp.data["bill_date"])  # type: ignore[index]
    created_at = parse_date(resp.data["created_at"])  # type: ignore[index]
    if bill_date is None or created_at is None:
        raise HTTPException(status_code=500, detail="Invalid date or datetime in bill record")
    return BillResponse(
        id=UUID(resp.data["id"]),  # type: ignore[index]
        group_id=UUID(resp.data["group_id"]),  # type: ignore[index]
        payer_id=UUID(resp.data["payer_id"]) if resp.data["payer_id"] else None,  # type: ignore[index]
        uploaded_by=UUID(resp.data["uploaded_by"]) if resp.data["uploaded_by"] else None,  # type: ignore[index]
        bill_date=bill_date,
        created_at=created_at
    )

@app.post("/items", response_model=ItemResponse)
def create_item(item: ItemCreate):
    item_id = str(uuid.uuid4())
    data = {
        "id": item_id,
        "bill_id": str(item.bill_id),
        "name": item.name,
        "price": float(item.price),
        "is_tax_or_tip": item.is_tax_or_tip
    }
    try:
        resp = supabase.table("items").insert(data).execute()
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="Item with this ID already exists.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    # Return the actual item data, not the wrapper
    item_data = resp.data[0]
    return ItemResponse(
        id=UUID(item_data["id"]),
        bill_id=UUID(item_data["bill_id"]),
        name=item_data["name"],
        price=item_data["price"],
        is_tax_or_tip=item_data["is_tax_or_tip"]
    )

@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: str):
    try:
        resp = supabase.table("items").select("*").eq("id", item_id).single().execute()
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Item not found")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    return ItemResponse(
        id=UUID(resp.data["id"]),  # type: ignore[index]
        bill_id=UUID(resp.data["bill_id"]),  # type: ignore[index]
        name=resp.data["name"],  # type: ignore[index]
        price=resp.data["price"],  # type: ignore[index]
        is_tax_or_tip=resp.data["is_tax_or_tip"]  # type: ignore[index]
    )

@app.post("/votes", response_model=VoteResponse)
def create_vote(vote: VoteCreate):
    vote_id = str(uuid.uuid4())
    data = {
        "id": vote_id,
        "item_id": str(vote.item_id),
        "user_id": str(vote.user_id),
        "ate": vote.ate
    }
    try:
        resp = supabase.table("votes").insert(data).execute()
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="Vote with this ID already exists.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    # Return the actual vote data, not the wrapper
    vote_data = resp.data[0]
    return VoteResponse(
        id=UUID(vote_data["id"]),
        item_id=UUID(vote_data["item_id"]),
        user_id=UUID(vote_data["user_id"]),
        ate=vote_data["ate"]
    )

@app.get("/votes/{vote_id}", response_model=VoteResponse)
def get_vote(vote_id: str):
    try:
        resp = supabase.table("votes").select("*").eq("id", vote_id).single().execute()
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Vote not found")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    return VoteResponse(
        id=UUID(resp.data["id"]),  # type: ignore[index]
        item_id=UUID(resp.data["item_id"]),  # type: ignore[index]
        user_id=UUID(resp.data["user_id"]),  # type: ignore[index]
        ate=resp.data["ate"]  # type: ignore[index]
    )

@app.get("/test-supabase", summary="Test Supabase connection", tags=["Test"])
async def test_supabase():
    try:
        resp = await run_in_threadpool(lambda: supabase.table("users").select("*").limit(1).execute())
    except APIError as e:
        if getattr(e, 'code', None) == '23505':
            raise HTTPException(status_code=409, detail="Resource already exists") from e
        raise HTTPException(status_code=500, detail=f"Unexpected Supabase error: {str(e)}") from e
    if getattr(resp, "error", None):  # type: ignore[attr-defined]
        return JSONResponse(status_code=500, content={"success": False, "data": None, "error": resp.error.message})  # type: ignore[attr-defined]
    return {"success": True, "data": resp.data}

# Add these endpoints to your FastAPI app:

@app.get("/bills/{bill_id}/split")
def get_bill_split(bill_id: str):
    """
    Calculate and return current split for a bill
    """
    try:
        # Get bill details
        bill_response = supabase.table("bills").select("*").eq("id", bill_id).single().execute()
        if not bill_response.data:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        bill = bill_response.data
        
        # Get items for this bill
        items_response = supabase.table("items").select("*").eq("bill_id", bill_id).execute()
        items = items_response.data
        
        # Get votes for all items
        votes_by_item = {}
        for item in items:
            votes_response = supabase.table("votes").select("user_id").eq("item_id", item["id"]).eq("ate", True).execute()
            votes_by_item[item["id"]] = [vote["user_id"] for vote in votes_response.data]
        
        # Calculate split
        calculator = SplitCalculator()
        split_result = calculator.calculate_bill_split(items, votes_by_item, bill["payer_id"])
        
        return JSONResponse(content=split_result)
        
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Bill not found")
        raise HTTPException(status_code=500, detail=f"Failed to calculate split: {str(e)}")


@app.post("/items/{item_id}/vote")
def toggle_item_vote(item_id: str, request: dict):
    """
    Toggle a user's vote on an item (ate/didn't eat)
    """
    try:
        user_id = request.get("user_id")
        ate = request.get("ate", True)
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Check if vote already exists
        existing_vote = supabase.table("votes").select("*").eq("item_id", item_id).eq("user_id", user_id).execute()
        
        if existing_vote.data:
            if ate:
                # Update existing vote to true
                supabase.table("votes").update({"ate": True}).eq("item_id", item_id).eq("user_id", user_id).execute()
                return JSONResponse(content={"status": "vote_updated", "ate": True})
            else:
                # Update existing vote to false
                supabase.table("votes").update({"ate": False}).eq("item_id", item_id).eq("user_id", user_id).execute()
                return JSONResponse(content={"status": "vote_updated", "ate": False})
        else:
            # Create new vote
            vote_data = {
                "id": str(uuid.uuid4()),
                "item_id": item_id,
                "user_id": user_id,
                "ate": ate
            }
            supabase.table("votes").insert(vote_data).execute()
            return JSONResponse(content={"status": "vote_created", "ate": ate})
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle vote: {str(e)}")


@app.get("/groups/{group_id}/members")
def get_group_members(group_id: str):
    """
    Get all members of a group with user details
    """
    try:
        # Get group members with user details
        response = supabase.table("group_members").select(
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
        
        return JSONResponse(content={"members": members})
        
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Group not found")
        raise HTTPException(status_code=500, detail=f"Failed to get group members: {str(e)}")


@app.get("/bills/{bill_id}/items")
def get_bill_items(bill_id: str):
    """
    Get all items for a bill with vote information
    """
    try:
        # Get items
        items_response = supabase.table("items").select("*").eq("bill_id", bill_id).execute()
        items = items_response.data
        
        # Get votes for each item
        for item in items:
            votes_response = supabase.table("votes").select("user_id, ate").eq("item_id", item["id"]).execute()
            item["votes"] = votes_response.data
        
        return JSONResponse(content={"items": items})
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bill items: {str(e)}")


@app.put("/bills/{bill_id}")
def update_bill(bill_id: str, request: dict):
    """
    Update bill details (like changing the payer)
    """
    try:
        update_data = {}
        
        if "payer_id" in request:
            update_data["payer_id"] = request["payer_id"]
        if "bill_date" in request:
            update_data["bill_date"] = request["bill_date"]
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        response = supabase.table("bills").update(update_data).eq("id", bill_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        return JSONResponse(content={"status": "updated", "bill": response.data[0]})
        
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Bill not found")
        raise HTTPException(status_code=500, detail=f"Failed to update bill: {str(e)}")


@app.put("/items/{item_id}")
def update_item(item_id: str, request: dict):
    """
    Update item details (name, price)
    """
    try:
        update_data = {}
        
        if "name" in request:
            update_data["name"] = request["name"]
        if "price" in request:
            update_data["price"] = float(request["price"])
        if "is_tax_or_tip" in request:
            update_data["is_tax_or_tip"] = request["is_tax_or_tip"]
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        response = supabase.table("items").update(update_data).eq("id", item_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Item not found")
        
        return JSONResponse(content={"status": "updated", "item": response.data[0]})
        
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Item not found")
        raise HTTPException(status_code=500, detail=f"Failed to update item: {str(e)}")

