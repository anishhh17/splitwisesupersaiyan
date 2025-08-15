"""
FastAPI dependencies for authentication and common functionality.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID

from app.core.config import settings
from app.services.database import db_service
from app.utils.auth_utils import GoogleTokenVerifier, JWTManager, UserService
from schemas import UserResponse

# Initialize authentication services
security = HTTPBearer()
google_verifier = GoogleTokenVerifier(settings.GOOGLE_CLIENT_ID)
jwt_manager = JWTManager(settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM, settings.JWT_EXPIRATION_SECONDS)
user_service = UserService(db_service.client)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_token: Optional[str] = Cookie(None)
) -> UserResponse:
    """
    Dependency to get the current authenticated user from JWT token.
    Supports both Authorization header and cookie-based authentication.
    """
    # Try to get token from Authorization header first
    token = None
    if credentials:
        token = credentials.credentials
    
    # If not found, try to get from cookie
    if not token and auth_token:
        token = auth_token
    
    if not token:
        raise HTTPException(status_code=401, detail="Authentication credentials not provided")
    
    try:
        # Verify JWT token using the JWT manager
        payload = jwt_manager.verify_token(token)
        
        # Get user from database using the user service
        user_id = payload.get("user_id")
        user_data = await user_service.get_user_by_id(user_id)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="User not found")
            
        return UserResponse(
            id=UUID(user_data["id"]),
            name=user_data["name"],
            email=user_data["email"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")


def get_database_service():
    """Dependency to get the database service."""
    return db_service


def get_google_verifier():
    """Dependency to get the Google token verifier."""
    return google_verifier


def get_jwt_manager():
    """Dependency to get the JWT manager."""
    return jwt_manager


def get_user_service():
    """Dependency to get the user service."""
    return user_service