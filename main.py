import os
import uuid
import json
import time
from uuid import UUID
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request, Response, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.concurrency import run_in_threadpool
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config
from dotenv import load_dotenv
from supabase import create_client, Client
import jwt as pyjwt
import requests
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
from postgrest.exceptions import APIError
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from schemas import UserCreate, UserResponse, GroupCreate, GroupResponse, GroupMembersCreate, GroupMembersResponse, BillCreate, BillResponse, ItemCreate, ItemResponse, VoteCreate, VoteResponse
from split_calculator import SplitCalculator
from image_processing import extract_items_from_receipt
from file_validator import FileValidator
from rate_limiter import rate_limit

if os.getenv("ENVIRONMENT") != "production":  # or check other env var or use __name__ == '__main__'
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 3600  # 1 hour

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")
    
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise RuntimeError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in the environment.")

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY must be set in the environment.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize the FastAPI app with title and description
app = FastAPI(
    title="Splitwise Super Saiyan",
    description="A FastAPI app for splitting bills with friends"
)

# Configure SessionMiddleware with a secure secret key
app.add_middleware(
    SessionMiddleware, 
    secret_key=JWT_SECRET_KEY,
    max_age=JWT_EXPIRATION_SECONDS
)

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify server is running
    """
    return {"status": "ok"}

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_SCOPE = "openid email profile"

# Set up JWT authentication
security = HTTPBearer()

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_token: Optional[str] = Cookie(None)
) -> UserResponse:
    """
    Dependency to get the current authenticated user from JWT token
    Checks for token in both Authorization header and cookies
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
        # Decode JWT token
        payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Verify token hasn't expired
        if payload.get("exp") < time.time():
            raise HTTPException(status_code=401, detail="Token has expired")
        
        # Get user from Supabase
        user_id = payload.get("user_id")
        user_data = await run_in_threadpool(lambda: supabase.table("users").select("*").eq("id", user_id).single().execute())
        
        if not user_data.data:
            raise HTTPException(status_code=401, detail="User not found")
            
        return UserResponse(
            id=UUID(user_data.data["id"]),
            name=user_data.data["name"],
            email=user_data.data["email"]
        )
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

# === OAuth Authentication Routes ===

@app.get("/login")
async def login(request: Request):
    """
    Initiates Google OAuth login flow
    Redirects user to Google's authentication page
    """
    # Generate a random state for CSRF protection
    from secrets import token_urlsafe
    state = token_urlsafe(32)
    
    # Store state in session
    request.session["oauth_state"] = state
    
    # Get the base URL of the application
    base_url = str(request.base_url).rstrip("/")
    
    # Force HTTPS in production
    if os.getenv("ENVIRONMENT") == "production":
        base_url = base_url.replace("http://", "https://")
    
    redirect_uri = f"{base_url}/auth"
    
    # Construct Google OAuth URL
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    }
    
    # Build the authorize URL with parameters
    from urllib.parse import urlencode
    authorize_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    
    # Redirect to Google's authorization page
    return RedirectResponse(url=authorize_url)

