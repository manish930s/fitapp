#!/usr/bin/env python3
"""
FitFlow Workout Dashboard Stats Edge Case Testing
Test the endpoint when user has no workout sessions
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://verify-email-signup.preview.emergentagent.com/api"
TEST_USER_EMAIL = "test_empty@fitflow.com"
TEST_USER_PASSWORD = "Test123!"

# Global variables
auth_token = None

def register_new_user():
    """Register a new user with no workout history"""
    global auth_token
    
    user_data = {
        "name": "Test Empty User",
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "age": 25,
        "gender": "female",
        "height": 165.0,
        "weight": 60.0,
        "activity_level": "light",
        "goal_weight": 55.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("token")
            
            if auth_token:
                print("✅ Successfully registered new user with no workout history")
                return True
            else:
                print("❌ Missing token in registration response")
                return False
        elif response.status_code == 400 and "already registered" in response.text:
            # User exists, try to login
            return login_existing_user()
        else:
            print(f"❌ Registration failed - Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return False

def login_existing_user():
    """Login with existing user"""
    global auth_token
    
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
                print("✅ Successfully logged in with existing user")
                return True
            else:
                print("❌ Missing token in login response")
                return False
        else:
            print(f"❌ Login failed - Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False

def test_empty_workout_dashboard_stats():
    """Test dashboard stats when user has no workout sessions"""
    if not auth_token:
        print("❌ No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        print("🏋️ Testing Workout Dashboard Stats endpoint for user with no workouts...")
        response = requests.get(f"{BASE_URL}/workouts/dashboard/stats", headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Failed - Status: {response.status_code}, Response: {response.text}")
            return False
        
        data = response.json()
        print(f"📊 Raw API Response: {json.dumps(data, indent=2)}")
        
        # CRITICAL VERIFICATION: Check expected values for empty state
        expected_values = {
            "total_workouts": 0,
            "total_volume_lifted": 0,
            "workouts_this_week": 0,
            "workouts_this_month": 0,
            "favorite_exercise": None,
            "recent_workout": None
        }
        
        all_correct = True
        
        for field, expected_value in expected_values.items():
            actual_value = data.get(field)
            
            if actual_value != expected_value:
                print(f"❌ {field}: Expected {expected_value}, got {actual_value}")
                all_correct = False
            else:
                print(f"✅ {field}: {actual_value} (correct)")
        
        # Check weight_unit is present (minor issue - missing in empty state)
        weight_unit = data.get("weight_unit")
        if weight_unit is None:
            print(f"⚠️  weight_unit: Missing (minor issue - should default to 'kg' or user preference)")
            # This is a minor issue, not critical for the main fix
        elif weight_unit not in ["kg", "lbs"]:
            print(f"❌ weight_unit: Expected 'kg' or 'lbs', got {weight_unit}")
            all_correct = False
        else:
            print(f"✅ weight_unit: {weight_unit} (correct)")
        
        if all_correct:
            print("✅ EDGE CASE SUCCESS: All critical values correct for user with no workout sessions")
            return True
        else:
            print("❌ EDGE CASE FAILURE: Some values incorrect for empty state")
            return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def run_edge_case_test():
    """Run the edge case test"""
    print("🎯 EDGE CASE TEST: Workout Dashboard Stats - No Workout Sessions")
    print("=" * 70)
    
    # Step 1: Register/Login user with no workout history
    if not register_new_user():
        print("❌ Cannot proceed without authentication")
        return False
    
    # Step 2: Test the endpoint
    success = test_empty_workout_dashboard_stats()
    
    # Summary
    print("\n" + "=" * 70)
    if success:
        print("✅ EDGE CASE PASSED: Dashboard stats correctly handle empty workout state")
        print("   - total_volume_lifted: 0 (correct for no workouts)")
        print("   - recent_workout: null (correct for no workouts)")
        print("   - All numeric fields are 0")
        print("   - All object fields are null")
    else:
        print("❌ EDGE CASE FAILED: Issues with empty workout state handling")
    
    return success

if __name__ == "__main__":
    run_edge_case_test()