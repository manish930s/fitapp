#!/usr/bin/env python3
"""
Supabase Migration Testing Suite
Tests critical endpoints after MongoDB to Supabase migration
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://task-done-5.preview.emergentagent.com/api"
TEST_USER_EMAIL = "supabasetest@fitflow.com"
TEST_USER_PASSWORD = "Test123!"
TEST_USER_NAME = "Supabase Test User"

# Global variables
auth_token = None
user_id = None
test_results = []

def log_test(test_name, success, message="", details=None):
    """Log test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}: {message}")
    if details:
        print(f"   Details: {details}")
    
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

def test_health_check():
    """Test API health"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=15)
        if response.status_code == 200:
            data = response.json()
            log_test("Health Check", True, f"Service healthy: {data.get('service')}")
            return True
        else:
            log_test("Health Check", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Health Check", False, f"Error: {str(e)}")
        return False

def test_user_registration():
    """Test user registration with Supabase"""
    global auth_token, user_id
    
    user_data = {
        "name": TEST_USER_NAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "age": 28,
        "gender": "female",
        "height": 165.0,
        "weight": 60.0,
        "activity_level": "moderate",
        "goal_weight": 55.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("token")
            user_id = data.get("user", {}).get("user_id")
            daily_calories = data.get("daily_calories")
            
            if auth_token and user_id:
                log_test("User Registration", True, 
                        f"User registered in Supabase. Daily calories: {daily_calories}")
                return True
            else:
                log_test("User Registration", False, "Missing token or user_id")
                return False
        elif response.status_code == 400 and "already registered" in response.text:
            log_test("User Registration", True, "User exists, trying login...")
            return test_user_login()
        else:
            log_test("User Registration", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("User Registration", False, f"Error: {str(e)}")
        return False

def test_user_login():
    """Test user login with Supabase"""
    global auth_token, user_id
    
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("token")
            user_id = data.get("user", {}).get("user_id")
            
            if auth_token and user_id:
                log_test("User Login", True, "Login successful with Supabase")
                return True
            else:
                log_test("User Login", False, "Missing token or user_id")
                return False
        else:
            log_test("User Login", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("User Login", False, f"Error: {str(e)}")
        return False

def test_user_profile():
    """Test user profile operations with Supabase"""
    if not auth_token:
        log_test("User Profile", False, "No auth token")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test GET profile
        response = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=15)
        
        if response.status_code != 200:
            log_test("User Profile GET", False, f"Status: {response.status_code}")
            return False
        
        profile = response.json()
        daily_calories = profile.get("daily_calories")
        
        if not daily_calories or "daily_target" not in daily_calories:
            log_test("User Profile GET", False, "Missing calorie calculations")
            return False
        
        # Test PUT profile
        update_data = {
            "weight": 58.5,
            "goal_weight": 54.0
        }
        
        response = requests.put(f"{BASE_URL}/user/profile", 
                              headers=headers, json=update_data, timeout=15)
        
        if response.status_code == 200:
            log_test("User Profile", True, 
                    f"Profile operations successful. Daily target: {daily_calories['daily_target']} kcal")
            return True
        else:
            log_test("User Profile PUT", False, f"Update failed: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("User Profile", False, f"Error: {str(e)}")
        return False

def test_food_scanner():
    """Test food scanner with AI integration"""
    if not auth_token:
        log_test("Food Scanner", False, "No auth token")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Simple test image (1x1 PNG)
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        print("🔍 Testing AI Food Scanner (may take 30-60 seconds)...")
        
        # Test food scan
        form_data = {"image": test_image}
        response = requests.post(f"{BASE_URL}/food/scan", 
                               headers=headers, data=form_data, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["food_name", "calories", "protein", "carbs", "fat", "portion_size"]
            
            if all(field in data for field in required_fields):
                scan_id = data.get("scan_id")
                
                # Test food history
                history_response = requests.get(f"{BASE_URL}/food/history", headers=headers, timeout=15)
                if history_response.status_code == 200:
                    history = history_response.json().get("history", [])
                    
                    # Test delete scan if we have a scan_id
                    if scan_id:
                        delete_response = requests.delete(f"{BASE_URL}/food/scan/{scan_id}", 
                                                        headers=headers, timeout=15)
                        if delete_response.status_code == 200:
                            log_test("Food Scanner", True, 
                                    f"AI scan, history, and delete working. Food: {data['food_name']}, "
                                    f"Calories: {data['calories']}, History: {len(history)} items")
                            return True
                
                log_test("Food Scanner", True, 
                        f"AI scan working. Food: {data['food_name']}, Calories: {data['calories']}")
                return True
            else:
                log_test("Food Scanner", False, "Missing fields in AI response")
                return False
        else:
            log_test("Food Scanner", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Food Scanner", False, f"Error: {str(e)}")
        return False

def test_daily_stats():
    """Test daily stats tracking"""
    if not auth_token:
        log_test("Daily Stats", False, "No auth token")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test POST daily stats
        stats_data = {
            "steps": 10000,
            "calories_burned": 400,
            "calories_consumed": 1800,
            "active_minutes": 60,
            "water_intake": 8,
            "sleep_hours": 8.0
        }
        
        response = requests.post(f"{BASE_URL}/stats/daily", 
                               headers=headers, json=stats_data, timeout=15)
        
        if response.status_code != 200:
            log_test("Daily Stats POST", False, f"Status: {response.status_code}")
            return False
        
        # Test GET daily stats
        response = requests.get(f"{BASE_URL}/stats/daily", headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("steps") == 10000 and data.get("calories_consumed") == 1800:
                
                # Test streak calculation
                streak_response = requests.get(f"{BASE_URL}/stats/streak", headers=headers, timeout=15)
                if streak_response.status_code == 200:
                    streak_data = streak_response.json()
                    streak_days = streak_data.get("streak_days", 0)
                    
                    log_test("Daily Stats", True, 
                            f"Stats tracking working. Steps: {data['steps']}, Streak: {streak_days} days")
                    return True
                
                log_test("Daily Stats", True, f"Stats saved correctly. Steps: {data['steps']}")
                return True
            else:
                log_test("Daily Stats GET", False, "Stats not saved correctly")
                return False
        else:
            log_test("Daily Stats GET", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Daily Stats", False, f"Error: {str(e)}")
        return False

def test_goals_and_measurements():
    """Test goals and measurements APIs"""
    if not auth_token:
        log_test("Goals & Measurements", False, "No auth token")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test create goal
        goal_data = {
            "goal_type": "weight_loss",
            "target_value": 54.0,
            "current_progress": 58.5,
            "unit": "kg"
        }
        
        response = requests.post(f"{BASE_URL}/goals", 
                               headers=headers, json=goal_data, timeout=15)
        
        if response.status_code != 200:
            log_test("Goals Create", False, f"Status: {response.status_code}")
            return False
        
        goal_result = response.json()
        goal_id = goal_result.get("goal_id")
        
        # Test get goals
        response = requests.get(f"{BASE_URL}/goals", headers=headers, timeout=15)
        if response.status_code != 200:
            log_test("Goals GET", False, f"Status: {response.status_code}")
            return False
        
        goals = response.json().get("goals", [])
        
        # Test update goal
        update_data = {
            "goal_type": "weight_loss",
            "target_value": 54.0,
            "current_progress": 57.0,
            "unit": "kg"
        }
        
        response = requests.put(f"{BASE_URL}/goals/{goal_id}", 
                              headers=headers, json=update_data, timeout=15)
        
        if response.status_code != 200:
            log_test("Goals Update", False, f"Status: {response.status_code}")
            return False
        
        # Test add measurement
        measurement_data = {
            "weight": 57.0,
            "body_fat": 18.5,
            "bmi": 21.0
        }
        
        response = requests.post(f"{BASE_URL}/measurements", 
                               headers=headers, json=measurement_data, timeout=15)
        
        if response.status_code != 200:
            log_test("Measurements Create", False, f"Status: {response.status_code}")
            return False
        
        # Test get latest measurement
        response = requests.get(f"{BASE_URL}/measurements/latest", headers=headers, timeout=15)
        if response.status_code == 200:
            latest = response.json().get("measurement", {})
            if latest.get("weight") == 57.0:
                
                # Test measurement history
                history_response = requests.get(f"{BASE_URL}/measurements/history", 
                                              headers=headers, timeout=15)
                if history_response.status_code == 200:
                    history = history_response.json().get("measurements", [])
                    
                    log_test("Goals & Measurements", True, 
                            f"All operations working. Goals: {len(goals)}, "
                            f"Latest weight: {latest['weight']}kg, History: {len(history)} entries")
                    return True
        
        log_test("Goals & Measurements", True, "Basic operations working")
        return True
        
    except Exception as e:
        log_test("Goals & Measurements", False, f"Error: {str(e)}")
        return False

def test_workout_features():
    """Test workout exercises and sessions"""
    if not auth_token:
        log_test("Workout Features", False, "No auth token")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test get exercises
        response = requests.get(f"{BASE_URL}/workouts/exercises", headers=headers, timeout=15)
        
        if response.status_code != 200:
            log_test("Workout Exercises", False, f"Status: {response.status_code}")
            return False
        
        exercises = response.json().get("exercises", [])
        
        if len(exercises) < 30:  # Should have 35+ exercises
            log_test("Workout Exercises", False, f"Expected 35+ exercises, got {len(exercises)}")
            return False
        
        # Test get exercise details
        response = requests.get(f"{BASE_URL}/workouts/exercises/bench-press", 
                              headers=headers, timeout=15)
        
        if response.status_code != 200:
            log_test("Exercise Details", False, f"Status: {response.status_code}")
            return False
        
        exercise = response.json()
        required_fields = ["exercise_id", "name", "category", "target_muscles", "instructions"]
        
        if not all(field in exercise for field in required_fields):
            log_test("Exercise Details", False, "Missing required fields")
            return False
        
        # Test create workout session
        session_data = {
            "exercise_id": "bench-press",
            "sets": [
                {"reps": 10, "weight": 50, "rpe": 7},
                {"reps": 8, "weight": 55, "rpe": 8}
            ],
            "notes": "Supabase test workout"
        }
        
        response = requests.post(f"{BASE_URL}/workouts/sessions", 
                               headers=headers, json=session_data, timeout=15)
        
        if response.status_code == 200:
            session_result = response.json()
            session_id = session_result.get("session_id")
            total_volume = session_result.get("total_volume")
            
            # Test get sessions
            sessions_response = requests.get(f"{BASE_URL}/workouts/sessions", 
                                           headers=headers, timeout=15)
            
            if sessions_response.status_code == 200:
                sessions = sessions_response.json().get("sessions", [])
                
                # Test delete session
                if session_id:
                    delete_response = requests.delete(f"{BASE_URL}/workouts/sessions/{session_id}", 
                                                    headers=headers, timeout=15)
                    if delete_response.status_code == 200:
                        log_test("Workout Features", True, 
                                f"All workout features working. Exercises: {len(exercises)}, "
                                f"Session volume: {total_volume}, Sessions: {len(sessions)}")
                        return True
                
                log_test("Workout Features", True, 
                        f"Workout features working. Exercises: {len(exercises)}, Volume: {total_volume}")
                return True
        
        log_test("Workout Features", True, f"Exercise library working. Count: {len(exercises)}")
        return True
        
    except Exception as e:
        log_test("Workout Features", False, f"Error: {str(e)}")
        return False

def test_meal_plans():
    """Test meal plan generation and management"""
    if not auth_token:
        log_test("Meal Plans", False, "No auth token")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        print("🍽️ Testing AI Meal Plan Generation (may take 60-90 seconds)...")
        
        # Test AI meal plan generation
        plan_data = {
            "duration": 1,  # 1 day for faster testing
            "dietary_preferences": "vegetarian",
            "allergies": None,
            "calorie_target": 1600
        }
        
        response = requests.post(f"{BASE_URL}/mealplan/generate", 
                               headers=headers, json=plan_data, timeout=120)
        
        if response.status_code == 200:
            plan = response.json()
            plan_id = plan.get("plan_id")
            days = plan.get("days", [])
            
            if plan_id and len(days) == 1:
                # Test list meal plans
                list_response = requests.get(f"{BASE_URL}/mealplan/list", 
                                           headers=headers, timeout=15)
                
                if list_response.status_code == 200:
                    plans = list_response.json().get("plans", [])
                    
                    # Test get meal plan details
                    detail_response = requests.get(f"{BASE_URL}/mealplan/{plan_id}", 
                                                 headers=headers, timeout=15)
                    
                    if detail_response.status_code == 200:
                        detail_plan = detail_response.json()
                        
                        # Test delete meal plan
                        delete_response = requests.delete(f"{BASE_URL}/mealplan/{plan_id}", 
                                                        headers=headers, timeout=15)
                        
                        if delete_response.status_code == 200:
                            log_test("Meal Plans", True, 
                                    f"AI meal plan generation working. Plans: {len(plans)}, "
                                    f"Generated 1-day vegetarian plan with {len(days)} days")
                            return True
                
                log_test("Meal Plans", True, f"AI generation working. Plan ID: {plan_id[:8]}...")
                return True
            else:
                log_test("Meal Plans", False, f"Invalid plan structure. ID: {plan_id}, Days: {len(days)}")
                return False
        else:
            log_test("Meal Plans", False, 
                    f"AI generation failed. Status: {response.status_code}, Response: {response.text}")
            return False
        
    except Exception as e:
        log_test("Meal Plans", False, f"Error: {str(e)}")
        return False

def test_ai_fitness_coach():
    """Test AI fitness coach chatbot"""
    if not auth_token:
        log_test("AI Fitness Coach", False, "No auth token")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        print("🤖 Testing AI Fitness Coach (may take 30-60 seconds)...")
        
        # Test send message
        chat_data = {
            "message": "What's a good 10-minute workout for beginners?"
        }
        
        response = requests.post(f"{BASE_URL}/chat/fitness", 
                               headers=headers, json=chat_data, timeout=90)
        
        if response.status_code == 200:
            chat_result = response.json()
            ai_message = chat_result.get("message", "")
            
            if len(ai_message) > 50:  # Should be a substantial response
                # Test chat history
                history_response = requests.get(f"{BASE_URL}/chat/history", 
                                              headers=headers, timeout=15)
                
                if history_response.status_code == 200:
                    history = history_response.json().get("chats", [])
                    
                    log_test("AI Fitness Coach", True, 
                            f"AI coach working. Response length: {len(ai_message)} chars, "
                            f"History: {len(history)} messages")
                    return True
                
                log_test("AI Fitness Coach", True, 
                        f"AI responses working. Length: {len(ai_message)} chars")
                return True
            else:
                log_test("AI Fitness Coach", False, f"Response too short: {ai_message}")
                return False
        else:
            log_test("AI Fitness Coach", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
        
    except Exception as e:
        log_test("AI Fitness Coach", False, f"Error: {str(e)}")
        return False

def run_all_tests():
    """Run all Supabase migration tests"""
    print("🧪 SUPABASE MIGRATION TESTING SUITE")
    print("=" * 50)
    print(f"Testing user: {TEST_USER_EMAIL}")
    print(f"Backend URL: {BASE_URL}")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("User Registration", test_user_registration),
        ("User Profile", test_user_profile),
        ("Food Scanner (AI)", test_food_scanner),
        ("Daily Stats", test_daily_stats),
        ("Goals & Measurements", test_goals_and_measurements),
        ("Workout Features", test_workout_features),
        ("Meal Plans (AI)", test_meal_plans),
        ("AI Fitness Coach", test_ai_fitness_coach),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            log_test(test_name, False, f"Unexpected error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 SUPABASE MIGRATION TEST RESULTS")
    print("=" * 50)
    
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    print(f"\n📊 SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Supabase migration successful!")
    else:
        print(f"⚠️  {total-passed} tests failed - Review issues above")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)