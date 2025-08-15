"""
Group management routes.
"""

import uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError
from uuid import UUID

from app.core.dependencies import get_current_user, get_database_service
from app.services.database import DatabaseService
from schemas import GroupCreate, GroupResponse, GroupMembersCreate, GroupMembersResponse

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("", response_model=GroupResponse)
async def create_group(
    group: GroupCreate,
    current_user = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Create a new group."""
    group_id = str(uuid.uuid4())
    data = {"id": group_id, "name": group.name}
    
    try:
        group_data = await database.create_group(data)
        return GroupResponse(
            id=UUID(group_data["id"]), 
            name=group_data["name"]
        )
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="Group with this ID already exists.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create group: {str(e)}")


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    current_user = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Get group by ID."""
    group_data = await database.get_group_by_id(group_id)
    if not group_data:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return GroupResponse(
        id=UUID(group_data["id"]), 
        name=group_data["name"]
    )


@router.get("/{group_id}/members")
async def get_group_members(
    group_id: str,
    current_user = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Get all members of a group with user details.
    """
    try:
        members = await database.get_group_members(group_id)
        return JSONResponse(content={"members": members})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get group members: {str(e)}")


@router.get("/{group_id}/bills")
async def get_group_bills(
    group_id: str,
    current_user = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Get all bills for a group.
    """
    try:
        from datetime import datetime
        
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
        
        bills_data = await database.get_group_bills(group_id)
        
        bills = []
        for bill in bills_data:
            bill_date = parse_date_only(bill["bill_date"])
            created_at = parse_date(bill["created_at"])
            
            if bill_date and created_at:
                # Get total bill amount
                items_response = database.client.table("items").select(
                    "price"
                ).eq("bill_id", bill["id"]).execute()
                
                total_amount = sum(item["price"] for item in items_response.data)
                
                bills.append({
                    "id": bill["id"],
                    "bill_date": bill_date.isoformat(),
                    "created_at": created_at.isoformat(),
                    "payer_id": bill["payer_id"],
                    "uploaded_by": bill["uploaded_by"],
                    "total_amount": total_amount
                })
        
        return JSONResponse(content={"bills": bills})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get group bills: {str(e)}")


# Group membership management

@router.post("/members", response_model=GroupMembersResponse)
async def add_user_to_group(
    membership: GroupMembersCreate,
    current_user = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Add user to group."""
    membership_id = str(uuid.uuid4())
    data = {
        "id": membership_id, 
        "group_id": str(membership.group_id), 
        "user_id": str(membership.user_id)
    }
    
    try:
        membership_data = await database.add_user_to_group(data)
        return GroupMembersResponse(
            id=UUID(membership_data["id"]), 
            group_id=UUID(membership_data["group_id"]), 
            user_id=UUID(membership_data["user_id"])
        )
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="User is already a member of this group.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add user to group: {str(e)}")


@router.get("/members/{membership_id}", response_model=GroupMembersResponse)
async def get_group_member(
    membership_id: str,
    current_user = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Get group member by membership ID."""
    try:
        resp = database.client.table("group_members").select("*").eq("id", membership_id).single().execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="Group member not found")
        
        return GroupMembersResponse(
            id=UUID(resp.data["id"]), 
            group_id=UUID(resp.data["group_id"]), 
            user_id=UUID(resp.data["user_id"])
        )
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Group member not found")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.delete("/members/{membership_id}")
async def remove_user_from_group(
    membership_id: str,
    current_user = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Remove user from group.
    """
    try:
        success = await database.remove_user_from_group(membership_id)
        if not success:
            raise HTTPException(status_code=404, detail="Group membership not found")
        
        return JSONResponse(content={
            "status": "deleted",
            "message": "User has been removed from the group",
            "membership_id": membership_id
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove user from group: {str(e)}")