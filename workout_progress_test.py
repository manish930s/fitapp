#!/usr/bin/env python3
"""
Enhanced Workout Progress Tracking Backend API Testing
Tests the new max_reps field in exercise stats and history endpoints
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://supabase-connect-22.preview.emergentagent.com/api"
TEST_USER_EMAIL = "test@fitflow.com"
TEST_USER_PASSWORD = "Test123!"

# Global variables
auth_token = None
session_id = None

def log_test(test_name, success, message="", details=None):
    """Log test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}: {message}")
    if details:
        print(f"   Details: {details}")

def login_user():
    """Login with test credentials"""
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
                log_test("User Login", True, "Login successful, token received")
                return True
            else:
                log_test("User Login", False, "Missing token in response")
                return False
        else:
            log_test("User Login", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("User Login", False, f"Error: {str(e)}")
        return False

def create_test_workout_session():
    """Create a test workout session for bench-press to ensure we have data"""
    global session_id
    
    if not auth_token:
        log_test("Create Test Session", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create a workout session with varied reps to test max_reps calculation
    session_data = {
        "exercise_id": "bench-press",
        "sets": [
            {"reps": 12, "weight": 50, "rpe": 6},  # Highest reps
            {"reps": 10, "weight": 60, "rpe": 7},
            {"reps": 8, "weight": 70, "rpe": 8},
            {"reps": 6, "weight": 80, "rpe": 9}    # Highest weight
        ],
        "notes": "Test session for max_reps verification"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/workouts/sessions", 
                               headers=headers, json=session_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get("session_id")
            
            if session_id:
                log_test("Create Test Session", True, 
                        f"Created test session with max reps: 12, max weight: 80kg")
                return True
            else:
                log_test("Create Test Session", False, "No session_id returned")
                return False
        else:
            log_test("Create Test Session", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Create Test Session", False, f"Error: {str(e)}")
        return False

def test_exercise_stats_max_reps():
    """Test GET /api/workouts/exercises/bench-press/stats - Verify max_reps field"""
    if not auth_token:
        log_test("Exercise Stats Max Reps", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/workouts/exercises/bench-press/stats", 
                              headers=headers, timeout=10)
        
        if response.status_code != 200:
            log_test("Exercise Stats Max Reps", False, 
                    f"Failed - Status: {response.status_code}, Response: {response.text}")
            return False
        
        stats = response.json()
        
        # Verify max_reps field exists
        if "max_reps" not in stats:
            log_test("Exercise Stats Max Reps", False, 
                    "max_reps field missing from response")
            return False
        
        max_reps = stats.get("max_reps")
        
        # Verify max_reps is an integer
        if not isinstance(max_reps, int):
            log_test("Exercise Stats Max Reps", False, 
                    f"max_reps should be integer, got {type(max_reps)}: {max_reps}")
            return False
        
        # Verify max_reps contains the highest number of reps (should be 12 from our test data)
        if max_reps != 12:
            log_test("Exercise Stats Max Reps", False, 
                    f"Expected max_reps=12 (highest from all sets), got {max_reps}")
            return False
        
        # Verify existing fields still work
        required_existing_fields = ["personal_best", "estimated_1rm", "total_sessions", "total_volume"]
        missing_fields = [field for field in required_existing_fields if field not in stats]
        
        if missing_fields:
            log_test("Exercise Stats Max Reps", False, 
                    f"Missing existing fields: {missing_fields}")
            return False
        
        # Verify personal_best is still correct (should be 80 from our test data)
        personal_best = stats.get("personal_best")
        if personal_best != 80:
            log_test("Exercise Stats Max Reps", False, 
                    f"personal_best incorrect: expected 80, got {personal_best}")
            return False
        
        # Verify estimated_1rm is calculated correctly
        estimated_1rm = stats.get("estimated_1rm")
        if estimated_1rm is None or estimated_1rm <= 0:
            log_test("Exercise Stats Max Reps", False, 
                    f"estimated_1rm invalid: {estimated_1rm}")
            return False
        
        log_test("Exercise Stats Max Reps", True, 
                f"✅ max_reps field working correctly: {max_reps} reps (highest from all sets). "
                f"Existing fields intact: PB={personal_best}kg, 1RM={estimated_1rm}kg")
        return True
        
    except Exception as e:
        log_test("Exercise Stats Max Reps", False, f"Error: {str(e)}")
        return False

def test_exercise_history_max_reps():
    """Test GET /api/workouts/exercises/bench-press/history - Verify max_reps field in each session"""
    if not auth_token:
        log_test("Exercise History Max Reps", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/workouts/exercises/bench-press/history", 
                              headers=headers, timeout=10)
        
        if response.status_code != 200:
            log_test("Exercise History Max Reps", False, 
                    f"Failed - Status: {response.status_code}, Response: {response.text}")
            return False
        
        data = response.json()
        history = data.get("history", [])
        
        if not history:
            log_test("Exercise History Max Reps", False, 
                    "No history found for bench-press")
            return False
        
        # Check each session in history for max_reps field
        for i, session in enumerate(history):
            # Verify max_reps field exists
            if "max_reps" not in session:
                log_test("Exercise History Max Reps", False, 
                        f"max_reps field missing from session {i}")
                return False
            
            max_reps = session.get("max_reps")
            
            # Verify max_reps is an integer
            if not isinstance(max_reps, int):
                log_test("Exercise History Max Reps", False, 
                        f"max_reps should be integer in session {i}, got {type(max_reps)}: {max_reps}")
                return False
            
            # Verify max_reps is positive (should represent highest reps from that session)
            if max_reps <= 0:
                log_test("Exercise History Max Reps", False, 
                        f"max_reps should be positive in session {i}, got {max_reps}")
                return False
            
            # Verify existing fields still work
            required_existing_fields = ["max_weight", "total_volume", "total_sets"]
            missing_fields = [field for field in required_existing_fields if field not in session]
            
            if missing_fields:
                log_test("Exercise History Max Reps", False, 
                        f"Missing existing fields in session {i}: {missing_fields}")
                return False
        
        # For the most recent session (our test session), verify max_reps is 12
        most_recent_session = history[0]
        recent_max_reps = most_recent_session.get("max_reps")
        
        if recent_max_reps != 12:
            log_test("Exercise History Max Reps", False, 
                    f"Expected max_reps=12 in most recent session, got {recent_max_reps}")
            return False
        
        # Verify max_weight is still correct in most recent session
        recent_max_weight = most_recent_session.get("max_weight")
        if recent_max_weight != 80:
            log_test("Exercise History Max Reps", False, 
                    f"Expected max_weight=80 in most recent session, got {recent_max_weight}")
            return False
        
        log_test("Exercise History Max Reps", True, 
                f"✅ max_reps field working correctly in all {len(history)} sessions. "
                f"Most recent session: max_reps={recent_max_reps}, max_weight={recent_max_weight}kg")
        return True
        
    except Exception as e:
        log_test("Exercise History Max Reps", False, f"Error: {str(e)}")
        return False

def test_max_reps_calculation_accuracy():
    """Test that max_reps calculation is accurate by creating another session with known data"""
    if not auth_token:
        log_test("Max Reps Calculation", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Create another session with specific reps to verify calculation
        session_data = {
            "exercise_id": "bench-press",
            "sets": [
                {"reps": 5, "weight": 85, "rpe": 9},   # Highest weight
                {"reps": 15, "weight": 40, "rpe": 6},  # Highest reps - should be max_reps
                {"reps": 8, "weight": 75, "rpe": 8}
            ],
            "notes": "Second test session for max_reps accuracy"
        }
        
        response = requests.post(f"{BASE_URL}/workouts/sessions", 
                               headers=headers, json=session_data, timeout=10)
        
        if response.status_code != 200:
            log_test("Max Reps Calculation", False, 
                    f"Failed to create second session - Status: {response.status_code}")
            return False
        
        # Now check the updated stats
        response = requests.get(f"{BASE_URL}/workouts/exercises/bench-press/stats", 
                              headers=headers, timeout=10)
        
        if response.status_code != 200:
            log_test("Max Reps Calculation", False, 
                    f"Failed to get updated stats - Status: {response.status_code}")
            return False
        
        stats = response.json()
        max_reps = stats.get("max_reps")
        
        # Should now be 15 (highest reps from all sessions)
        if max_reps != 15:
            log_test("Max Reps Calculation", False, 
                    f"Expected max_reps=15 after second session, got {max_reps}")
            return False
        
        # Personal best should now be 85 (highest weight from all sessions)
        personal_best = stats.get("personal_best")
        if personal_best != 85:
            log_test("Max Reps Calculation", False, 
                    f"Expected personal_best=85 after second session, got {personal_best}")
            return False
        
        # Check history to verify the new session has correct max_reps
        response = requests.get(f"{BASE_URL}/workouts/exercises/bench-press/history", 
                              headers=headers, timeout=10)
        
        if response.status_code == 200:
            history_data = response.json()
            history = history_data.get("history", [])
            
            if history:
                # Most recent session should have max_reps=15
                recent_session = history[0]
                recent_max_reps = recent_session.get("max_reps")
                
                if recent_max_reps != 15:
                    log_test("Max Reps Calculation", False, 
                            f"Expected max_reps=15 in most recent session history, got {recent_max_reps}")
                    return False
        
        log_test("Max Reps Calculation", True, 
                f"✅ max_reps calculation accurate: updated to {max_reps} after new session. "
                f"Personal best also updated to {personal_best}kg")
        return True
        
    except Exception as e:
        log_test("Max Reps Calculation", False, f"Error: {str(e)}")
        return False

def run_enhanced_workout_tests():
    """Run all enhanced workout progress tracking tests"""
    print("🏋️ Enhanced Workout Progress Tracking Backend API Tests")
    print("=" * 60)
    
    # Step 1: Login
    if not login_user():
        print("❌ Cannot proceed without authentication")
        return False
    
    # Step 2: Create test workout session (if needed)
    if not create_test_workout_session():
        print("❌ Cannot proceed without test data")
        return False
    
    # Step 3: Test Exercise Stats API with max_reps
    stats_success = test_exercise_stats_max_reps()
    
    # Step 4: Test Exercise History API with max_reps
    history_success = test_exercise_history_max_reps()
    
    # Step 5: Test max_reps calculation accuracy
    calculation_success = test_max_reps_calculation_accuracy()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏋️ ENHANCED WORKOUT PROGRESS TRACKING TEST SUMMARY")
    print("=" * 60)
    
    all_tests_passed = stats_success and history_success and calculation_success
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Exercise Stats API - max_reps field working correctly")
        print("✅ Exercise History API - max_reps field in each session")
        print("✅ Max reps calculation accuracy verified")
        print("✅ All existing functionality remains intact")
    else:
        print("❌ SOME TESTS FAILED!")
        if not stats_success:
            print("❌ Exercise Stats API - max_reps field issues")
        if not history_success:
            print("❌ Exercise History API - max_reps field issues")
        if not calculation_success:
            print("❌ Max reps calculation accuracy issues")
    
    return all_tests_passed

if __name__ == "__main__":
    success = run_enhanced_workout_tests()
    exit(0 if success else 1)