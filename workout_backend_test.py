#!/usr/bin/env python3
"""
COMPREHENSIVE WORKOUT TRACKING BACKEND TESTING
Focus on NEW untested features as specified in review request
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://task-done-5.preview.emergentagent.com/api"
TEST_USER_EMAIL = "test@fitflow.com"
TEST_USER_PASSWORD = "Test123!"

# Global variables
auth_token = None
test_results = {}
created_session_ids = []

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
                log_test("Login", True, "Successfully logged in with test credentials")
                return True
            else:
                log_test("Login", False, "No token received")
                return False
        else:
            log_test("Login", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Login", False, f"Error: {str(e)}")
        return False

def test_expanded_exercise_library():
    """Test EXPANDED EXERCISE LIBRARY (35+ exercises) - PRIORITY 2"""
    if not auth_token:
        log_test("Expanded Exercise Library", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        print("🏋️ Testing EXPANDED Exercise Library (35+ exercises)...")
        
        # Test 1: Get ALL exercises - Should return 35+ exercises
        response = requests.get(f"{BASE_URL}/workouts/exercises", headers=headers, timeout=10)
        
        if response.status_code != 200:
            log_test("Expanded Exercise Library - All", False, 
                    f"Failed - Status: {response.status_code}, Response: {response.text}")
            return False
        
        data = response.json()
        exercises = data.get("exercises", [])
        
        # CRITICAL: Should return 35+ exercises (expanded from 6)
        if len(exercises) < 35:
            log_test("Expanded Exercise Library - Count", False, 
                    f"Expected 35+ exercises, got {len(exercises)}. Library not expanded!")
            return False
        
        # Test 2: Test ALL 7 categories (including NEW ones: Shoulders, Arms, Core)
        categories_to_test = {
            "All": 35,  # Should return all 35+ exercises
            "Chest": 6,  # Should return 6 exercises (includes Chest Press)
            "Back": 6,   # Should return 6 exercises  
            "Legs": 7,   # Should return 7 exercises
            "Shoulders": 5,  # NEW - Should return 5 exercises
            "Arms": 5,       # NEW - Should return 5 exercises
            "Core": 6        # NEW - Should return 6 exercises (includes Mountain Climbers)
        }
        
        category_results = {}
        
        for category, expected_count in categories_to_test.items():
            if category == "All":
                category_exercises = exercises
            else:
                response = requests.get(f"{BASE_URL}/workouts/exercises?category={category}", 
                                      headers=headers, timeout=10)
                
                if response.status_code != 200:
                    log_test(f"Expanded Exercise Library - {category}", False, 
                            f"Category {category} failed - Status: {response.status_code}")
                    return False
                
                category_data = response.json()
                category_exercises = category_data.get("exercises", [])
            
            actual_count = len(category_exercises)
            category_results[category] = actual_count
            
            # For "All", check minimum count
            if category == "All":
                if actual_count < expected_count:
                    log_test(f"Expanded Exercise Library - {category}", False, 
                            f"Expected at least {expected_count} exercises, got {actual_count}")
                    return False
            else:
                # For specific categories, check exact count
                if actual_count != expected_count:
                    log_test(f"Expanded Exercise Library - {category}", False, 
                            f"Expected {expected_count} {category} exercises, got {actual_count}")
                    return False
        
        # Test 3: Verify specific NEW exercises exist
        new_exercises_to_check = {
            "Shoulders": ["Lateral Raise", "Front Raise", "Rear Delt Fly", "Shrugs"],
            "Arms": ["Bicep Curl", "Hammer Curl", "Tricep Pushdown", "Dips", "Skull Crushers"],
            "Core": ["Plank", "Crunches", "Russian Twists", "Leg Raises", "Cable Crunches", "Mountain Climbers"]
        }
        
        for category, exercise_names in new_exercises_to_check.items():
            response = requests.get(f"{BASE_URL}/workouts/exercises?category={category}", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                category_data = response.json()
                category_exercises = category_data.get("exercises", [])
                found_names = [ex["name"] for ex in category_exercises]
                
                missing_exercises = [name for name in exercise_names if name not in found_names]
                if missing_exercises:
                    log_test(f"Expanded Exercise Library - {category} Exercises", False, 
                            f"Missing {category} exercises: {missing_exercises}")
                    return False
        
        log_test("Expanded Exercise Library", True, 
                f"✅ EXPANDED LIBRARY CONFIRMED: {category_results['All']} total exercises, "
                f"ALL 7 categories working: Chest({category_results['Chest']}), "
                f"Back({category_results['Back']}), Legs({category_results['Legs']}), "
                f"Shoulders({category_results['Shoulders']}), Arms({category_results['Arms']}), "
                f"Core({category_results['Core']})")
        return True
        
    except Exception as e:
        log_test("Expanded Exercise Library", False, f"Error: {str(e)}")
        return False

def test_real_unsplash_images():
    """Test REAL UNSPLASH IMAGES VERIFICATION - PRIORITY 3"""
    if not auth_token:
        log_test("Real Unsplash Images", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        print("🖼️ Testing REAL Unsplash Images (no placeholder emojis)...")
        
        # Test specific NEW exercises as mentioned in review
        test_exercises = ["lateral-raise", "bicep-curl", "plank"]
        
        for exercise_id in test_exercises:
            response = requests.get(f"{BASE_URL}/workouts/exercises/{exercise_id}", 
                                  headers=headers, timeout=10)
            
            if response.status_code != 200:
                log_test(f"Real Unsplash Images - {exercise_id}", False, 
                        f"Failed to get {exercise_id} - Status: {response.status_code}")
                return False
            
            exercise = response.json()
            image_url = exercise.get("image_url", "")
            
            # CRITICAL: Check for real Unsplash URLs
            if not image_url or "images.unsplash.com" not in image_url:
                log_test(f"Real Unsplash Images - {exercise_id}", False, 
                        f"Expected real Unsplash URL for {exercise_id}, got: {image_url}")
                return False
            
            # Check NO placeholder emojis in image_url
            emoji_indicators = ["🏋️", "💪", "🤸", "🏃", "emoji"]
            if any(indicator in image_url for indicator in emoji_indicators):
                log_test(f"Real Unsplash Images - {exercise_id}", False, 
                        f"Found placeholder emoji in image_url for {exercise_id}: {image_url}")
                return False
        
        # Test a sample of all exercises for real images
        response = requests.get(f"{BASE_URL}/workouts/exercises", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            exercises = data.get("exercises", [])
            
            # Check first 10 exercises for real Unsplash images
            sample_exercises = exercises[:10]
            invalid_images = []
            
            for exercise in sample_exercises:
                image_url = exercise.get("image_url", "")
                if not image_url or "images.unsplash.com" not in image_url:
                    invalid_images.append(exercise.get("name", "Unknown"))
            
            if invalid_images:
                log_test("Real Unsplash Images - Sample Check", False, 
                        f"Exercises with invalid images: {invalid_images}")
                return False
        
        log_test("Real Unsplash Images", True, 
                f"✅ ALL EXERCISES have real Unsplash images (verified {len(test_exercises)} new exercises + sample)")
        return True
        
    except Exception as e:
        log_test("Real Unsplash Images", False, f"Error: {str(e)}")
        return False

def test_auto_suggestion_feature():
    """Test AUTO-SUGGESTION FEATURE (last_session field) - PRIORITY 4"""
    if not auth_token:
        log_test("Auto-Suggestion Feature", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        print("💡 Testing AUTO-SUGGESTION Feature (last_session field)...")
        
        # Step 1: Create a workout session for bench-press with specific sets
        session_data = {
            "exercise_id": "bench-press",
            "sets": [
                {"reps": 10, "weight": 60, "rpe": 7},
                {"reps": 8, "weight": 70, "rpe": 8},
                {"reps": 6, "weight": 80, "rpe": 9}
            ],
            "notes": "Auto-suggestion test workout"
        }
        
        response = requests.post(f"{BASE_URL}/workouts/sessions", 
                               headers=headers, json=session_data, timeout=10)
        
        if response.status_code != 200:
            log_test("Auto-Suggestion Feature - Create Session", False, 
                    f"Failed to create session - Status: {response.status_code}")
            return False
        
        result = response.json()
        session_id = result.get("session_id")
        if session_id:
            created_session_ids.append(session_id)
        
        # Step 2: Call GET /api/workouts/exercises/bench-press to check last_session
        response = requests.get(f"{BASE_URL}/workouts/exercises/bench-press", 
                              headers=headers, timeout=10)
        
        if response.status_code != 200:
            log_test("Auto-Suggestion Feature - Get Exercise", False, 
                    f"Failed to get exercise - Status: {response.status_code}")
            return False
        
        exercise = response.json()
        last_session = exercise.get("last_session")
        
        # CRITICAL: Verify last_session field exists and has correct structure
        if last_session is None:
            log_test("Auto-Suggestion Feature - last_session Field", False, 
                    "last_session field is null - auto-suggestion not working")
            return False
        
        # Verify last_session structure
        required_fields = ["exercise_id", "sets", "total_volume", "max_weight"]
        missing_fields = [field for field in required_fields if field not in last_session]
        
        if missing_fields:
            log_test("Auto-Suggestion Feature - Structure", False, 
                    f"Missing fields in last_session: {missing_fields}")
            return False
        
        # Verify data matches what we created
        if last_session.get("exercise_id") != "bench-press":
            log_test("Auto-Suggestion Feature - Exercise ID", False, 
                    f"Wrong exercise_id in last_session: {last_session.get('exercise_id')}")
            return False
        
        sets = last_session.get("sets", [])
        if len(sets) != 3:
            log_test("Auto-Suggestion Feature - Sets Count", False, 
                    f"Expected 3 sets in last_session, got {len(sets)}")
            return False
        
        # Verify volume calculation
        expected_volume = (10 * 60) + (8 * 70) + (6 * 80)  # 1640
        if last_session.get("total_volume") != expected_volume:
            log_test("Auto-Suggestion Feature - Volume", False, 
                    f"Volume mismatch. Expected: {expected_volume}, Got: {last_session.get('total_volume')}")
            return False
        
        # Verify max_weight
        if last_session.get("max_weight") != 80:
            log_test("Auto-Suggestion Feature - Max Weight", False, 
                    f"Max weight mismatch. Expected: 80, Got: {last_session.get('max_weight')}")
            return False
        
        # Step 3: Test exercise with NO previous sessions (should have null last_session)
        response = requests.get(f"{BASE_URL}/workouts/exercises/overhead-press", 
                              headers=headers, timeout=10)
        
        if response.status_code == 200:
            exercise_no_history = response.json()
            last_session_no_history = exercise_no_history.get("last_session")
            
            if last_session_no_history is not None:
                log_test("Auto-Suggestion Feature - No History", False, 
                        f"Expected null last_session for overhead-press, got: {last_session_no_history}")
                return False
        
        log_test("Auto-Suggestion Feature", True, 
                f"✅ AUTO-SUGGESTION working: last_session contains previous workout data "
                f"(3 sets, {expected_volume} volume, 80kg max)")
        return True
        
    except Exception as e:
        log_test("Auto-Suggestion Feature", False, f"Error: {str(e)}")
        return False

def test_edit_workout_session_endpoint():
    """Test NEW EDIT WORKOUT SESSION ENDPOINT - HIGHEST PRIORITY 1"""
    if not auth_token:
        log_test("Edit Workout Session", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        print("✏️ Testing NEW EDIT WORKOUT SESSION ENDPOINT (PUT /api/workouts/sessions/{session_id})...")
        
        # Step 1: Create a workout session first
        session_data = {
            "exercise_id": "bench-press",
            "sets": [
                {"reps": 10, "weight": 60, "rpe": 7},
                {"reps": 8, "weight": 70, "rpe": 8},
                {"reps": 6, "weight": 80, "rpe": 9}
            ],
            "notes": "Original session for edit test"
        }
        
        response = requests.post(f"{BASE_URL}/workouts/sessions", 
                               headers=headers, json=session_data, timeout=10)
        
        if response.status_code != 200:
            log_test("Edit Workout Session - Create", False, 
                    f"Failed to create session - Status: {response.status_code}")
            return False
        
        result = response.json()
        session_id = result.get("session_id")
        original_volume = result.get("total_volume")  # Should be 1640
        
        if not session_id:
            log_test("Edit Workout Session - Session ID", False, "No session_id returned")
            return False
        
        created_session_ids.append(session_id)
        
        # Step 2: Edit the session with different sets/weights
        edit_data = {
            "exercise_id": "bench-press",
            "sets": [
                {"reps": 12, "weight": 65, "rpe": 6},
                {"reps": 10, "weight": 70, "rpe": 7}
            ],
            "notes": "Edited session with different sets"
        }
        
        # CRITICAL: Test the NEW PUT endpoint
        response = requests.put(f"{BASE_URL}/workouts/sessions/{session_id}", 
                              headers=headers, json=edit_data, timeout=10)
        
        if response.status_code != 200:
            log_test("Edit Workout Session - PUT Request", False, 
                    f"PUT endpoint failed - Status: {response.status_code}, Response: {response.text}")
            return False
        
        edit_result = response.json()
        
        # Step 3: Verify volume recalculation
        new_volume = edit_result.get("total_volume")
        expected_new_volume = (12 * 65) + (10 * 70)  # 780 + 700 = 1480
        
        if new_volume != expected_new_volume:
            log_test("Edit Workout Session - Volume Recalculation", False, 
                    f"Volume not recalculated correctly. Expected: {expected_new_volume}, Got: {new_volume}")
            return False
        
        # Step 4: Verify max_weight recalculation
        new_max_weight = edit_result.get("max_weight", 0)
        expected_max_weight = 70  # Changed from 80 to 70
        
        if new_max_weight != expected_max_weight:
            log_test("Edit Workout Session - Max Weight Recalculation", False, 
                    f"Max weight not recalculated. Expected: {expected_max_weight}, Got: {new_max_weight}")
            return False
        
        # Step 5: Verify session was actually updated by fetching it
        response = requests.get(f"{BASE_URL}/workouts/sessions/{session_id}", 
                              headers=headers, timeout=10)
        
        if response.status_code == 200:
            updated_session = response.json()
            updated_sets = updated_session.get("sets", [])
            
            if len(updated_sets) != 2:
                log_test("Edit Workout Session - Sets Update", False, 
                        f"Sets not updated correctly. Expected 2 sets, got {len(updated_sets)}")
                return False
            
            if updated_session.get("notes") != "Edited session with different sets":
                log_test("Edit Workout Session - Notes Update", False, 
                        "Notes not updated correctly")
                return False
        
        log_test("Edit Workout Session - Basic Functionality", True, 
                f"✅ EDIT ENDPOINT working: Volume recalculated {original_volume}→{new_volume}, "
                f"Max weight {80}→{expected_max_weight}")
        
        # Step 6: Test EDGE CASES
        
        # Edge Case 1: Invalid session_id (should return 404)
        invalid_edit_data = {
            "exercise_id": "bench-press",
            "sets": [{"reps": 10, "weight": 60, "rpe": 7}],
            "notes": "Test"
        }
        
        response = requests.put(f"{BASE_URL}/workouts/sessions/invalid-session-id", 
                              headers=headers, json=invalid_edit_data, timeout=10)
        
        if response.status_code != 404:
            log_test("Edit Workout Session - Invalid ID", False, 
                    f"Expected 404 for invalid session_id, got {response.status_code}")
            return False
        
        # Edge Case 2: Try to edit with different exercise_id
        different_exercise_data = {
            "exercise_id": "squat",  # Different from original bench-press
            "sets": [{"reps": 10, "weight": 100, "rpe": 7}],
            "notes": "Different exercise"
        }
        
        response = requests.put(f"{BASE_URL}/workouts/sessions/{session_id}", 
                              headers=headers, json=different_exercise_data, timeout=10)
        
        # This should either fail or handle gracefully
        if response.status_code == 200:
            # If it allows changing exercise_id, verify it's handled correctly
            result = response.json()
            if result.get("exercise_id") != "squat":
                log_test("Edit Workout Session - Exercise Change", False, 
                        "Exercise ID change not handled correctly")
                return False
        
        # Edge Case 3: Empty sets array
        empty_sets_data = {
            "exercise_id": "bench-press",
            "sets": [],
            "notes": "Empty sets test"
        }
        
        response = requests.put(f"{BASE_URL}/workouts/sessions/{session_id}", 
                              headers=headers, json=empty_sets_data, timeout=10)
        
        # Should handle empty sets gracefully (either reject or set volume to 0)
        if response.status_code == 200:
            result = response.json()
            if result.get("total_volume", -1) != 0:
                log_test("Edit Workout Session - Empty Sets", False, 
                        f"Empty sets should result in 0 volume, got {result.get('total_volume')}")
                return False
        
        log_test("Edit Workout Session", True, 
                f"✅ NEW EDIT ENDPOINT fully functional: Volume/weight recalculation working, "
                f"Edge cases handled (404 for invalid ID, empty sets)")
        return True
        
    except Exception as e:
        log_test("Edit Workout Session", False, f"Error: {str(e)}")
        return False

def test_volume_stats_recalculation():
    """Test VOLUME & STATS RECALCULATION - PRIORITY 6"""
    if not auth_token:
        log_test("Volume Stats Recalculation", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        print("📊 Testing VOLUME & STATS RECALCULATION...")
        
        # Create session with specific sets as mentioned in review
        session_data = {
            "exercise_id": "squat",
            "sets": [
                {"reps": 10, "weight": 60, "rpe": 7},
                {"reps": 8, "weight": 70, "rpe": 8},
                {"reps": 6, "weight": 80, "rpe": 9}
            ],
            "notes": "Volume calculation test"
        }
        
        response = requests.post(f"{BASE_URL}/workouts/sessions", 
                               headers=headers, json=session_data, timeout=10)
        
        if response.status_code != 200:
            log_test("Volume Stats Recalculation - Create", False, 
                    f"Failed to create session - Status: {response.status_code}")
            return False
        
        result = response.json()
        session_id = result.get("session_id")
        original_volume = result.get("total_volume")
        
        # Verify original calculation: 10x60 + 8x70 + 6x80 = 600 + 560 + 480 = 1640
        expected_original_volume = (10 * 60) + (8 * 70) + (6 * 80)  # 1640
        
        if original_volume != expected_original_volume:
            log_test("Volume Stats Recalculation - Original", False, 
                    f"Original volume incorrect. Expected: {expected_original_volume}, Got: {original_volume}")
            return False
        
        created_session_ids.append(session_id)
        
        # Edit session to 2 sets as mentioned in review: 12x65kg, 10x70kg
        edit_data = {
            "exercise_id": "squat",
            "sets": [
                {"reps": 12, "weight": 65, "rpe": 6},
                {"reps": 10, "weight": 70, "rpe": 7}
            ],
            "notes": "Edited for volume recalculation test"
        }
        
        response = requests.put(f"{BASE_URL}/workouts/sessions/{session_id}", 
                              headers=headers, json=edit_data, timeout=10)
        
        if response.status_code != 200:
            log_test("Volume Stats Recalculation - Edit", False, 
                    f"Edit failed - Status: {response.status_code}")
            return False
        
        edit_result = response.json()
        new_volume = edit_result.get("total_volume")
        new_max_weight = edit_result.get("max_weight", 0)
        
        # Verify recalculation: 12x65 + 10x70 = 780 + 700 = 1480
        expected_new_volume = (12 * 65) + (10 * 70)  # 1480
        
        if new_volume != expected_new_volume:
            log_test("Volume Stats Recalculation - New Volume", False, 
                    f"Volume recalculation incorrect. Expected: {expected_new_volume}, Got: {new_volume}")
            return False
        
        # Verify max_weight updates from 80kg to 70kg
        if new_max_weight != 70:
            log_test("Volume Stats Recalculation - Max Weight", False, 
                    f"Max weight recalculation incorrect. Expected: 70, Got: {new_max_weight}")
            return False
        
        # Verify GET /api/workouts/dashboard/stats reflects the updated volume
        response = requests.get(f"{BASE_URL}/workouts/dashboard/stats", headers=headers, timeout=10)
        
        if response.status_code == 200:
            dashboard_stats = response.json()
            total_volume_lifted = dashboard_stats.get("total_volume_lifted", 0)
            
            # Should include our updated volume
            if total_volume_lifted < expected_new_volume:
                log_test("Volume Stats Recalculation - Dashboard", False, 
                        f"Dashboard stats not updated. Total volume: {total_volume_lifted}")
                return False
        
        log_test("Volume Stats Recalculation", True, 
                f"✅ VOLUME RECALCULATION working: {expected_original_volume}→{expected_new_volume}, "
                f"Max weight: 80→70, Dashboard stats updated")
        return True
        
    except Exception as e:
        log_test("Volume Stats Recalculation", False, f"Error: {str(e)}")
        return False

def test_edge_cases_error_handling():
    """Test EDGE CASES & ERROR HANDLING - PRIORITY 5"""
    if not auth_token:
        log_test("Edge Cases Error Handling", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        print("⚠️ Testing EDGE CASES & ERROR HANDLING...")
        
        # Test 1: Invalid category name
        response = requests.get(f"{BASE_URL}/workouts/exercises?category=InvalidCategory", 
                              headers=headers, timeout=10)
        
        # Should return empty list or handle gracefully
        if response.status_code == 200:
            data = response.json()
            exercises = data.get("exercises", [])
            if len(exercises) > 0:
                log_test("Edge Cases - Invalid Category", False, 
                        f"Invalid category returned {len(exercises)} exercises instead of 0")
                return False
        elif response.status_code not in [400, 404]:
            log_test("Edge Cases - Invalid Category", False, 
                    f"Unexpected status for invalid category: {response.status_code}")
            return False
        
        # Test 2: Invalid exercise_id
        response = requests.get(f"{BASE_URL}/workouts/exercises/invalid-exercise-id", 
                              headers=headers, timeout=10)
        
        if response.status_code != 404:
            log_test("Edge Cases - Invalid Exercise ID", False, 
                    f"Expected 404 for invalid exercise_id, got {response.status_code}")
            return False
        
        # Test 3: DELETE session then try to edit it
        if created_session_ids:
            session_to_delete = created_session_ids[0]
            
            # Delete the session
            response = requests.delete(f"{BASE_URL}/workouts/sessions/{session_to_delete}", 
                                     headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Try to edit the deleted session
                edit_data = {
                    "exercise_id": "bench-press",
                    "sets": [{"reps": 10, "weight": 60, "rpe": 7}],
                    "notes": "Should fail"
                }
                
                response = requests.put(f"{BASE_URL}/workouts/sessions/{session_to_delete}", 
                                      headers=headers, json=edit_data, timeout=10)
                
                if response.status_code != 404:
                    log_test("Edge Cases - Edit Deleted Session", False, 
                            f"Expected 404 for editing deleted session, got {response.status_code}")
                    return False
        
        # Test 4: Try to access another user's session (simulate with invalid session ID)
        fake_session_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{BASE_URL}/workouts/sessions/{fake_session_id}", 
                              headers=headers, timeout=10)
        
        if response.status_code != 404:
            log_test("Edge Cases - Wrong User Session", False, 
                    f"Expected 404 for wrong user session, got {response.status_code}")
            return False
        
        # Test 5: Invalid data in session creation
        invalid_session_data = {
            "exercise_id": "bench-press",
            "sets": [
                {"reps": -5, "weight": -10, "rpe": 15}  # Invalid values
            ],
            "notes": "Invalid data test"
        }
        
        response = requests.post(f"{BASE_URL}/workouts/sessions", 
                               headers=headers, json=invalid_session_data, timeout=10)
        
        # Should either reject or sanitize the data
        if response.status_code == 200:
            result = response.json()
            # If it accepts the data, verify it's handled appropriately
            if result.get("total_volume", 0) < 0:
                log_test("Edge Cases - Invalid Data", False, 
                        "Negative volume allowed with invalid data")
                return False
        
        log_test("Edge Cases Error Handling", True, 
                f"✅ ERROR HANDLING working: Invalid category/exercise (404), "
                f"Deleted session edit (404), Invalid data handled")
        return True
        
    except Exception as e:
        log_test("Edge Cases Error Handling", False, f"Error: {str(e)}")
        return False

def run_comprehensive_workout_tests():
    """Run all comprehensive workout tracking tests"""
    print("🏋️‍♂️ STARTING COMPREHENSIVE WORKOUT TRACKING BACKEND TESTING")
    print("=" * 80)
    print("Focus: NEW untested features as specified in review request")
    print("Backend URL:", BASE_URL)
    print("Test User:", TEST_USER_EMAIL)
    print("=" * 80)
    
    # Login first
    if not login_user():
        print("❌ CRITICAL: Login failed - cannot proceed with tests")
        return
    
    # Run tests in priority order
    tests = [
        ("1. NEW EDIT WORKOUT SESSION ENDPOINT (HIGHEST PRIORITY)", test_edit_workout_session_endpoint),
        ("2. EXPANDED EXERCISE LIBRARY (35+ exercises)", test_expanded_exercise_library),
        ("3. REAL UNSPLASH IMAGES VERIFICATION", test_real_unsplash_images),
        ("4. AUTO-SUGGESTION FEATURE (last_session field)", test_auto_suggestion_feature),
        ("5. EDGE CASES & ERROR HANDLING", test_edge_cases_error_handling),
        ("6. VOLUME & STATS RECALCULATION", test_volume_stats_recalculation)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 60)
        
        try:
            if test_func():
                passed_tests += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("🏁 COMPREHENSIVE WORKOUT TESTING COMPLETE")
    print("=" * 80)
    print(f"✅ PASSED: {passed_tests}/{total_tests} tests")
    print(f"❌ FAILED: {total_tests - passed_tests}/{total_tests} tests")
    
    if passed_tests == total_tests:
        print("🎉 ALL NEW WORKOUT FEATURES WORKING PERFECTLY!")
    else:
        print("⚠️  Some tests failed - see details above")
    
    print("\nDetailed Results:")
    for test_name, result in test_results.items():
        status = "✅" if result["success"] else "❌"
        print(f"{status} {test_name}: {result['message']}")

if __name__ == "__main__":
    run_comprehensive_workout_tests()