@app.get("/auth")
# @rate_limit(max_requests=10, window_seconds=3600, per="ip")  # Limit to 10 auth requests per hour per IP
async def auth(request: Request):
    """
    Google OAuth callback route that handles the authorization code exchange
    Processes the OAuth response from Google, gets user info and creates or fetches the user
    Returns a JWT token for subsequent API authentication
    """
    try:
        # Extract the authorization code and state from query parameters
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        
        # Verify state to prevent CSRF attacks
        session_state = request.session.get("oauth_state")
        if not state or not session_state or state != session_state:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Clear the state from session
        request.session.pop("oauth_state", None)
        
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not provided")
        
        # Get the base URL of the application
        base_url = str(request.base_url).rstrip("/")
        
        # Force HTTPS in production
        if os.getenv("ENVIRONMENT") == "production":
            base_url = base_url.replace("http://", "https://")
        
        redirect_uri = f"{base_url}/auth"
        
        # Exchange authorization code for access token
        token_response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to obtain access token")
            
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Use access token to get user info
        userinfo_response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
            
        user_info = userinfo_response.json()
        
        if not user_info.get("email"):
            raise HTTPException(status_code=400, detail="Email not provided by Google")
            
        # Check if user exists in database
        user_email = user_info["email"]
        user_name = user_info.get("name", user_info.get("given_name", "Unknown"))
        
        user_query = supabase.table("users").select("*").eq("email", user_email).execute()
        
        # If user doesn't exist, create a new user
        if not user_query.data:
            user_create = UserCreate(name=user_name, email=user_email)
            user_id = str(uuid.uuid4())
            user_data = {"id": user_id, "name": user_create.name, "email": user_create.email}
            user_resp = supabase.table("users").insert(user_data).execute()
            
            if not user_resp.data:
                raise HTTPException(status_code=500, detail="Failed to create user")
                
            user = user_resp.data[0]
        else:
            # User already exists
            user = user_query.data[0]
        
        # Create JWT token
        expiration = time.time() + JWT_EXPIRATION_SECONDS
        payload = {
            "user_id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "exp": expiration
        }
        
        # Sign JWT token
        jwt_token = pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        # Create response with JWT token
        response = JSONResponse(
            content={"access_token": jwt_token, "token_type": "bearer", "expires_in": JWT_EXPIRATION_SECONDS}
        )
        
        # Set JWT as HTTP-only cookie for additional security
        IS_LOCAL = os.getenv("ENVIRONMENT") == "local"  # or check some other env var

        response.set_cookie(
            key="auth_token",
            value=jwt_token,
            httponly=True,
            secure=not IS_LOCAL,
            samesite="lax",
            max_age=JWT_EXPIRATION_SECONDS
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

@app.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """
    Returns the currently authenticated user's information
    Uses the JWT token from the Authorization header to authenticate
    """
    return current_user

@app.get("/logout")
async def logout():
    """
    Logs out the user by clearing the authentication cookie
    """
    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(key="auth_token")
    return response

@app.post("/process-bill-image")
@rate_limit(max_requests=5, window_seconds=60, per="user")  # Limit to 5 requests per minute per user
async def process_bill_image(
    file: UploadFile = File(...),
    group_id: str = Form(...),
    uploaded_by: str = Form(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Accepts a bill image, extracts items, creates bill and items in DB, and returns the created bill and items
    """
    try:
        # Validate the uploaded image file first
        image_bytes = await FileValidator.validate_image_file(file)
        result = extract_items_from_receipt(image_bytes)

        # Create bill
        bill_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        bill_data = {
            "id": bill_id,
            "group_id": group_id,
            "payer_id": None,
            "uploaded_by": uploaded_by,
            "bill_date": now.split("T")[0],
            "created_at": now
        }
        bill_resp = supabase.table("bills").insert(bill_data).execute()
        if not bill_resp.data:
            raise HTTPException(status_code=500, detail="Failed to create bill")

        # Insert items
        items_to_insert = []
        for item in result.get("items", []):
            items_to_insert.append({
                "id": str(uuid.uuid4()),
                "bill_id": bill_id,
                "name": item["name"],
                "price": float(item["price"]),
                "is_tax_or_tip": item.get("is_tax_or_tip", False)
            })
        # Add tax and tip as items if present and > 0
        if float(result.get("tax_amount", 0)) > 0:
            items_to_insert.append({
                "id": str(uuid.uuid4()),
                "bill_id": bill_id,
                "name": "Tax",
                "price": float(result["tax_amount"]),
                "is_tax_or_tip": True
            })
        if float(result.get("tip_amount", 0)) > 0:
            items_to_insert.append({
                "id": str(uuid.uuid4()),
                "bill_id": bill_id,
                "name": "Tip",
                "price": float(result["tip_amount"]),
                "is_tax_or_tip": True
            })
        items_resp = supabase.table("items").insert(items_to_insert).execute()
        if not items_resp.data:
            raise HTTPException(status_code=500, detail="Failed to create items")

        return JSONResponse(content={
            "bill": bill_resp.data[0],
            "items": items_resp.data,
            "extracted": result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

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
@rate_limit(max_requests=5, window_seconds=3600, per="ip")  # Limit to 5 user creations per hour per IP
def create_user(user: UserCreate, current_user: UserResponse = Depends(get_current_user)):
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
def get_user(user_id: str, current_user: UserResponse = Depends(get_current_user)):
    try:
        resp = supabase.table("users").select("*").eq("id", user_id).single().execute()
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="User not found")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    return UserResponse(id=UUID(resp.data["id"]), name=resp.data["name"], email=resp.data["email"])  # type: ignore[index]

@app.post("/groups", response_model=GroupResponse)
def create_group(group: GroupCreate, current_user: UserResponse = Depends(get_current_user)):
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
def get_group(group_id: str, current_user: UserResponse = Depends(get_current_user)):
    try:
        resp = supabase.table("groups").select("*").eq("id", group_id).single().execute()
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Group not found")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    return GroupResponse(id=UUID(resp.data["id"]), name=resp.data["name"])  # type: ignore[index]

@app.post("/group_members", response_model=GroupMembersResponse)
def add_user_to_group(membership: GroupMembersCreate, current_user: UserResponse = Depends(get_current_user)):
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
def get_group_member(membership_id: str, current_user: UserResponse = Depends(get_current_user)):
    try:
        resp = supabase.table("group_members").select("*").eq("id", membership_id).single().execute()
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Group member not found")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    return GroupMembersResponse(id=UUID(resp.data["id"]), group_id=UUID(resp.data["group_id"]), user_id=UUID(resp.data["user_id"]))  # type: ignore[index]

@app.post("/bills", response_model=BillResponse)
@rate_limit(max_requests=30, window_seconds=3600, per="user")  # Limit to 30 bill creations per hour per user
def create_bill(bill: BillCreate, current_user: UserResponse = Depends(get_current_user)):
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
def get_bill(bill_id: str, current_user: UserResponse = Depends(get_current_user)):
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
def create_item(item: ItemCreate, current_user: UserResponse = Depends(get_current_user)):
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
def get_item(item_id: str, current_user: UserResponse = Depends(get_current_user)):
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
def create_vote(vote: VoteCreate, current_user: UserResponse = Depends(get_current_user)):
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
def get_vote(vote_id: str, current_user: UserResponse = Depends(get_current_user)):
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
def get_bill_split(bill_id: str, current_user: UserResponse = Depends(get_current_user)):
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
def toggle_item_vote(item_id: str, request: dict, current_user: UserResponse = Depends(get_current_user)):
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
def get_group_members(group_id: str, current_user: UserResponse = Depends(get_current_user)):
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
def get_bill_items(bill_id: str, current_user: UserResponse = Depends(get_current_user)):
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
def update_bill(bill_id: str, request: dict, current_user: UserResponse = Depends(get_current_user)):
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
def update_item(item_id: str, request: dict, current_user: UserResponse = Depends(get_current_user)):
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


@app.delete("/bills/{bill_id}")
def delete_bill(bill_id: str, current_user: UserResponse = Depends(get_current_user)):
    """
    Delete a bill and all associated items/votes
    """
    try:
        # First, get the bill to ensure it exists and for data validation
        bill_response = supabase.table("bills").select("*").eq("id", bill_id).single().execute()
        if not bill_response.data:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        # Get all items associated with this bill
        items_response = supabase.table("items").select("id").eq("bill_id", bill_id).execute()
        item_ids = [item["id"] for item in items_response.data]
        
        # Delete votes associated with these items (delete them first due to foreign key constraints)
        if item_ids:
            for item_id in item_ids:
                # Delete votes for each item
                supabase.table("votes").delete().eq("item_id", item_id).execute()
        
        # Delete the items
        if item_ids:
            supabase.table("items").delete().eq("bill_id", bill_id).execute()
        
        # Finally delete the bill itself
        supabase.table("bills").delete().eq("id", bill_id).execute()
        
        return JSONResponse(content={
            "status": "deleted", 
            "message": "Bill and all associated items and votes have been deleted",
            "bill_id": bill_id
        })
        
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Bill not found")
        raise HTTPException(status_code=500, detail=f"Failed to delete bill: {str(e)}")


@app.delete("/items/{item_id}")
def delete_item(item_id: str, current_user: UserResponse = Depends(get_current_user)):
    """
    Delete an item and all its votes
    """
    try:
        # First, get the item to ensure it exists
        item_response = supabase.table("items").select("*").eq("id", item_id).single().execute()
        if not item_response.data:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Delete votes associated with this item first (due to foreign key constraints)
        supabase.table("votes").delete().eq("item_id", item_id).execute()
        
        # Then delete the item itself
        supabase.table("items").delete().eq("id", item_id).execute()
        
        return JSONResponse(content={
            "status": "deleted",
            "message": "Item and all associated votes have been deleted",
            "item_id": item_id
        })
        
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Item not found")
        raise HTTPException(status_code=500, detail=f"Failed to delete item: {str(e)}")


@app.delete("/votes/{vote_id}")
def delete_vote(vote_id: str, current_user: UserResponse = Depends(get_current_user)):
    """
    Delete a specific vote
    """
    try:
        # First, get the vote to ensure it exists
        vote_response = supabase.table("votes").select("*").eq("id", vote_id).single().execute()
        if not vote_response.data:
            raise HTTPException(status_code=404, detail="Vote not found")
        
        # Delete the vote
        supabase.table("votes").delete().eq("id", vote_id).execute()
        
        return JSONResponse(content={
            "status": "deleted",
            "message": "Vote has been deleted",
            "vote_id": vote_id
        })
        
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Vote not found")
        raise HTTPException(status_code=500, detail=f"Failed to delete vote: {str(e)}")


@app.get("/users/search")
def search_users(email: str = None, name: str = None, current_user: UserResponse = Depends(get_current_user)):
    """
    Search users by email or name to add to groups
    """
    try:
        if not email and not name:
            raise HTTPException(status_code=400, detail="Either email or name parameter is required")
        
        # Build the query
        query = supabase.table("users").select("id, name, email")
        
        # Apply filters based on provided parameters
        if email:
            query = query.ilike("email", f"%{email}%")
        if name:
            query = query.ilike("name", f"%{name}%")
        
        # Execute the query with a reasonable limit
        response = query.limit(10).execute()
        
        users = []
        for user in response.data:
            users.append({
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            })
        
        return JSONResponse(content={"users": users})
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Failed to search users: {str(e)}")


@app.delete("/group_members/{membership_id}")
def remove_user_from_group(membership_id: str, current_user: UserResponse = Depends(get_current_user)):
    """
    Remove user from group
    """
    try:
        # First, get the membership to ensure it exists
        membership_response = supabase.table("group_members").select("*").eq("id", membership_id).single().execute()
        if not membership_response.data:
            raise HTTPException(status_code=404, detail="Group membership not found")
        
        # Delete the membership
        supabase.table("group_members").delete().eq("id", membership_id).execute()
        
        return JSONResponse(content={
            "status": "deleted",
            "message": "User has been removed from the group",
            "membership_id": membership_id
        })
        
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116":
            raise HTTPException(status_code=404, detail="Group membership not found")
        raise HTTPException(status_code=500, detail=f"Failed to remove user from group: {str(e)}")


@app.get("/users/{user_id}/groups")
def get_user_groups(user_id: str, current_user: UserResponse = Depends(get_current_user)):
    """
    Get all groups a user belongs to
    """
    try:
        # Get all group memberships for this user
        memberships_response = supabase.table("group_members").select(
            "group_id, groups(*)"
        ).eq("user_id", user_id).execute()
        
        if not memberships_response.data:
            return JSONResponse(content={"groups": []})
        
        # Extract group information
        groups = []
        for membership in memberships_response.data:
            group_data = membership["groups"]
            if group_data:  # Ensure group exists
                groups.append({
                    "id": group_data["id"],
                    "name": group_data["name"]
                })
        
        return JSONResponse(content={"groups": groups})
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user groups: {str(e)}")


@app.get("/groups/{group_id}/bills")
def get_group_bills(group_id: str, current_user: UserResponse = Depends(get_current_user)):
    """
    Get all bills for a group
    """
    try:
        # Get all bills for this group
        bills_response = supabase.table("bills").select(
            "*"
        ).eq("group_id", group_id).order("bill_date", desc=True).execute()
        
        bills = []
        for bill in bills_response.data:
            bill_date = parse_date_only(bill["bill_date"])
            created_at = parse_date(bill["created_at"])
            
            if bill_date and created_at:
                # Get total bill amount
                items_response = supabase.table("items").select(
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
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Failed to get group bills: {str(e)}")

