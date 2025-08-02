# Splitwise Super Saiyan

A FastAPI application for splitting bills with friends, with image processing capabilities to extract items from receipts.

## Features

- User authentication with Google OAuth
- Group and bill management
- Receipt image processing using Gemini AI
- Fair bill splitting calculations
- Rate limiting for API protection
- Robust file validation for image uploads

## Components

### File Validation

The application includes a robust `FileValidator` class that:

- Validates image file types using both MIME type detection and file extensions
- Checks file size limits (default 10MB)
- Verifies image dimensions 
- Detects file formats using magic bytes
- Prevents common file upload vulnerabilities

### Rate Limiting

API endpoints are protected by rate limiting to prevent abuse:

- Image processing: 5 requests per minute per user
- Authentication: 10 requests per hour per IP address
- User creation: 5 requests per hour per IP address
- Bill creation: 30 requests per hour per user

The rate limiter uses a sliding window approach and can be configured per endpoint.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in a `.env` file:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=your_jwt_secret
```

3. Run the application:
```bash
uvicorn main:app --reload
```

## API Documentation

When the application is running, API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
