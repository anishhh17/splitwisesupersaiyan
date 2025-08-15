"""
Splitwise Super Saiyan - Main FastAPI Application

A clean, modular FastAPI application for splitting bills with friends.
Features client-side Google OAuth, Gemini AI receipt processing, and comprehensive bill management.
"""

from fastapi import FastAPI

from app.core.config import settings
from app.routers import auth, health, users, groups, bills, items, votes

# Initialize the FastAPI app
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION
)

# Include all routers
app.include_router(health.router)  # Health check routes (no prefix)
app.include_router(auth.router)    # Authentication routes (/auth)
app.include_router(users.router)   # User management routes (/users)
app.include_router(groups.router)  # Group management routes (/groups)
app.include_router(bills.router)   # Bill management routes (/bills)
app.include_router(items.router)   # Item management routes (/items)
app.include_router(votes.router)   # Vote management routes (/votes)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Splitwise Super Saiyan API",
        "version": "2.0.0",
        "architecture": "modular",
        "features": [
            "Client-side Google OAuth",
            "Gemini AI receipt processing",
            "Bill splitting calculations",
            "Group and user management",
            "Rate limiting",
            "File validation"
        ],
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)