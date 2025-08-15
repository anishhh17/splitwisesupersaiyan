"""
Health check and utility routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from postgrest.exceptions import APIError

from app.services.database import DatabaseService, db_service

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify server is running.
    """
    return {"status": "ok"}


@router.get("/test-supabase", summary="Test Supabase connection", tags=["Test"])
async def test_supabase(database: DatabaseService = Depends(lambda: db_service)):
    """
    Test the Supabase database connection.
    """
    try:
        resp = await run_in_threadpool(lambda: database.client.table("users").select("*").limit(1).execute())
    except APIError as e:
        if getattr(e, 'code', None) == '23505':
            raise HTTPException(status_code=409, detail="Resource already exists") from e
        raise HTTPException(status_code=500, detail=f"Unexpected Supabase error: {str(e)}") from e
    
    if getattr(resp, "error", None):
        return JSONResponse(status_code=500, content={"success": False, "data": None, "error": resp.error.message})
    
    return {"success": True, "data": resp.data}