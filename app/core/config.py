"""
Configuration settings for the Splitwise Super Saiyan application.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
if os.getenv("ENVIRONMENT") != "production":
    load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # Gemini AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 3600  # 1 hour
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # FastAPI Configuration
    APP_TITLE: str = "Splitwise Super Saiyan"
    APP_DESCRIPTION: str = "A FastAPI app for splitting bills with friends"
    
    def validate_required_settings(self) -> None:
        """Validate that all required environment variables are set."""
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")
            
        if not self.GOOGLE_CLIENT_ID or not self.GOOGLE_CLIENT_SECRET:
            raise RuntimeError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in the environment.")

        if not self.JWT_SECRET_KEY:
            raise RuntimeError("JWT_SECRET_KEY must be set in the environment.")


# Global settings instance
settings = Settings()

# Validate settings on import
settings.validate_required_settings()