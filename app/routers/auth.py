"""
Authentication routes for client-side Google OAuth integration.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.dependencies import get_google_verifier, get_jwt_manager, get_user_service, get_current_user
from app.utils.auth_utils import GoogleTokenVerifier, JWTManager, UserService
from schemas import GoogleAuthRequest, AuthResponse, UserResponse
from app.utils.rate_limiter import rate_limit

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/google", response_model=AuthResponse)
@rate_limit(max_requests=10, window_seconds=3600, per="ip")
async def authenticate_google(
    auth_request: GoogleAuthRequest,
    google_verifier: GoogleTokenVerifier = Depends(get_google_verifier),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
    user_service: UserService = Depends(get_user_service)
):
    """
    Authenticate user with Google ID token from client-side OAuth.
    
    This endpoint:
    1. Verifies the Google ID token with Google's servers
    2. Creates or retrieves the user from the database
    3. Issues a backend JWT token for subsequent requests
    
    Args:
        auth_request: Contains the Google ID token from client-side OAuth
        
    Returns:
        AuthResponse with access token and user information
    """
    try:
        # Verify Google ID token
        google_user_data = await google_verifier.verify_id_token(auth_request.id_token)
        
        # Get or create user in database
        user_data = await user_service.get_or_create_user(google_user_data)
        
        # Create backend JWT token
        access_token = jwt_manager.create_token(
            user_id=user_data["id"],
            email=user_data["email"],
            name=user_data["name"]
        )
        
        # Return authentication response
        return AuthResponse(
            access_token=access_token,
            expires_in=settings.JWT_EXPIRATION_SECONDS,
            user={
                "id": user_data["id"],
                "name": user_data["name"],
                "email": user_data["email"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.post("/refresh")
async def refresh_token(
    current_user: UserResponse = Depends(get_current_user),
    jwt_manager: JWTManager = Depends(get_jwt_manager)
):
    """
    Refresh the current user's JWT token.
    
    This endpoint allows clients to refresh their authentication token
    before it expires, providing a seamless user experience.
    """
    try:
        # Create a new JWT token for the current user
        access_token = jwt_manager.create_token(
            user_id=str(current_user.id),
            email=current_user.email,
            name=current_user.name
        )
        
        return JSONResponse(content={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRATION_SECONDS
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")


@router.post("/logout")
async def logout():
    """
    Logout endpoint for client-side applications.
    
    Since we're using stateless JWT tokens, logout is primarily handled
    client-side by removing the token. This endpoint provides a standard
    logout response and can be extended for additional cleanup if needed.
    """
    return JSONResponse(content={
        "message": "Successfully logged out",
        "instructions": "Remove the access token from client storage"
    })


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """
    Returns the currently authenticated user's information.
    Uses the JWT token from the Authorization header to authenticate.
    """
    return current_user