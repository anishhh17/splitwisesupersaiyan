"""
Bill management routes.
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError
from uuid import UUID

from app.core.dependencies import get_current_user, get_database_service
from app.services.database import DatabaseService
from schemas import BillCreate, BillResponse, UserResponse
from app.utils.rate_limiter import rate_limit
from app.utils.split_calculator import SplitCalculator
from app.utils.image_processing import extract_items_from_receipt
from app.utils.file_validator import FileValidator

router = APIRouter(prefix="/bills", tags=["Bills"])


def parse_date(val):
    """Parse date string to datetime object."""
    if isinstance(val, str):
        s = val.replace('Z', '+00:00')
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    return val


def parse_date_only(val):
    """Parse date string to date object."""
    dt = parse_date(val)
    return dt.date() if dt else None


@router.post("", response_model=BillResponse)
@rate_limit(max_requests=30, window_seconds=3600, per="user")
async def create_bill(
    bill: BillCreate,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Create a new bill."""
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
        bill_data = await database.create_bill(data)
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
    except APIError as e:
        if getattr(e, "code", None) == "23505":
            raise HTTPException(status_code=409, detail="Bill with this ID already exists.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bill: {str(e)}")


@router.get("/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: str,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """Get bill by ID."""
    bill_data = await database.get_bill_by_id(bill_id)
    if not bill_data:
        raise HTTPException(status_code=404, detail="Bill not found")
    
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


@router.put("/{bill_id}")
async def update_bill(
    bill_id: str,
    request: dict,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Update bill details (like changing the payer).
    """
    try:
        update_data = {}
        
        if "payer_id" in request:
            update_data["payer_id"] = request["payer_id"]
        if "bill_date" in request:
            update_data["bill_date"] = request["bill_date"]
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        bill_data = await database.update_bill(bill_id, update_data)
        return JSONResponse(content={"status": "updated", "bill": bill_data})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update bill: {str(e)}")


@router.delete("/{bill_id}")
async def delete_bill(
    bill_id: str,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Delete a bill and all associated items/votes.
    """
    try:
        # Check if bill exists first
        bill_data = await database.get_bill_by_id(bill_id)
        if not bill_data:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        # Delete bill and all related data
        await database.delete_bill(bill_id)
        
        return JSONResponse(content={
            "status": "deleted", 
            "message": "Bill and all associated items and votes have been deleted",
            "bill_id": bill_id
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete bill: {str(e)}")


@router.get("/{bill_id}/items")
async def get_bill_items(
    bill_id: str,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Get all items for a bill with vote information.
    """
    try:
        items = await database.get_bill_items(bill_id)
        return JSONResponse(content={"items": items})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bill items: {str(e)}")


@router.get("/{bill_id}/split")
async def get_bill_split(
    bill_id: str,
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Calculate and return current split for a bill.
    """
    try:
        # Get bill details
        bill_data = await database.get_bill_by_id(bill_id)
        if not bill_data:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        # Get items for this bill
        items = await database.get_bill_items(bill_id)
        
        # Get votes for all items
        votes_by_item = {}
        for item in items:
            votes_by_item[item["id"]] = await database.get_item_votes(item["id"])
        
        # Calculate split
        calculator = SplitCalculator()
        split_result = calculator.calculate_bill_split(items, votes_by_item, bill_data["payer_id"])
        
        # Format response to match test expectations
        response = {
            "splits": split_result["totals"],
            "payer_id": split_result["payer_id"]
        }
        
        return JSONResponse(content=response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate split: {str(e)}")


@router.post("/process-image")
@rate_limit(max_requests=5, window_seconds=60, per="user")
async def process_bill_image(
    file: UploadFile = File(...),
    group_id: str = Form(...),
    uploaded_by: str = Form(None),
    current_user: UserResponse = Depends(get_current_user),
    database: DatabaseService = Depends(get_database_service)
):
    """
    Accepts a bill image, extracts items, creates bill and items in DB, and returns the created bill and items.
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
        bill_response = await database.create_bill(bill_data)

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
        
        items_response = await database.create_items_bulk(items_to_insert)

        return JSONResponse(content={
            "bill": bill_response,
            "items": items_response,
            "extracted": result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")