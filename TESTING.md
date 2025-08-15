# Testing Guide for Splitwise Super Saiyan

This comprehensive guide explains how to run and understand the complete test suite for the Splitwise Super Saiyan API.

## 🚀 Quick Start

**Run all tests with real data:**
```bash
# From backend directory
python scripts/run_full_tests.py

# Or from project root (Windows)
splitwisesupersaiyan/venv/Scripts/python.exe splitwisesupersaiyan/scripts/run_full_tests.py
```

This will automatically:
1. ✅ Set up test data in your Supabase database
2. 🧪 Run all test suites in correct order
3. 📊 Provide comprehensive results with statistics
4. 🧹 Optionally clean up test data when finished

## 📁 Test Structure Overview

### **New Organized Structure**
```
tests/                              # All test files centralized
├── archive/                        # Legacy test files (pre-refactoring)
│   ├── test_api.py                # Old API tests
│   ├── test_auth.py               # Old auth tests
│   └── test_*.py                  # Other archived tests
├── test_api_structure.py           # API endpoint validation
├── test_new_auth_flow.py           # Authentication flow tests
├── test_full_integration.py        # End-to-end integration tests
├── test_gemini_key.py              # AI integration tests
├── test_splitting_logic.py         # Unit tests for calculations
└── test_config.py                  # Shared test configuration

scripts/                            # Test utilities and runners
├── run_full_tests.py               # Comprehensive test runner
├── setup_test_data.py              # Test data management
├── run_tests.py                    # Legacy simple runner
└── verify_split.py                 # Split verification utility

assets/                             # Test assets
├── test_bill.jpg                   # Sample receipt image
└── test_receipt.png                # Generated test receipt
```

### **Core Test Files**
- **`tests/test_splitting_logic.py`** - Unit tests for bill calculation algorithms
- **`tests/test_api_structure.py`** - Validates all 33 API endpoints
- **`tests/test_new_auth_flow.py`** - Tests client-side OAuth + JWT flow
- **`tests/test_full_integration.py`** - End-to-end workflows with real data
- **`tests/test_gemini_key.py`** - AI integration and image processing tests

### **Support Files**
- **`scripts/setup_test_data.py`** - Creates/manages realistic test data
- **`tests/test_config.py`** - Shared configuration and test utilities
- **`scripts/run_full_tests.py`** - Orchestrates complete testing workflow

## 🛠️ Prerequisites

### **1. Environment Setup**
```bash
# Navigate to backend directory
cd splitwisesupersaiyan

# Activate virtual environment
venv\Scripts\activate     # Windows
# OR
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### **2. Environment Variables**
Create `.env` file with:
```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Google OAuth Configuration  
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key

# Environment
ENVIRONMENT=development
```

### **3. FastAPI Server**
```bash
# Start the development server
uvicorn main:app --reload
```
Server should be running at `http://localhost:8000`

## 🧪 Running Tests

### **Option 1: Complete Test Suite (Recommended)**
```bash
# Comprehensive test run with all features
python scripts/run_full_tests.py

# With options
python scripts/run_full_tests.py --cleanup      # Clean up after tests
python scripts/run_full_tests.py --no-setup    # Skip test data setup  
python scripts/run_full_tests.py --keep-data   # Keep test data (default)
```

**What this does:**
- ✅ Validates prerequisites and environment
- ✅ Checks server connectivity
- ✅ Sets up realistic test data in database
- ✅ Runs all 5 test suites in correct order
- ✅ Provides detailed results and statistics
- ✅ Offers cleanup options

### **Option 2: Individual Test Types**

**Unit Tests (No server required):**
```bash
python -m unittest tests.test_splitting_logic -v
```
- Tests bill splitting calculations
- Validates precision and rounding
- Checks edge cases and complex scenarios

**API Structure Tests:**
```bash
python -m tests.test_api_structure
```
- Validates all 33 API endpoints
- Checks authentication requirements
- Tests response formats

**Authentication Tests:**
```bash
python -m tests.test_new_auth_flow
```
- Tests JWT token creation/validation
- Simulates Google OAuth flow
- Validates protected endpoint security

