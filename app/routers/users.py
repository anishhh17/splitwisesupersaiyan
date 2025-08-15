"""
User management routes.
"""

import uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError
from uuid import UUID

from app.core.dependencies import get_current_user, get_database_service
from app.services.database import DatabaseService
from schemas import UserCreate, UserResponse
from app.utils.rate_limiter import rate_limit

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse)
@rate_limit(max_requests=5, window_seconds=3600, per="ip")
async def create_user(
    user: UserCreate,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Create a new user."""
    user_id = str(uuid.uuid4())
    data = {"id": user_id, "name": user.name, "email": user.email}
    
    try:
        user_data = await database.create_user(data)
        return UserResponse(
            id=UUID(user_data["id"]), 
            name=user_data["name"], 
            email=user_data["email"]
        )
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="User with this email already exists.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/search")
async def search_users(
    email: str = None,
    name: str = None,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Search users by email or name to add to groups.
    """
    if not email and not name:
        raise HTTPException(status_code=400, detail="Either email or name parameter is required")
    
    try:
        users = await database.search_users(email=email, name=name)
        return JSONResponse(content={"users": users})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search users: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Get user by ID."""
    user_data = await database.get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=UUID(user_data["id"]), 
        name=user_data["name"], 
        email=user_data["email"]
    )


@router.get("/{user_id}/groups")
async def get_user_groups(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Get all groups a user belongs to.
    """
    try:
        groups = await database.get_user_groups(user_id)
        return JSONResponse(content={"groups": groups})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user groups: {str(e)}")