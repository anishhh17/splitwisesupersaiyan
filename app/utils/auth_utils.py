"""
Authentication utilities for client-side Google OAuth integration.

This module provides utilities for:
1. Verifying Google ID tokens from client-side OAuth
2. Creating and validating backend JWT tokens
3. Managing user sessions and authentication state
"""

import os
import time
import jwt as pyjwt
import requests
from typing import Optional, Dict, Any
from fastapi import HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import uuid
from datetime import datetime, timedelta


class GoogleTokenVerifier:
    """Handles verification of Google ID tokens from client-side OAuth flow."""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.google_request = google_requests.Request()
    
    async def verify_id_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Google ID token and extract user information.
        
        Args:
            token: Google ID token from client-side OAuth
            
        Returns:
            Dict containing user information (sub, email, name, etc.)
            
        Raises:
            HTTPException: If token verification fails
        """
        try:
            # Verify the token with Google's servers
            id_info = id_token.verify_oauth2_token(
                token, 
                self.google_request, 
                self.client_id
            )
            
            # Verify the issuer
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            # Extract user information
            user_data = {
                'google_id': id_info['sub'],
                'email': id_info['email'],
                'name': id_info.get('name', ''),
                'given_name': id_info.get('given_name', ''),
                'family_name': id_info.get('family_name', ''),
                'picture': id_info.get('picture', ''),
                'email_verified': id_info.get('email_verified', False)
            }
            
            return user_data
            
        except ValueError as e:
            raise HTTPException(
                status_code=401, 
                detail=f"Invalid Google ID token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=401, 
                detail=f"Token verification failed: {str(e)}"
            )


class JWTManager:
    """Handles creation and validation of backend JWT tokens."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", expiration_seconds: int = 3600):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_seconds = expiration_seconds
    
    def create_token(self, user_id: str, email: str, name: str) -> str:
        """
        Create a JWT token for authenticated user.
        
        Args:
            user_id: User's UUID in the database
            email: User's email address
            name: User's display name
            
        Returns:
            Encoded JWT token string
        """
        expiration = time.time() + self.expiration_seconds
        payload = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "exp": expiration,
            "iat": time.time(),
            "iss": "splitbuddy-backend"
        }
        
        return pyjwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = pyjwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token hasn't expired
            if payload.get("exp", 0) < time.time():
                raise HTTPException(status_code=401, detail="Token has expired")
            
            return payload
            
        except pyjwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except pyjwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


class UserService:
    """Service for managing user authentication and database operations."""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def get_or_create_user(self, google_user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get existing user or create new user from Google OAuth data.
        
        Args:
            google_user_data: User data from Google ID token verification
            
        Returns:
            User data from database
            
        Raises:
            HTTPException: If user creation fails
        """
        email = google_user_data['email']
        name = google_user_data.get('name', google_user_data.get('given_name', 'Unknown'))
        
        try:
            # Check if user exists
            user_query = self.supabase.table("users").select("*").eq("email", email).execute()
            
            if user_query.data:
                # User exists, return existing user
                user = user_query.data[0]
                
                # Update name if it's different (user might have changed it on Google)
                if user['name'] != name:
                    update_resp = self.supabase.table("users").update({"name": name}).eq("id", user["id"]).execute()
                    if update_resp.data:
                        user = update_resp.data[0]
                
                return user
            else:
                # User doesn't exist, create new user
                user_id = str(uuid.uuid4())
                user_data = {
                    "id": user_id,
                    "name": name,
                    "email": email
                }
                
                user_resp = self.supabase.table("users").insert(user_data).execute()
                
                if not user_resp.data:
                    raise HTTPException(status_code=500, detail="Failed to create user")
                
                return user_resp.data[0]
                
        except Exception as e:
            if "Failed to create user" in str(e):
                raise e
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID from database.
        
        Args:
            user_id: User's UUID
            
        Returns:
            User data or None if not found
        """
        try:
            user_query = self.supabase.table("users").select("*").eq("id", user_id).execute()
            return user_query.data[0] if user_query.data else None
        except Exception:
            return None