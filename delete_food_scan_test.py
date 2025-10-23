#!/usr/bin/env python3
"""
FitFlow DELETE Food Scan Endpoint Testing Suite
Tests the new DELETE /api/food/scan/{scan_id} endpoint with comprehensive scenarios
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://verify-email-signup.preview.emergentagent.com/api"
TEST_USER_EMAIL = "test@fitflow.com"
TEST_USER_PASSWORD = "Test123!"

# Global variables for test state
auth_token = None
user_id = None
test_results = {}
created_scan_ids = []

def log_test(test_name, success, message="", details=None):
    """Log test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}: {message}")
    if details:
        print(f"   Details: {details}")
    
    test_results[test_name] = {
        "success": success,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }

def test_login():
    """Test user login to get authentication token"""
    global auth_token, user_id
    
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("token")
            user_id = data.get("user", {}).get("user_id")
            
            if auth_token and user_id:
                log_test("User Login", True, "Login successful, token received")
                return True
            else:
                log_test("User Login", False, "Missing token or user_id in response")
                return False
        elif response.status_code == 401:
            # Try to register the user first
            print("🔄 User not found, attempting registration...")
            return test_register_and_login()
        else:
            log_test("User Login", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("User Login", False, f"Error: {str(e)}")
        return False

def test_register_and_login():
    """Register user and then login"""
    global auth_token, user_id
    
    # Try to register first
    user_data = {
        "name": "Test User",
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "age": 30,
        "gender": "male",
        "height": 175.0,
        "weight": 70.0,
        "activity_level": "moderate",
        "goal_weight": 68.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("token")
            user_id = data.get("user", {}).get("user_id")
            
            if auth_token and user_id:
                log_test("User Login", True, "User registered and logged in successfully")
                return True
            else:
                log_test("User Login", False, "Missing token or user_id in registration response")
                return False
        elif response.status_code == 400 and "already registered" in response.text:
            # User exists but login failed - password might be wrong
            log_test("User Login", False, "User exists but login failed - check credentials")
            return False
        else:
            log_test("User Login", False, 
                    f"Registration failed - Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("User Login", False, f"Registration error: {str(e)}")
        return False

def create_test_food_scan():
    """Create a test food scan to use for deletion testing"""
    if not auth_token:
        return None
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Simple 1x1 red pixel PNG image for testing
    simple_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    form_data = {"image": simple_png}
    
    try:
        print("🔍 Creating test food scan...")
        response = requests.post(f"{BASE_URL}/food/scan", 
                               headers=headers, data=form_data, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            scan_id = data.get("scan_id")
            if scan_id:
                created_scan_ids.append(scan_id)
                print(f"✅ Created test food scan: {scan_id}")
                return scan_id
        
        print(f"❌ Failed to create test food scan: {response.status_code}")
        return None
            
    except Exception as e:
        print(f"❌ Error creating test food scan: {str(e)}")
        return None

def test_get_food_history():
    """Test getting food scan history to find existing scan_ids"""
    if not auth_token:
        log_test("Get Food History", False, "No auth token available")
        return False, []
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/food/history", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            history = data.get("history", [])
            scan_ids = [scan["scan_id"] for scan in history]
            
            log_test("Get Food History", True, 
                    f"Retrieved {len(history)} food scan records with {len(scan_ids)} scan IDs")
            return True, scan_ids
        else:
            log_test("Get Food History", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False, []
            
    except Exception as e:
        log_test("Get Food History", False, f"Error: {str(e)}")
        return False, []

def test_delete_food_scan_success():
    """Test successful deletion of a food scan"""
    if not auth_token:
        log_test("Delete Food Scan - Success", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # First, get existing scans or create one
    success, existing_scan_ids = test_get_food_history()
    if not success:
        return False
    
    # If no existing scans, create one
    if not existing_scan_ids:
        scan_id = create_test_food_scan()
        if not scan_id:
            log_test("Delete Food Scan - Success", False, "Could not create test scan for deletion")
            return False
    else:
        scan_id = existing_scan_ids[0]  # Use the first existing scan
    
    try:
        # Test successful deletion
        response = requests.delete(f"{BASE_URL}/food/scan/{scan_id}", 
                                 headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            expected_message = "Food scan deleted successfully"
            
            if data.get("message") == expected_message:
                log_test("Delete Food Scan - Success", True, 
                        f"Successfully deleted scan {scan_id[:8]}... with correct message")
                return True
            else:
                log_test("Delete Food Scan - Success", False, 
                        f"Unexpected message: {data.get('message')}")
                return False
        else:
            log_test("Delete Food Scan - Success", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Delete Food Scan - Success", False, f"Error: {str(e)}")
        return False

def test_verify_deletion_from_history():
    """Test that deleted scan is removed from food history"""
    if not auth_token:
        log_test("Verify Deletion from History", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create a new scan specifically for this test
    scan_id = create_test_food_scan()
    if not scan_id:
        log_test("Verify Deletion from History", False, "Could not create test scan")
        return False
    
    try:
        # Get history before deletion
        response = requests.get(f"{BASE_URL}/food/history", headers=headers, timeout=10)
        if response.status_code != 200:
            log_test("Verify Deletion from History", False, "Could not get initial history")
            return False
        
        before_data = response.json()
        before_history = before_data.get("history", [])
        before_scan_ids = [scan["scan_id"] for scan in before_history]
        
        # Verify our scan is in the history
        if scan_id not in before_scan_ids:
            log_test("Verify Deletion from History", False, 
                    f"Test scan {scan_id} not found in history before deletion")
            return False
        
        # Delete the scan
        delete_response = requests.delete(f"{BASE_URL}/food/scan/{scan_id}", 
                                        headers=headers, timeout=10)
        
        if delete_response.status_code != 200:
            log_test("Verify Deletion from History", False, 
                    f"Deletion failed: {delete_response.status_code}")
            return False
        
        # Get history after deletion
        response = requests.get(f"{BASE_URL}/food/history", headers=headers, timeout=10)
        if response.status_code != 200:
            log_test("Verify Deletion from History", False, "Could not get history after deletion")
            return False
        
        after_data = response.json()
        after_history = after_data.get("history", [])
        after_scan_ids = [scan["scan_id"] for scan in after_history]
        
        # Verify our scan is no longer in the history
        if scan_id in after_scan_ids:
            log_test("Verify Deletion from History", False, 
                    f"Deleted scan {scan_id} still appears in history")
            return False
        
        # Verify history count decreased by 1
        if len(after_history) != len(before_history) - 1:
            log_test("Verify Deletion from History", False, 
                    f"History count mismatch. Before: {len(before_history)}, After: {len(after_history)}")
            return False
        
        log_test("Verify Deletion from History", True, 
                f"Scan {scan_id[:8]}... successfully removed from history (count: {len(before_history)} → {len(after_history)})")
        return True
        
    except Exception as e:
        log_test("Verify Deletion from History", False, f"Error: {str(e)}")
        return False

def test_delete_same_scan_twice():
    """Test edge case: Try to delete the same scan_id again (should return 404)"""
    if not auth_token:
        log_test("Delete Same Scan Twice", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create a new scan for this test
    scan_id = create_test_food_scan()
    if not scan_id:
        log_test("Delete Same Scan Twice", False, "Could not create test scan")
        return False
    
    try:
        # First deletion (should succeed)
        response1 = requests.delete(f"{BASE_URL}/food/scan/{scan_id}", 
                                  headers=headers, timeout=10)
        
        if response1.status_code != 200:
            log_test("Delete Same Scan Twice", False, 
                    f"First deletion failed: {response1.status_code}")
            return False
        
        # Second deletion (should return 404)
        response2 = requests.delete(f"{BASE_URL}/food/scan/{scan_id}", 
                                  headers=headers, timeout=10)
        
        if response2.status_code == 404:
            log_test("Delete Same Scan Twice", True, 
                    f"Second deletion correctly returned 404 for already deleted scan {scan_id[:8]}...")
            return True
        else:
            log_test("Delete Same Scan Twice", False, 
                    f"Expected 404 for second deletion, got {response2.status_code}")
            return False
            
    except Exception as e:
        log_test("Delete Same Scan Twice", False, f"Error: {str(e)}")
        return False

def test_delete_invalid_scan_id():
    """Test edge case: Try to delete with invalid scan_id (should return 404)"""
    if not auth_token:
        log_test("Delete Invalid Scan ID", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test with completely invalid scan_id
        invalid_scan_id = "invalid-scan-id-12345"
        response = requests.delete(f"{BASE_URL}/food/scan/{invalid_scan_id}", 
                                 headers=headers, timeout=10)
        
        if response.status_code == 404:
            log_test("Delete Invalid Scan ID", True, 
                    f"Correctly returned 404 for invalid scan_id: {invalid_scan_id}")
            return True
        else:
            log_test("Delete Invalid Scan ID", False, 
                    f"Expected 404 for invalid scan_id, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Delete Invalid Scan ID", False, f"Error: {str(e)}")
        return False

def test_delete_without_auth():
    """Test deletion without authentication (should return 401)"""
    try:
        # Create a scan first (with auth)
        scan_id = create_test_food_scan()
        if not scan_id:
            log_test("Delete Without Auth", False, "Could not create test scan")
            return False
        
        # Try to delete without auth headers
        response = requests.delete(f"{BASE_URL}/food/scan/{scan_id}", timeout=10)
        
        if response.status_code in [401, 403]:
            log_test("Delete Without Auth", True, 
                    f"Correctly returned {response.status_code} for unauthenticated request")
            return True
        else:
            log_test("Delete Without Auth", False, 
                    f"Expected 401/403 for unauthenticated request, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Delete Without Auth", False, f"Error: {str(e)}")
        return False

def test_delete_other_user_scan():
    """Test trying to delete another user's scan (should return 404)"""
    if not auth_token:
        log_test("Delete Other User Scan", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Use a UUID that looks valid but doesn't belong to this user
        other_user_scan_id = "12345678-1234-1234-1234-123456789abc"
        response = requests.delete(f"{BASE_URL}/food/scan/{other_user_scan_id}", 
                                 headers=headers, timeout=10)
        
        if response.status_code == 404:
            log_test("Delete Other User Scan", True, 
                    "Correctly returned 404 for scan not belonging to user")
            return True
        else:
            log_test("Delete Other User Scan", False, 
                    f"Expected 404 for other user's scan, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Delete Other User Scan", False, f"Error: {str(e)}")
        return False

def run_all_tests():
    """Run all DELETE food scan tests"""
    print("🧪 Starting DELETE Food Scan Endpoint Testing Suite")
    print("=" * 60)
    
    # Test sequence
    tests = [
        ("1. User Login", test_login),
        ("2. Delete Food Scan - Success", test_delete_food_scan_success),
        ("3. Verify Deletion from History", test_verify_deletion_from_history),
        ("4. Delete Same Scan Twice (404)", test_delete_same_scan_twice),
        ("5. Delete Invalid Scan ID (404)", test_delete_invalid_scan_id),
        ("6. Delete Without Auth (401)", test_delete_without_auth),
        ("7. Delete Other User Scan (404)", test_delete_other_user_scan),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            log_test(test_name, False, f"Unexpected error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 DELETE FOOD SCAN ENDPOINT TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} {test_name}: {result['message']}")
    
    print(f"\n📊 OVERALL RESULTS: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! DELETE food scan endpoint is working correctly.")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)