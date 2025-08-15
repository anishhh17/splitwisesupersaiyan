#!/usr/bin/env python3
"""
Test runner for the Splitwise Super Saiyan API.
Runs all available tests in the correct order.
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path

def run_python_script(script_name):
    """Run a Python script and return success status."""
    print(f"\n{'='*60}")
    print(f"TESTING Running {script_name}")
    print('='*60)
    
    try:
        # Run the script
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, 
                              text=True, 
                              timeout=60)
        
        if result.returncode == 0:
            print(f"SUCCESS {script_name} completed successfully")
            return True
        else:
            print(f"WARNING {script_name} completed with issues (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT {script_name} timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"ERROR {script_name} failed with error: {str(e)}")
        return False

def run_unit_tests():
    """Run unit tests using unittest."""
    print(f"\n{'='*60}")
    print("TESTING Running Unit Tests (test_splitting_logic.py)")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, "-m", "unittest", "test_splitting_logic"], 
                              capture_output=False, 
                              text=True, 
                              timeout=30)
        
        if result.returncode == 0:
            print("SUCCESS Unit tests completed successfully")
            return True
        else:
            print(f"WARNING Unit tests completed with issues (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print("TIMEOUT Unit tests timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"ERROR Unit tests failed with error: {str(e)}")
        return False

def check_server_running():
    """Check if the FastAPI server is running."""
    import httpx
    
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get("http://localhost:8000/health")
            if resp.status_code == 200:
                return True
    except:
        pass
    return False

def main():
    """Run all tests."""
    print("LAUNCHING Splitwise Super Saiyan Test Suite")
    print("=" * 60)
    print("TESTING Running comprehensive tests for the modular FastAPI application")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("ERROR: Please run this script from the splitwisesupersaiyan directory")
        print("   Expected files: main.py, test_*.py")
        sys.exit(1)
    
    # Check if server is running
    if not check_server_running():
        print("WARNING: FastAPI server doesn't seem to be running")
        print("TIP Start the server with: uvicorn main:app --reload")
        print("   (Some tests will fail without a running server)")
        print()
    else:
        print("SUCCESS FastAPI server is running and responding")
        print()
    
    # List of tests to run
    tests = [
        # Unit tests first (don't require server)
        ("unit_tests", "Split calculation logic"),
        
        # Gemini integration test (doesn't require server)
        ("test_gemini_key.py", "Gemini AI integration"),
        
        # API structure tests (require server)
        ("test_api_structure.py", "API endpoint structure"),
        
        # Authentication tests (require server)
        ("test_new_auth_flow.py", "New authentication flow"),
        
        # Integration tests (require server)
        ("test_api_integration.py", "API integration workflows"),
    ]
    
    results = {}
    
    for test_name, description in tests:
        print(f"\nNEXT: {description}")
        input("Press Enter to continue (or Ctrl+C to exit)...")
        
        if test_name == "unit_tests":
            success = run_unit_tests()
        else:
            success = run_python_script(test_name)
        
        results[test_name] = success
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY TEST SUMMARY")
    print('='*60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nRESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS All tests passed! Your application is working correctly.")
    elif passed >= total * 0.7:
        print("WARNING Most tests passed. Check the failed tests for issues.")
    else:
        print("ERROR Many tests failed. Review your application setup.")
    
    print(f"\n{'='*60}")
    print("TROUBLESHOOTING Tips:")
    print("• Make sure the FastAPI server is running: uvicorn main:app --reload")
    print("• Check your .env file has the correct environment variables")
    print("• Verify Supabase connection if database tests fail")
    print("• Check Gemini API key if OCR tests fail")
    print("• Review logs above for specific error details")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSTOPPED Tests interrupted by user")
    except Exception as e:
        print(f"\nERROR Test runner failed: {str(e)}")
        sys.exit(1)