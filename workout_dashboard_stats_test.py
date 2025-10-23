#!/usr/bin/env python3
"""
FitFlow Workout Dashboard Stats Testing
Focused test for the "Kg and Recent Workout" display issue fix
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://verify-email-signup.preview.emergentagent.com/api"
TEST_USER_EMAIL = "test@fitflow.com"
TEST_USER_PASSWORD = "Test123!"

# Global variables
auth_token = None
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

def register_or_login_user():
    """Register or login with test credentials"""
    global auth_token
    
    # Try login first
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("token")
            
            if auth_token:
                log_test("Login", True, "Successfully logged in with existing test credentials")
                return True
            else:
                log_test("Login", False, "Missing token in login response")
                return False
        elif response.status_code == 401:
            # User doesn't exist, try to register
            print("🔄 User doesn't exist, attempting registration...")
            return register_user()
        else:
            log_test("Login", False, f"Login failed - Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Login", False, f"Login error: {str(e)}")
        return False

def register_user():
    """Register new test user"""
    global auth_token
    
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
            
            if auth_token:
                log_test("Registration", True, "Successfully registered new test user")
                return True
            else:
                log_test("Registration", False, "Missing token in registration response")
                return False
        else:
            log_test("Registration", False, f"Registration failed - Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Registration", False, f"Registration error: {str(e)}")
        return False

def test_workout_dashboard_stats():
    """Test GET /api/workouts/dashboard/stats endpoint - CRITICAL TEST for Kg and Recent Workout fix"""
    if not auth_token:
        log_test("Workout Dashboard Stats", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        print("🏋️ Testing Workout Dashboard Stats endpoint...")
        response = requests.get(f"{BASE_URL}/workouts/dashboard/stats", headers=headers, timeout=15)
        
        if response.status_code != 200:
            log_test("Workout Dashboard Stats", False, 
                    f"Failed - Status: {response.status_code}, Response: {response.text}")
            return False
        
        data = response.json()
        print(f"📊 Raw API Response: {json.dumps(data, indent=2)}")
        
        # CRITICAL VERIFICATION 1: Check required fields exist
        required_fields = ["total_workouts", "total_volume_lifted", "recent_workout", "favorite_exercise", "weight_unit"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            log_test("Workout Dashboard Stats - Required Fields", False, 
                    f"Missing required fields: {missing_fields}")
            return False
        
        # CRITICAL VERIFICATION 2: total_volume_lifted field (the "Kg" field that was broken)
        total_volume_lifted = data.get("total_volume_lifted")
        if total_volume_lifted is None:
            log_test("Workout Dashboard Stats - Total Volume Lifted", False, 
                    "total_volume_lifted field is None/undefined")
            return False
        
        if not isinstance(total_volume_lifted, (int, float)):
            log_test("Workout Dashboard Stats - Total Volume Lifted Type", False, 
                    f"total_volume_lifted should be numeric, got {type(total_volume_lifted)}: {total_volume_lifted}")
            return False
        
        # CRITICAL VERIFICATION 3: recent_workout field (the "Recent Workout" field that was broken)
        recent_workout = data.get("recent_workout")
        
        if recent_workout is not None:
            # If user has workout sessions, verify structure
            if not isinstance(recent_workout, dict):
                log_test("Workout Dashboard Stats - Recent Workout Type", False, 
                        f"recent_workout should be object or null, got {type(recent_workout)}: {recent_workout}")
                return False
            
            # Verify recent_workout structure
            required_recent_fields = ["exercise_id", "name", "created_at"]
            missing_recent_fields = [field for field in required_recent_fields if field not in recent_workout]
            
            if missing_recent_fields:
                log_test("Workout Dashboard Stats - Recent Workout Structure", False, 
                        f"Missing fields in recent_workout: {missing_recent_fields}")
                return False
            
            # Verify recent_workout.name is not empty
            recent_name = recent_workout.get("name")
            if not recent_name or not isinstance(recent_name, str) or len(recent_name.strip()) == 0:
                log_test("Workout Dashboard Stats - Recent Workout Name", False, 
                        f"recent_workout.name should be non-empty string, got: {recent_name}")
                return False
        
        # VERIFICATION 4: favorite_exercise field
        favorite_exercise = data.get("favorite_exercise")
        
        if favorite_exercise is not None:
            if not isinstance(favorite_exercise, dict):
                log_test("Workout Dashboard Stats - Favorite Exercise Type", False, 
                        f"favorite_exercise should be object or null, got {type(favorite_exercise)}")
                return False
            
            # Verify favorite_exercise structure
            required_fav_fields = ["exercise_id", "name", "count"]
            missing_fav_fields = [field for field in required_fav_fields if field not in favorite_exercise]
            
            if missing_fav_fields:
                log_test("Workout Dashboard Stats - Favorite Exercise Structure", False, 
                        f"Missing fields in favorite_exercise: {missing_fav_fields}")
                return False
        
        # VERIFICATION 5: weight_unit field
        weight_unit = data.get("weight_unit")
        if not weight_unit or weight_unit not in ["kg", "lbs"]:
            log_test("Workout Dashboard Stats - Weight Unit", False, 
                    f"weight_unit should be 'kg' or 'lbs', got: {weight_unit}")
            return False
        
        # VERIFICATION 6: total_workouts field
        total_workouts = data.get("total_workouts")
        if not isinstance(total_workouts, int) or total_workouts < 0:
            log_test("Workout Dashboard Stats - Total Workouts", False, 
                    f"total_workouts should be non-negative integer, got: {total_workouts}")
            return False
        
        # SUCCESS: All critical fields verified
        success_message = f"✅ CRITICAL FIXES VERIFIED: "
        success_message += f"total_volume_lifted={total_volume_lifted} (numeric), "
        
        if recent_workout:
            success_message += f"recent_workout.name='{recent_workout['name']}' (valid), "
        else:
            success_message += f"recent_workout=null (no sessions yet), "
        
        success_message += f"weight_unit='{weight_unit}', total_workouts={total_workouts}"
        
        if favorite_exercise:
            success_message += f", favorite_exercise.name='{favorite_exercise['name']}'"
        
        log_test("Workout Dashboard Stats", True, success_message)
        
        # Additional detailed logging for debugging
        print(f"\n📋 DETAILED VERIFICATION RESULTS:")
        print(f"   ✅ total_volume_lifted: {total_volume_lifted} ({type(total_volume_lifted).__name__})")
        print(f"   ✅ recent_workout: {recent_workout}")
        print(f"   ✅ favorite_exercise: {favorite_exercise}")
        print(f"   ✅ weight_unit: {weight_unit}")
        print(f"   ✅ total_workouts: {total_workouts}")
        
        return True
        
    except Exception as e:
        log_test("Workout Dashboard Stats", False, f"Error: {str(e)}")
        return False

def create_test_workout_session():
    """Create a test workout session to ensure we have data for testing"""
    if not auth_token:
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Create a simple workout session
        session_data = {
            "exercise_id": "bench-press",
            "sets": [
                {"reps": 10, "weight": 60, "rpe": 7},
                {"reps": 8, "weight": 70, "rpe": 8}
            ],
            "notes": "Test session for dashboard stats"
        }
        
        response = requests.post(f"{BASE_URL}/workouts/sessions", 
                               headers=headers, json=session_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get("session_id")
            total_volume = result.get("total_volume")
            log_test("Create Test Workout", True, 
                    f"Created test workout session (ID: {session_id[:8]}..., Volume: {total_volume})")
            return True
        else:
            log_test("Create Test Workout", False, 
                    f"Failed to create test workout - Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Create Test Workout", False, f"Error creating test workout: {str(e)}")
        return False

def run_focused_test():
    """Run the focused test for workout dashboard stats"""
    print("🎯 FOCUSED TEST: Workout Dashboard Stats - 'Kg and Recent Workout' Fix Verification")
    print("=" * 80)
    
    # Step 1: Login or Register
    if not register_or_login_user():
        print("❌ Cannot proceed without authentication")
        return False
    
    # Step 2: Create a test workout session (to ensure we have data)
    print("\n📝 Creating test workout session to ensure data exists...")
    create_test_workout_session()
    
    # Step 3: Test the critical endpoint
    print("\n🔍 Testing GET /api/workouts/dashboard/stats endpoint...")
    success = test_workout_dashboard_stats()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY:")
    
    passed_tests = sum(1 for result in test_results.values() if result["success"])
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {status} {test_name}: {result['message']}")
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if success:
        print("✅ CRITICAL SUCCESS: Workout Dashboard Stats endpoint working correctly!")
        print("   - total_volume_lifted field present and numeric (fixes 'Kg' display)")
        print("   - recent_workout field present with proper structure (fixes 'Recent Workout' display)")
        print("   - All required fields validated")
    else:
        print("❌ CRITICAL FAILURE: Issues found with workout dashboard stats endpoint")
    
    return success

if __name__ == "__main__":
    run_focused_test()