**Full Integration Tests:**
```bash
# Setup test data first
python scripts/setup_test_data.py --setup

# Run integration tests
python -m tests.test_full_integration
```
- End-to-end workflows with real data
- User, group, and bill operations
- Complete bill splitting scenarios

**AI Integration Tests:**
```bash
python -m tests.test_gemini_key
```
- Tests Gemini AI receipt processing
- Validates image processing pipeline
- Checks JSON response formatting

## 🗄️ Test Data Management

The test suite uses **real data** in your Supabase database to enable comprehensive testing.

### **Setup Test Data**
```bash
python scripts/setup_test_data.py --setup
```

**Creates:**
- **5 test users**: admin, alice, bob, charlie, diana
- **3 test groups**: "Pizza Night", "Roommates", "Weekend Trip" 
- **3 test bills**: Pizza receipt, grocery bill, restaurant tab
- **Realistic voting patterns**: Users vote for items they consumed
- **Fixed UUIDs**: Predictable IDs starting with `550e8400`, `660e8400`, etc.

### **Check Test Data Status**
```bash
python scripts/setup_test_data.py --status
```

### **Clean Up Test Data**
```bash
python scripts/setup_test_data.py --cleanup
```

**⚠️ Important Notes:**
- Test data uses **fixed UUIDs** for predictable, repeatable tests
- Data is **isolated** from production data (different UUID ranges)
- **Safe to run** multiple times - idempotent operations
- **Realistic scenarios** mirror actual application usage

## 📊 Test Coverage & Results

### **Expected Test Results**

**🎯 Perfect Scenario (100% Success):**
```
============================================================
RESULTS: FINAL TEST RESULTS
============================================================
PASS     Unit Tests              (8/8 tests)
PASS     API Structure           (33 endpoints verified)
PASS     Authentication          (All flows working)
PASS     Full Integration        (14/14 scenarios)
PASS     Gemini AI              (Image processing working)

STATS: Overall Results: 5/5 test suites passed (100.0%)
🎉 EXCELLENT: Your application is working perfectly!
🚀 READY: Ready for production deployment!
```

**📈 Typical Real-World Results:**
- **Unit Tests**: 100% (should always pass)
- **API Structure**: 85-95% (some endpoints may show 403 without auth)
- **Authentication**: 90-100% (depends on database connectivity)
- **Full Integration**: 95-100% (with proper test data)
- **Gemini AI**: 100% or 0% (depends on valid API key)

### **Detailed Test Coverage**

**Unit Tests (8 tests):**
- ✅ Even amount splitting calculations
- ✅ Uneven amount splitting with proper cent distribution
- ✅ Small amount handling (penny-level precision)
- ✅ Edge cases (zero amounts, single person, invalid inputs)
- ✅ Complex bill scenarios with multiple users
- ✅ Mario's Pizza receipt scenario (real-world test)
- ✅ Precision and rounding validation
- ✅ No-eaters scenario handling

**API Structure Tests (33 endpoints):**
- ✅ All endpoint registration verification
- ✅ Authentication requirement validation
- ✅ HTTP method and path verification
- ✅ Response format checking
- ✅ Error handling validation
- ✅ Documentation endpoint availability

**Authentication Flow Tests:**
- ✅ JWT token creation and validation
- ✅ Google OAuth flow simulation
- ✅ Protected endpoint access control
- ✅ Token expiration handling
- ✅ Invalid token rejection
- ✅ User authentication state management

**Integration Tests (14 scenarios):**
- ✅ User profile operations
- ✅ User search functionality
- ✅ Group management workflows
- ✅ Group membership operations
- ✅ Bill creation and retrieval
- ✅ Bill split calculations
- ✅ Item management and voting
- ✅ Authentication edge cases
- ✅ Token refresh mechanisms
- ✅ Error handling scenarios

## 🐛 Troubleshooting Guide

### **Common Issues & Solutions**

**🔴 Server Connection Issues**
```
❌ ERROR: Server is not running or not accessible
💡 Solution: uvicorn main:app --reload
```

**🔴 Database Connection Problems**
```
❌ ERROR: Supabase connection failed  
💡 Check: SUPABASE_URL and SUPABASE_KEY in .env file
💡 Verify: Network connectivity to Supabase
```

