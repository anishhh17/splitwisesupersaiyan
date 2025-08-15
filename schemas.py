from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

# -------------------- User Models --------------------

class UserCreate(BaseModel):
    """
    Input model for creating a new user.
    """
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    """
    Output model representing a user.
    """
    id: UUID
    name: str
    email: EmailStr

    class Config:
        from_attributes = True

# -------------------- Group Models --------------------

class GroupCreate(BaseModel):
    """
    Input model for creating a new group.
    """
    name: str

class GroupResponse(BaseModel):
    """
    Output model representing a group.
    """
    id: UUID
    name: str

    class Config:
        from_attributes = True

# -------------------- GroupMembers Models --------------------

class GroupMembersCreate(BaseModel):
    """
    Input model for adding a user to a group.
    """
    group_id: UUID
    user_id: UUID

class GroupMembersResponse(BaseModel):
    """
    Output model representing a group membership.
    """
    id: UUID
    group_id: UUID
    user_id: UUID

    class Config:
        from_attributes = True

# -------------------- Bill Models --------------------

class BillCreate(BaseModel):
    """
    Input model for creating a new bill.
    """
    group_id: UUID
    payer_id: Optional[UUID] = None
    uploaded_by: Optional[UUID] = None
    bill_date: date

class BillResponse(BaseModel):
    """
    Output model representing a bill.
    """
    id: UUID
    group_id: UUID
    payer_id: Optional[UUID] = None
    uploaded_by: Optional[UUID] = None
    bill_date: date
    created_at: datetime

    class Config:
        from_attributes = True

# -------------------- Item Models --------------------

class ItemCreate(BaseModel):
    """
    Input model for creating a new item on a bill.
    """
    bill_id: UUID
    name: str
    price: Decimal
    is_tax_or_tip: bool = False

class ItemResponse(BaseModel):
    """
    Output model representing an item on a bill.
    """
    id: UUID
    bill_id: UUID
    name: str
    price: float
    is_tax_or_tip: bool

    class Config:
        from_attributes = True

# -------------------- Vote Models --------------------

class VoteCreate(BaseModel):
    """
    Input model for voting on an item (whether a user consumed it).
    """
    item_id: UUID
    user_id: UUID
    ate: bool

class VoteResponse(BaseModel):
    """
    Output model representing a user's vote on an item.
    """
    id: UUID
    item_id: UUID
    user_id: UUID
    ate: bool

    class Config:
        from_attributes = True


# -------------------- Authentication Models --------------------

class GoogleAuthRequest(BaseModel):
    """
    Request model for Google ID token authentication.
    """
    id_token: str

class AuthResponse(BaseModel):
    """
    Response model for successful authentication.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]