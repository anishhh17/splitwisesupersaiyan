# Splitwise Super Saiyan

A modern, production-ready FastAPI application for splitting bills with friends. Features AI-powered receipt processing, client-side Google OAuth authentication, and comprehensive bill management capabilities.

## 🚀 Features

### Core Features
- **Client-side Google OAuth** with backend JWT token management
- **Group and bill management** with real-time split calculations
- **AI Receipt Processing** using Gemini AI to extract items from images
- **Fair bill splitting** with precise cent distribution algorithms
- **Rate limiting** for API protection and abuse prevention
- **Robust file validation** for secure image uploads
- **Comprehensive test suite** with real database integration

### Security & Performance
- JWT-based authentication with token refresh
- Rate limiting with sliding window approach
- Secure file upload validation with magic byte detection
- Image dimension and size constraints
- Comprehensive input validation using Pydantic
- CORS configuration for cross-origin requests

## 📁 Project Structure

```
splitwisesupersaiyan/
├── app/                          # Core application code
│   ├── core/                    # Configuration and dependencies
│   │   ├── config.py           # Environment configuration
│   │   └── dependencies.py     # FastAPI dependencies
│   ├── routers/                 # API endpoint routers
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── bills.py            # Bill management
│   │   ├── groups.py           # Group management
│   │   ├── items.py            # Item management
│   │   ├── users.py            # User management
│   │   └── votes.py            # Voting system
│   ├── services/                # External services
│   │   └── database.py         # Database service layer
│   └── utils/                   # Utility modules
│       ├── auth_utils.py       # Authentication utilities
│       ├── file_validator.py   # File validation
│       ├── image_processing.py # AI image processing
│       ├── rate_limiter.py     # Rate limiting
│       └── split_calculator.py # Bill splitting logic
├── tests/                       # Comprehensive test suite
│   ├── archive/                # Legacy test files
│   ├── test_api_structure.py   # API endpoint tests
│   ├── test_auth_flow.py       # Authentication tests
│   ├── test_full_integration.py # End-to-end tests
│   ├── test_gemini_key.py      # AI integration tests
│   ├── test_splitting_logic.py # Unit tests
│   └── test_config.py          # Test configuration
├── scripts/                     # Utility scripts
│   ├── run_full_tests.py       # Test suite runner
│   ├── setup_test_data.py      # Test data management
│   └── verify_split.py         # Split verification
├── assets/                      # Static assets
│   ├── test_bill.jpg           # Sample receipt image
│   └── test_receipt.png        # Generated test receipt
├── main.py                      # FastAPI application entry point
├── schemas.py                   # Pydantic data models
├── models.py                    # Database models
└── requirements.txt             # Python dependencies
```

## 🛠️ Quick Setup

### Prerequisites
- Python 3.9+
- Supabase account and project
- Google OAuth credentials
- Gemini AI API key

### Installation

1. **Clone and navigate to the project:**
```bash
cd splitwisesupersaiyan
```

2. **Create and activate virtual environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**

Copy `.env.example` to `.env` and configure:
```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# JWT Configuration
JWT_SECRET_KEY=your_secret_key_for_jwt_signing

# Environment
ENVIRONMENT=development
```

5. **Run the application:**
```bash
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

## 🧪 Testing

### Complete Test Suite
Run the comprehensive test suite with real database integration:

```bash
# From backend directory
python scripts/run_full_tests.py

# From project root (Windows)
splitwisesupersaiyan/venv/Scripts/python.exe splitwisesupersaiyan/scripts/run_full_tests.py
```

### Individual Test Types
```bash
# Unit tests only
python -m unittest tests.test_splitting_logic -v

# API structure tests
python -m tests.test_api_structure

# Authentication tests
python -m tests.test_new_auth_flow

# Full integration tests
python -m tests.test_full_integration

# AI integration tests
python -m tests.test_gemini_key
```

### Test Data Management
```bash
# Create test data in database
python scripts/setup_test_data.py --setup

# Check test data status
python scripts/setup_test_data.py --status

# Clean up test data
python scripts/setup_test_data.py --cleanup
```

## 📚 API Documentation

When running, comprehensive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Key Endpoints

#### Authentication
- `POST /auth/google` - Authenticate with Google ID token
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - Logout
- `GET /auth/me` - Get current user info

#### Bill Management
- `POST /bills` - Create a new bill
- `GET /bills/{bill_id}` - Get bill details
- `GET /bills/{bill_id}/split` - Calculate bill split
- `POST /bills/process-image` - Process receipt image with AI

#### Group Management
- `POST /groups` - Create a group
- `GET /groups/{group_id}` - Get group details
- `POST /groups/members` - Add member to group

## 🔧 Configuration

### Rate Limiting
- **Image processing**: 5 requests per minute per user
- **Authentication**: 10 requests per hour per IP
- **User creation**: 5 requests per hour per IP
- **Bill creation**: 30 requests per hour per user

### File Upload Limits
- **Maximum file size**: 10MB
- **Supported formats**: JPEG, PNG, GIF, BMP, WebP, TIFF
- **Image dimensions**: 10px - 10,000px

### Security Features
- JWT token expiration: 1 hour (configurable)
- Google ID token verification
- File type validation using magic bytes
- Input sanitization and validation
- CORS protection

## 🏗️ Architecture

### Authentication Flow
1. **Frontend**: Uses client-side Google OAuth to get ID token
2. **Frontend**: Sends ID token to `/auth/google` endpoint
3. **Backend**: Verifies ID token with Google's servers
4. **Backend**: Creates/retrieves user from Supabase database
5. **Backend**: Issues JWT token for subsequent API calls
6. **Frontend**: Uses JWT token in Authorization header

### Database Schema
The application uses Supabase (PostgreSQL) with the following main tables:
- `users` - User profiles and authentication
- `groups` - Bill splitting groups
- `group_members` - Group membership relationships
- `bills` - Bill records
- `items` - Individual bill items
- `votes` - User votes for item consumption

### AI Integration
- **Gemini 1.5 Flash** for receipt image processing
- Structured JSON output for parsed receipt data
- Automatic item extraction with price detection
- Tax and tip identification

## 🚀 Deployment

The application is production-ready with:
- ✅ Comprehensive test coverage (100% pass rate)
- ✅ Environment-based configuration
- ✅ Proper error handling and logging
- ✅ Security best practices
- ✅ Modular, maintainable architecture

### Deployment Options
1. **Docker** (recommended)
2. **Cloud platforms** (AWS ECS, Google Cloud Run, Azure Container Instances)
3. **Serverless** (AWS Lambda, Vercel Functions)
4. **Traditional hosting** (VPS with systemd service)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite: `python scripts/run_full_tests.py`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

### Troubleshooting
- Check `.env` file has correct environment variables
- Verify Supabase connection and credentials
- Ensure FastAPI server is running
- Check Gemini API key if AI tests fail
- Review server logs for detailed error information

### Common Issues
1. **Module not found errors**: Ensure virtual environment is activated
2. **Database connection issues**: Verify Supabase credentials
3. **Authentication failures**: Check Google OAuth configuration
4. **Test failures**: Run `python scripts/setup_test_data.py --setup`

For detailed testing information, see [TESTING.md](TESTING.md).