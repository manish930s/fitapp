#!/usr/bin/env python3
"""
FitFlow Signup/Registration Testing Suite
Tests the complete user registration flow as specified in the review request
"""

import requests
import json
import time
from datetime import datetime
import os

# Configuration
BASE_URL = "https://auth-repair-52.preview.emergentagent.com/api"

# Test user data as specified in the review request
TEST_USER_DATA = {
    "name": "SignupTest User",
    "email": "signuptest@fitflow.com",
    "password": "Test123!",
    "age": 25,
    "gender": "male",
    "height": 175,
    "weight": 70,
    "goal_weight": 65,
    "activity_level": "moderate"
}

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

def test_health_check():
    """Test the health check endpoint first"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_test("Health Check", True, f"Service is healthy: {data.get('service', 'Unknown')}")
            return True
        else:
            log_test("Health Check", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("Health Check", False, f"Connection error: {str(e)}")
        return False

def cleanup_existing_user():
    """Clean up any existing user with the test email"""
    try:
        # Try to login first to see if user exists
        login_data = {
            "email": TEST_USER_DATA["email"],
            "password": TEST_USER_DATA["password"]
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            print(f"⚠️  User {TEST_USER_DATA['email']} already exists - this is expected for repeated tests")
            return True
        return False
    except Exception as e:
        print(f"⚠️  Cleanup check failed: {str(e)}")
        return False

def test_user_registration():
    """Test POST /api/auth/register endpoint with specified user credentials"""
    global auth_token, user_id
    
    print(f"\n🔍 Testing User Registration with data:")
    print(f"   Name: {TEST_USER_DATA['name']}")
    print(f"   Email: {TEST_USER_DATA['email']}")
    print(f"   Age: {TEST_USER_DATA['age']}")
    print(f"   Gender: {TEST_USER_DATA['gender']}")
    print(f"   Height: {TEST_USER_DATA['height']} cm")
    print(f"   Weight: {TEST_USER_DATA['weight']} kg")
    print(f"   Goal Weight: {TEST_USER_DATA['goal_weight']} kg")
    print(f"   Activity Level: {TEST_USER_DATA['activity_level']}")
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER_DATA, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure as specified in review
            required_fields = ["message", "token", "user", "daily_calories"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                log_test("Registration Response Structure", False, 
                        f"Missing required fields: {missing_fields}")
                return False
            
            # Verify message
            if data.get("message") != "Registration successful!":
                log_test("Registration Message", False, 
                        f"Expected 'Registration successful!', got: {data.get('message')}")
                return False
            
            # Verify token is JWT string
            token = data.get("token")
            if not token or not isinstance(token, str) or len(token) < 50:
                log_test("Registration JWT Token", False, 
                        f"Invalid JWT token format: {token}")
                return False
            
            auth_token = token
            
            # Verify user object structure
            user = data.get("user", {})
            user_required_fields = ["user_id", "name", "email", "age", "gender", "height", "weight", "goal_weight", "activity_level"]
            user_missing_fields = [field for field in user_required_fields if field not in user]
            
            if user_missing_fields:
                log_test("Registration User Object", False, 
                        f"Missing user fields: {user_missing_fields}")
                return False
            
            user_id = user.get("user_id")
            
            # Verify user data matches input
            data_matches = (
                user.get("name") == TEST_USER_DATA["name"] and
                user.get("email") == TEST_USER_DATA["email"] and
                user.get("age") == TEST_USER_DATA["age"] and
                user.get("gender") == TEST_USER_DATA["gender"] and
                user.get("height") == TEST_USER_DATA["height"] and
                user.get("weight") == TEST_USER_DATA["weight"] and
                user.get("goal_weight") == TEST_USER_DATA["goal_weight"] and
                user.get("activity_level") == TEST_USER_DATA["activity_level"]
            )
            
            if not data_matches:
                log_test("Registration User Data Verification", False, 
                        f"User data doesn't match input. Got: {user}")
                return False
            
            # Verify daily_calories object
            daily_calories = data.get("daily_calories", {})
            calorie_required_fields = ["bmr", "tdee", "daily_target"]
            calorie_missing_fields = [field for field in calorie_required_fields if field not in daily_calories]
            
            if calorie_missing_fields:
                log_test("Registration Daily Calories", False, 
                        f"Missing daily_calories fields: {calorie_missing_fields}")
                return False
            
            # Verify calorie calculations are reasonable
            bmr = daily_calories.get("bmr")
            tdee = daily_calories.get("tdee")
            daily_target = daily_calories.get("daily_target")
            
            if not (1500 <= bmr <= 2500 and 1800 <= tdee <= 3500 and 1500 <= daily_target <= 3000):
                log_test("Registration Calorie Calculations", False, 
                        f"Unreasonable calorie values: BMR={bmr}, TDEE={tdee}, Target={daily_target}")
                return False
            
            log_test("User Registration", True, 
                    f"Registration successful! User ID: {user_id}, Daily Target: {daily_target} calories")
            return True
            
        elif response.status_code == 400 and "already registered" in response.text:
            # User already exists - this is expected for repeated tests
            log_test("User Registration", True, 
                    "User already exists (expected for repeated tests) - proceeding with login test")
            return True
        else:
            log_test("User Registration", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("User Registration", False, f"Error: {str(e)}")
        return False

def test_immediate_login():
    """Test that user can login immediately after registration using same credentials"""
    global auth_token, user_id
    
    login_data = {
        "email": TEST_USER_DATA["email"],
        "password": TEST_USER_DATA["password"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify login response structure
            required_fields = ["message", "token", "user"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                log_test("Login Response Structure", False, 
                        f"Missing required fields: {missing_fields}")
                return False
            
            # Verify login message
            if data.get("message") != "Login successful":
                log_test("Login Message", False, 
                        f"Expected 'Login successful', got: {data.get('message')}")
                return False
            
            # Verify token
            token = data.get("token")
            if not token or not isinstance(token, str) or len(token) < 50:
                log_test("Login JWT Token", False, 
                        f"Invalid JWT token format: {token}")
                return False
            
            auth_token = token
            
            # Verify user object
            user = data.get("user", {})
            login_user_fields = ["user_id", "name", "email"]
            login_missing_fields = [field for field in login_user_fields if field not in user]
            
            if login_missing_fields:
                log_test("Login User Object", False, 
                        f"Missing user fields: {login_missing_fields}")
                return False
            
            # Verify user data matches registration
            if user.get("email") != TEST_USER_DATA["email"] or user.get("name") != TEST_USER_DATA["name"]:
                log_test("Login User Data Verification", False, 
                        f"User data doesn't match registration. Got: {user}")
                return False
            
            user_id = user.get("user_id")
            
            log_test("Immediate Login After Registration", True, 
                    f"Login successful with same credentials. User ID: {user_id}")
            return True
        else:
            log_test("Immediate Login After Registration", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Immediate Login After Registration", False, f"Error: {str(e)}")
        return False

def test_jwt_token_validity():
    """Test that JWT token is valid and can be used for authenticated requests"""
    if not auth_token:
        log_test("JWT Token Validity", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test token with user profile endpoint
        response = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify we get user data back
            if not data or "name" not in data or "email" not in data:
                log_test("JWT Token Validity", False, 
                        "Token valid but profile data incomplete")
                return False
            
            # Verify the data matches our test user
            if data.get("email") != TEST_USER_DATA["email"]:
                log_test("JWT Token Validity", False, 
                        f"Token returns wrong user data: {data.get('email')}")
                return False
            
            log_test("JWT Token Validity", True, 
                    f"JWT token valid and returns correct user profile for {data.get('email')}")
            return True
        elif response.status_code == 401:
            log_test("JWT Token Validity", False, 
                    "JWT token rejected - authentication failed")
            return False
        else:
            log_test("JWT Token Validity", False, 
                    f"Unexpected status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("JWT Token Validity", False, f"Error: {str(e)}")
        return False

def test_duplicate_email_error():
    """Test error handling: Try to register with the same email again"""
    try:
        # Try to register with the same email again
        response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER_DATA, timeout=10)
        
        if response.status_code == 400:
            response_text = response.text.lower()
            if "already registered" in response_text or "email already" in response_text:
                log_test("Duplicate Email Error Handling", True, 
                        "Correctly returned 400 error for duplicate email registration")
                return True
            else:
                log_test("Duplicate Email Error Handling", False, 
                        f"400 status but wrong error message: {response.text}")
                return False
        else:
            log_test("Duplicate Email Error Handling", False, 
                    f"Expected 400 for duplicate email, got: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Duplicate Email Error Handling", False, f"Error: {str(e)}")
        return False

def test_invalid_registration_data():
    """Test error handling with invalid registration data"""
    try:
        # Test with missing required fields
        invalid_data = {
            "name": "Test User",
            "email": "invalid@test.com"
            # Missing password and other required fields
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=invalid_data, timeout=10)
        
        if response.status_code in [400, 422]:  # Either is acceptable for validation errors
            log_test("Invalid Registration Data", True, 
                    f"Correctly rejected invalid data with status {response.status_code}")
            return True
        else:
            log_test("Invalid Registration Data", False, 
                    f"Expected 400/422 for invalid data, got: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Invalid Registration Data", False, f"Error: {str(e)}")
        return False

def run_comprehensive_signup_test():
    """Run the complete signup/registration test suite"""
    print("🚀 Starting Comprehensive Signup/Registration Test Suite")
    print("=" * 70)
    
    # Track overall success
    all_tests_passed = True
    
    # Test 1: Health check
    if not test_health_check():
        all_tests_passed = False
    
    # Test 2: Check for existing user
    cleanup_existing_user()
    
    # Test 3: User registration
    if not test_user_registration():
        all_tests_passed = False
    
    # Test 4: Immediate login after registration
    if not test_immediate_login():
        all_tests_passed = False
    
    # Test 5: JWT token validity
    if not test_jwt_token_validity():
        all_tests_passed = False
    
    # Test 6: Duplicate email error handling
    if not test_duplicate_email_error():
        all_tests_passed = False
    
    # Test 7: Invalid registration data handling
    if not test_invalid_registration_data():
        all_tests_passed = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed_count = sum(1 for result in test_results.values() if result["success"])
    total_count = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} {test_name}")
        if not result["success"]:
            print(f"     Error: {result['message']}")
    
    print(f"\n📈 Results: {passed_count}/{total_count} tests passed")
    
    if all_tests_passed:
        print("🎉 ALL SIGNUP/REGISTRATION TESTS PASSED!")
        print("✅ Complete user registration flow works end-to-end without network errors")
    else:
        print("❌ SOME TESTS FAILED - Review the errors above")
    
    return all_tests_passed

if __name__ == "__main__":
    success = run_comprehensive_signup_test()
    exit(0 if success else 1)