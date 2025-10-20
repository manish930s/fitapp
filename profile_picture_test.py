#!/usr/bin/env python3
"""
FitFlow Profile Picture Testing Suite
Tests Edit Profile functionality with profile picture support
"""

import requests
import json
import base64
import time
from datetime import datetime
import os

# Configuration
BASE_URL = "https://fitness-track-5.preview.emergentagent.com/api"
TEST_USER_EMAIL = "test@fitflow.com"
TEST_USER_PASSWORD = "Test123!"

# Global variables for test state
auth_token = None
user_id = None
test_results = {}

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

def create_test_base64_image():
    """Create a small test base64 image (10x10 pixel PNG)"""
    # This is a 10x10 red square PNG image in base64
    return "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY/z//z8DJQAggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIEQAALMABAfyFzrAAAAAASUVORK5CYII="

def test_user_registration_and_login():
    """Test user registration and login to get auth token"""
    global auth_token, user_id
    
    # First try to register the user
    register_data = {
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
        # Try registration first
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("token")
            user_id = data.get("user", {}).get("user_id")
            
            if auth_token and user_id:
                log_test("User Registration & Login", True, "User registered successfully, token received")
                return True
        elif response.status_code == 400 and "already registered" in response.text:
            # User already exists, try to login
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                auth_token = data.get("token")
                user_id = data.get("user", {}).get("user_id")
                
                if auth_token and user_id:
                    log_test("User Registration & Login", True, "User login successful, token received")
                    return True
                else:
                    log_test("User Registration & Login", False, "Missing token or user_id in login response")
                    return False
            else:
                log_test("User Registration & Login", False, 
                        f"Login failed - Status: {response.status_code}, Response: {response.text}")
                return False
        else:
            log_test("User Registration & Login", False, 
                    f"Registration failed - Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("User Registration & Login", False, f"Error: {str(e)}")
        return False

def test_get_profile_picture_field():
    """Test 1: GET /api/user/profile - verify profile_picture field is present"""
    if not auth_token:
        log_test("GET Profile Picture Field", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if profile_picture field exists in response
            if "profile_picture" in data:
                profile_picture = data.get("profile_picture")
                log_test("GET Profile Picture Field", True, 
                        f"profile_picture field present. Current value: {profile_picture}")
                return True
            else:
                log_test("GET Profile Picture Field", False, 
                        "profile_picture field missing from response")
                return False
        else:
            log_test("GET Profile Picture Field", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("GET Profile Picture Field", False, f"Error: {str(e)}")
        return False

def test_comprehensive_profile_update():
    """Test 2: PUT /api/user/profile with ALL fields including profile_picture"""
    if not auth_token:
        log_test("Comprehensive Profile Update", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create test base64 image
    test_image = create_test_base64_image()
    
    # Update ALL profile fields including profile_picture
    profile_data = {
        "name": "Jane Smith",
        "age": 28,
        "weight": 65.0,
        "profile_picture": test_image
    }
    
    try:
        response = requests.put(f"{BASE_URL}/user/profile", 
                              headers=headers, json=profile_data, timeout=10)
        
        if response.status_code == 200:
            log_test("Comprehensive Profile Update", True, 
                    "Profile updated with all fields including profile_picture")
            return True
        else:
            log_test("Comprehensive Profile Update", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Comprehensive Profile Update", False, f"Error: {str(e)}")
        return False

def test_data_persistence_verification():
    """Test 3: Verify data persistence with GET request after update"""
    if not auth_token:
        log_test("Data Persistence Verification", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify all updated fields are persisted
            expected_values = {
                "name": "Jane Smith",
                "age": 28,
                "weight": 65.0
            }
            
            verification_results = []
            for field, expected_value in expected_values.items():
                actual_value = data.get(field)
                if actual_value == expected_value:
                    verification_results.append(f"✓ {field}: {actual_value}")
                else:
                    verification_results.append(f"✗ {field}: expected {expected_value}, got {actual_value}")
            
            # Check profile_picture persistence
            profile_picture = data.get("profile_picture")
            if profile_picture and len(profile_picture) > 50:  # Base64 should be longer than 50 chars
                verification_results.append(f"✓ profile_picture: base64 data persisted ({len(profile_picture)} chars)")
                all_verified = True
            else:
                verification_results.append(f"✗ profile_picture: not properly persisted ({profile_picture})")
                all_verified = False
            
            # Check if all other fields match
            for field, expected_value in expected_values.items():
                if data.get(field) != expected_value:
                    all_verified = False
            
            if all_verified:
                log_test("Data Persistence Verification", True, 
                        f"All data persisted correctly. {'; '.join(verification_results)}")
                return True
            else:
                log_test("Data Persistence Verification", False, 
                        f"Some data not persisted correctly. {'; '.join(verification_results)}")
                return False
        else:
            log_test("Data Persistence Verification", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Data Persistence Verification", False, f"Error: {str(e)}")
        return False

def test_partial_update():
    """Test 4: PUT /api/user/profile with ONLY profile_picture field"""
    if not auth_token:
        log_test("Partial Update Test", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Get current profile data first
    try:
        response = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=10)
        if response.status_code != 200:
            log_test("Partial Update Test", False, "Could not get current profile")
            return False
        
        current_data = response.json()
        current_name = current_data.get("name")
        current_age = current_data.get("age")
        current_weight = current_data.get("weight")
        
        # Create a different test image for partial update
        new_test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAFfeTFkuQAAAABJRU5ErkJggg=="
        
        # Update ONLY profile_picture
        partial_data = {
            "profile_picture": new_test_image
        }
        
        response = requests.put(f"{BASE_URL}/user/profile", 
                              headers=headers, json=partial_data, timeout=10)
        
        if response.status_code != 200:
            log_test("Partial Update Test", False, 
                    f"Partial update failed - Status: {response.status_code}, Response: {response.text}")
            return False
        
        # Verify that only profile_picture changed, other fields remain unchanged
        response = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=10)
        if response.status_code != 200:
            log_test("Partial Update Test", False, "Could not verify partial update")
            return False
        
        updated_data = response.json()
        
        # Check that other fields remained unchanged
        verification_results = []
        if updated_data.get("name") == current_name:
            verification_results.append("✓ name unchanged")
        else:
            verification_results.append(f"✗ name changed from {current_name} to {updated_data.get('name')}")
        
        if updated_data.get("age") == current_age:
            verification_results.append("✓ age unchanged")
        else:
            verification_results.append(f"✗ age changed from {current_age} to {updated_data.get('age')}")
        
        if updated_data.get("weight") == current_weight:
            verification_results.append("✓ weight unchanged")
        else:
            verification_results.append(f"✗ weight changed from {current_weight} to {updated_data.get('weight')}")
        
        # Check that profile_picture was updated
        updated_profile_picture = updated_data.get("profile_picture")
        if updated_profile_picture == new_test_image:
            verification_results.append("✓ profile_picture updated correctly")
            success = True
        else:
            verification_results.append("✗ profile_picture not updated correctly")
            success = False
        
        # Check if other fields remained the same
        if (updated_data.get("name") == current_name and 
            updated_data.get("age") == current_age and 
            updated_data.get("weight") == current_weight and
            success):
            log_test("Partial Update Test", True, 
                    f"Partial update successful. {'; '.join(verification_results)}")
            return True
        else:
            log_test("Partial Update Test", False, 
                    f"Partial update affected other fields. {'; '.join(verification_results)}")
            return False
            
    except Exception as e:
        log_test("Partial Update Test", False, f"Error: {str(e)}")
        return False

def test_edge_cases():
    """Test 5: Edge cases - null and empty string profile_picture"""
    if not auth_token:
        log_test("Edge Cases Test", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test with null profile_picture
        null_data = {"profile_picture": None}
        
        response = requests.put(f"{BASE_URL}/user/profile", 
                              headers=headers, json=null_data, timeout=10)
        
        if response.status_code != 200:
            log_test("Edge Cases - Null", False, 
                    f"Null profile_picture failed - Status: {response.status_code}")
            return False
        
        # Verify null was set
        response = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("profile_picture") is None:
                null_test_passed = True
            else:
                null_test_passed = False
        else:
            null_test_passed = False
        
        # Test with empty string profile_picture
        empty_data = {"profile_picture": ""}
        
        response = requests.put(f"{BASE_URL}/user/profile", 
                              headers=headers, json=empty_data, timeout=10)
        
        if response.status_code != 200:
            log_test("Edge Cases - Empty String", False, 
                    f"Empty profile_picture failed - Status: {response.status_code}")
            return False
        
        # Verify empty string was set
        response = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("profile_picture") == "":
                empty_test_passed = True
            else:
                empty_test_passed = False
        else:
            empty_test_passed = False
        
        if null_test_passed and empty_test_passed:
            log_test("Edge Cases Test", True, 
                    "Both null and empty string profile_picture handled correctly")
            return True
        else:
            log_test("Edge Cases Test", False, 
                    f"Edge cases failed - Null: {null_test_passed}, Empty: {empty_test_passed}")
            return False
            
    except Exception as e:
        log_test("Edge Cases Test", False, f"Error: {str(e)}")
        return False

def run_profile_picture_tests():
    """Run all profile picture tests in order"""
    print("🚀 Starting FitFlow Profile Picture Tests")
    print("=" * 60)
    
    # Test order based on dependencies
    tests = [
        ("User Registration & Login", test_user_registration_and_login),
        ("1. GET Profile Picture Field", test_get_profile_picture_field),
        ("2. Comprehensive Profile Update", test_comprehensive_profile_update),
        ("3. Data Persistence Verification", test_data_persistence_verification),
        ("4. Partial Update Test", test_partial_update),
        ("5. Edge Cases Test", test_edge_cases)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            success = test_func()
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            log_test(test_name, False, f"Unexpected error: {str(e)}")
            failed += 1
        
        # Small delay between tests
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("📊 PROFILE PICTURE TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    # Show detailed results
    print("\n📋 DETAILED RESULTS:")
    for test_name, result in test_results.items():
        status = "✅" if result["success"] else "❌"
        print(f"{status} {test_name}: {result['message']}")
    
    return passed, failed, test_results

if __name__ == "__main__":
    passed, failed, results = run_profile_picture_tests()
    
    # Save detailed results
    with open("/app/profile_picture_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/profile_picture_test_results.json")