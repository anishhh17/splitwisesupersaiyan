"""
Vote management routes.
"""

import uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError
from uuid import UUID

from app.core.dependencies import get_current_user, get_database_service
from app.services.database import DatabaseService
from schemas import VoteCreate, VoteResponse, UserResponse

router = APIRouter(prefix="/votes", tags=["Votes"])


@router.post("", response_model=VoteResponse)
async def create_vote(
    vote: VoteCreate,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Create a new vote."""
    vote_id = str(uuid.uuid4())
    data = {
        "id": vote_id,
        "item_id": str(vote.item_id),
        "user_id": str(vote.user_id),
        "ate": vote.ate
    }
    
    try:
        vote_data = await database.create_vote(data)
        return VoteResponse(
            id=UUID(vote_data["id"]),
            item_id=UUID(vote_data["item_id"]),
            user_id=UUID(vote_data["user_id"]),
            ate=vote_data["ate"]
        )
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="Vote with this ID already exists.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vote: {str(e)}")


@router.get("/{vote_id}", response_model=VoteResponse)
async def get_vote(
    vote_id: str,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Get vote by ID."""
    vote_data = await database.get_vote_by_id(vote_id)
    if not vote_data:
        raise HTTPException(status_code=404, detail="Vote not found")
    
    return VoteResponse(
        id=UUID(vote_data["id"]),
        item_id=UUID(vote_data["item_id"]),
        user_id=UUID(vote_data["user_id"]),
        ate=vote_data["ate"]
    )


@router.delete("/{vote_id}")
async def delete_vote(
    vote_id: str,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Delete a specific vote.
    """
    try:
        success = await database.delete_vote(vote_id)
        if not success:
            raise HTTPException(status_code=404, detail="Vote not found")
        
        return JSONResponse(content={
            "status": "deleted",
            "message": "Vote has been deleted",
            "vote_id": vote_id
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete vote: {str(e)}")