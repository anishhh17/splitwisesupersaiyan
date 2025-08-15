#!/usr/bin/env python3
"""
Complete Test Suite Runner for Splitwise Super Saiyan

This script handles the complete testing workflow:
1. Sets up test data in the database
2. Runs all tests in the correct order
3. Provides comprehensive results
4. Optionally cleans up test data when done

Usage:
    python run_full_tests.py              # Run all tests with setup
    python run_full_tests.py --no-setup   # Run tests without data setup
    python run_full_tests.py --cleanup    # Clean up test data after tests
"""

import asyncio
import subprocess
import sys
import os
import argparse
import httpx
from pathlib import Path

def run_command(command, description, timeout=60):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print('='*60)
    
    try:
        if isinstance(command, list):
            result = subprocess.run(command, capture_output=False, text=True, timeout=timeout)
        else:
            result = subprocess.run(command, shell=True, capture_output=False, text=True, timeout=timeout)
        
        if result.returncode == 0:
            print(f"SUCCESS: {description}")
            return True
        else:
            print(f"FAILED: {description} (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {description} - after {timeout} seconds")
        return False
    except Exception as e:
        print(f"ERROR: {description} - {str(e)}")
        return False

def check_prerequisites():
    """Check that all prerequisites are met."""
    print("Checking Prerequisites")
    print("=" * 30)
    
    issues = []
    
    # Get the script directory and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level from scripts/
    
    # Change to project root if not already there
    if os.getcwd() != project_root:
        os.chdir(project_root)
        print(f"OK: Changed to project directory: {project_root}")
    
    # Check if we're in the correct directory
    if not os.path.exists("main.py"):
        issues.append("ERROR: Not in the correct directory (main.py not found)")
    else:
        print("OK: In correct directory")
    
    # Check for environment file
    if not os.path.exists(".env"):
        issues.append("WARNING: .env file not found - some tests may fail")
    else:
        print("OK: .env file found")
    
    # Check for required test files in new structure
    required_files = [
        "scripts/setup_test_data.py",
        "tests/test_config.py", 
        "tests/test_splitting_logic.py",
        "tests/test_full_integration.py"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            issues.append(f"ERROR: Required test file missing: {file}")
        else:
            print(f"OK: {file} found")
    
    return issues

async def check_server_status():
    """Check if the FastAPI server is running."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:8000/health")
            if resp.status_code == 200:
                return True
    except:
        pass
    return False

def setup_test_data():
    """Set up test data in the database."""
    print("\nSetting Up Test Data")
    print("=" * 30)
    
    # Check data status first
    status_success = run_command(
        [sys.executable, "scripts/setup_test_data.py", "--status"],
        "Checking test data status",
        timeout=30
    )
    
    if status_success:
        print("OK: Test data already exists and is ready")
        return True
    
    # Set up data
    setup_success = run_command(
        [sys.executable, "scripts/setup_test_data.py", "--setup"],
        "Creating test data in database",
        timeout=60
    )
    
    return setup_success

def cleanup_test_data():
    """Clean up test data from the database."""
    print("\nCleaning Up Test Data")
    print("=" * 30)
    
    cleanup_success = run_command(
        [sys.executable, "scripts/setup_test_data.py", "--cleanup"],
        "Removing test data from database",
        timeout=30
    )
    
    return cleanup_success

async def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run complete test suite for Splitwise Super Saiyan")
    parser.add_argument("--no-setup", action="store_true", help="Skip test data setup")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test data after tests")
    parser.add_argument("--keep-data", action="store_true", help="Keep test data after tests (default)")
    
    args = parser.parse_args()
    
    print("Splitwise Super Saiyan - Complete Test Suite")
    print("=" * 60)
    print("This will run comprehensive tests with real database data")
    print()
    
    # Check prerequisites
    issues = check_prerequisites()
    if issues:
        print("\nERROR: Prerequisites not met:")
        for issue in issues:
            print(f"   {issue}")
        print("\nPlease fix these issues and try again")
        sys.exit(1)
    
    print("OK: All prerequisites met")
    
    # Check if server is running
    server_running = await check_server_status()
    if not server_running:
        print("\nWARNING: FastAPI server is not running")
        print("TIP: Start the server with: uvicorn main:app --reload")
        print("   (Tests will fail without a running server)")
        
        response = input("\nDo you want to continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting...")
            sys.exit(1)
    else:
        print("\nSUCCESS: FastAPI server is running and responding")
    
    # Set up test data unless skipped
    if not args.no_setup:
        data_setup_success = setup_test_data()
        if not data_setup_success:
            print("\nERROR: Test data setup failed")
            print("TIP: Try running: python setup_test_data.py --setup")
            sys.exit(1)
    else:
        print("\nWARNING: Skipping test data setup (--no-setup flag)")
    
    # Run tests in order
    test_results = {}
    
    print(f"\n{'='*60}")
    print("TESTING: RUNNING TEST SUITE")
    print('='*60)
    
    # 1. Unit Tests (don't require server)
    print("\n[1] UNIT TESTS")
    print("-" * 20)
    unit_test_success = run_command(
        [sys.executable, "-m", "unittest", "tests.test_splitting_logic", "-v"],
        "Split calculation logic tests",
        timeout=30
    )
    test_results["Unit Tests"] = unit_test_success
    
    # 2. API Structure Tests (require server)
    print("\n[2] API STRUCTURE TESTS")
    print("-" * 30)
    structure_test_success = run_command(
        [sys.executable, "-m", "tests.test_api_structure"],
        "API endpoint structure validation",
        timeout=45
    )
    test_results["API Structure"] = structure_test_success
    
    # 3. Authentication Tests (require server)
    print("\n[3] AUTHENTICATION TESTS")
    print("-" * 30)
    auth_test_success = run_command(
        [sys.executable, "-m", "tests.test_new_auth_flow"],
        "Authentication flow validation",
        timeout=45
    )
    test_results["Authentication"] = auth_test_success
    
    # 4. Full Integration Tests (require server + data)
    print("\n[4] FULL INTEGRATION TESTS")
    print("-" * 35)
    integration_test_success = run_command(
        [sys.executable, "-m", "tests.test_full_integration"],
        "End-to-end workflow tests with real data",
        timeout=60
    )
    test_results["Full Integration"] = integration_test_success
    
    # 5. Gemini Tests (optional - require API key)
    print("\n[5] GEMINI AI TESTS (Optional)")
    print("-" * 35)
    gemini_test_success = run_command(
        [sys.executable, "-m", "tests.test_gemini_key"],
        "Gemini AI integration tests",
        timeout=45
    )
    test_results["Gemini AI"] = gemini_test_success
    
    # Clean up test data if requested
    if args.cleanup:
        cleanup_success = cleanup_test_data()
        if not cleanup_success:
            print("WARNING: Test data cleanup failed")
    elif not args.keep_data and not args.no_setup:
        # Ask user if they want to clean up
        print("\nCLEANUP: Test data cleanup:")
        response = input("Do you want to remove test data from the database? (y/N): ")
        if response.lower() == 'y':
            cleanup_test_data()
    
    # Print final results
    print(f"\n{'='*60}")
    print("RESULTS: FINAL TEST RESULTS")
    print('='*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results.items():
        status = "PASS" if success else "FAIL"
        print(f"{status:8} {test_name}")
        if success:
            passed += 1
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"\nSTATS: Overall Results: {passed}/{total} test suites passed ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("EXCELLENT: Your application is working perfectly!")
        print("READY: Ready for production deployment!")
    elif success_rate >= 75:
        print("GOOD: Most functionality is working correctly")
        print("REVIEW: Review failed tests for minor issues")
    elif success_rate >= 50:
        print("WARNING: MODERATE: Some significant issues need attention")
        print("FIX: Fix the failing tests before deployment")
    else:
        print("ERROR: NEEDS WORK: Multiple critical issues detected")
        print("WORK REQUIRED: Significant development work required")
    
    print(f"\n{'='*60}")
    print("TROUBLESHOOTING TIPS:")
    print("• Check .env file has correct environment variables")
    print("• Verify Supabase connection and credentials")
    print("• Ensure FastAPI server is running: uvicorn main:app --reload")
    print("• Check Gemini API key if AI tests fail")
    print("• Review server logs for detailed error information")
    print("• Run individual tests for more specific debugging")
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 75 else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSTOPPED: Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Test runner failed: {str(e)}")
        sys.exit(1)