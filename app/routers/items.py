"""
Item management routes.
"""

import uuid
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError
from uuid import UUID

from app.core.dependencies import get_current_user, get_database_service
from app.services.database import DatabaseService
from schemas import ItemCreate, ItemResponse, UserResponse

router = APIRouter(prefix="/items", tags=["Items"])


@router.post("", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Create a new item."""
    item_id = str(uuid.uuid4())
    data = {
        "id": item_id,
        "bill_id": str(item.bill_id),
        "name": item.name,
        "price": float(item.price),
        "is_tax_or_tip": item.is_tax_or_tip
    }
    
    try:
        item_data = await database.create_item(data)
        return ItemResponse(
            id=UUID(item_data["id"]),
            bill_id=UUID(item_data["bill_id"]),
            name=item_data["name"],
            price=float(item_data["price"]),
            is_tax_or_tip=item_data["is_tax_or_tip"]
        )
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="Item with this ID already exists.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create item: {str(e)}")


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: str,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Get item by ID."""
    item_data = await database.get_item_by_id(item_id)
    if not item_data:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return ItemResponse(
        id=UUID(item_data["id"]),
        bill_id=UUID(item_data["bill_id"]),
        name=item_data["name"],
        price=float(item_data["price"]),
        is_tax_or_tip=item_data["is_tax_or_tip"]
    )


@router.put("/{item_id}")
async def update_item(
    item_id: str,
    request: dict,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Update item details (name, price).
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
        
        item_data = await database.update_item(item_id, update_data)
        return JSONResponse(content={"status": "updated", "item": item_data})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update item: {str(e)}")


@router.delete("/{item_id}")
async def delete_item(
    item_id: str,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Delete an item and all its votes.
    """
    try:
        # Check if item exists first
        item_data = await database.get_item_by_id(item_id)
        if not item_data:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Delete item and all related votes
        await database.delete_item(item_id)
        
        return JSONResponse(content={
            "status": "deleted",
            "message": "Item and all associated votes have been deleted",
            "item_id": item_id
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete item: {str(e)}")


@router.post("/{item_id}/vote")
async def toggle_item_vote(
    item_id: str,
    request: dict,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Toggle a user's vote on an item (ate/didn't eat).
    """
    try:
        user_id = request.get("user_id")
        ate = request.get("ate", True)
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        result = await database.toggle_item_vote(item_id, user_id, ate)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle vote: {str(e)}")