**🔴 Missing Test Data**
```
❌ WARNING: Test data is incomplete
💡 Run: python scripts/setup_test_data.py --setup
💡 Check: Database permissions and connectivity
```

**🔴 Authentication Failures**
```
❌ ERROR: User not found / Token verification failed
💡 Ensure: Test data is properly set up
💡 Check: JWT_SECRET_KEY in environment variables
```

**🔴 Module Import Errors**
```
❌ ERROR: ModuleNotFoundError: No module named 'httpx'
💡 Activate: Virtual environment (venv\Scripts\activate)
💡 Install: pip install -r requirements.txt
```

**🔴 Gemini AI Failures**
```
❌ ERROR: No GEMINI_API_KEY found
💡 Add: Valid Gemini API key to .env file
💡 Note: This test is optional and won't affect overall grade
```

**🔴 File Path Issues (Windows)**
```
❌ ERROR: File not found errors
💡 Use: Forward slashes in paths (/)
💡 Run: From correct directory (splitwisesupersaiyan/)
```

### **Debugging Steps**

1. **Check Prerequisites:**
   ```bash
   # Verify you're in correct directory
   ls main.py  # Should exist
   
   # Check environment file
   ls .env     # Should exist
   
   # Verify virtual environment
   which python  # Should point to venv/Scripts/python
   ```

2. **Test Database Connection:**
   ```bash
   python scripts/setup_test_data.py --status
   ```

3. **Verify Server:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "healthy"}
   ```

4. **Run Individual Tests:**
   ```bash
   # Start with unit tests (no dependencies)
   python -m unittest tests.test_splitting_logic -v
   
   # Then try API tests
   python -m tests.test_api_structure
   ```

## 🔧 Advanced Usage

### **Custom Test Scenarios**
```bash
# Run without automatic data setup
python scripts/run_full_tests.py --no-setup

# Clean up test data after completion
python scripts/run_full_tests.py --cleanup

# Keep test data for debugging
python scripts/run_full_tests.py --keep-data
```

### **Test Data Inspection**
```bash
# Check what test data exists
python scripts/setup_test_data.py --status

# View test configuration
python -c "from tests.test_config import *; print('Test users:', TEST_USERS)"
```

### **Manual Test Data Creation**
```python
from tests.test_config import *

# Generate JWT token for specific user
token, user_id = generate_test_jwt_token("alice")
print(f"Token for Alice: {token}")

# Use test user IDs
alice_id = TEST_USERS["alice"]["id"]
```

## 📈 Continuous Integration

### **CI/CD Pipeline Setup**
```bash
# Setup phase
python scripts/setup_test_data.py --setup

# Test phase  
python scripts/run_full_tests.py --no-setup --cleanup

# Exit codes:
# 0 = Success (75%+ tests passed)
# 1 = Failure (< 75% tests passed)
```

### **Docker Integration**
```dockerfile
# In your Dockerfile
RUN python scripts/setup_test_data.py --setup
RUN python scripts/run_full_tests.py --no-setup
```

## 🎯 Best Practices

### **Development Workflow**
1. **Start with unit tests** - Fast feedback on logic changes
2. **Use integration tests** for feature validation
3. **Run full suite** before committing changes
4. **Keep test data** during development sessions
5. **Clean up** when switching between features

### **Test Data Management**
- **Setup once** per development session
- **Check status** before running integration tests
- **Clean up** when switching projects or branches
- **Regenerate** if database schema changes

### **Debugging Failed Tests**
1. **Check server logs** for detailed error information
2. **Run individual tests** to isolate issues
3. **Verify test data** is properly set up
4. **Check environment variables** are correct
5. **Review network connectivity** to external services

---

## 📞 Getting Help

**Test-specific issues:**
- Review individual test file comments for guidance
- Check the troubleshooting section above
- Verify all prerequisites are met

**Environment issues:**
- Ensure virtual environment is activated
- Verify all dependencies are installed
- Check .env file configuration

**Database issues:**
- Verify Supabase credentials and connectivity
- Check database permissions
- Try recreating test data

**Need more help?** Check the main [README.md](README.md) for additional setup guidance and architecture information.