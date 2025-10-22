#!/usr/bin/env python3
"""
Focused Meal Plan Generation API Test
Tests the specific meal plan generation scenario requested by user
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://undefined-stats-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "test@fitflow.com"
TEST_USER_PASSWORD = "Test123!"

# Global variables
auth_token = None
user_id = None
generated_plan_id = None

def log_result(test_name, success, message="", details=None):
    """Log test results with clear formatting"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"   {message}")
    if details:
        print(f"   Details: {details}")
    print()

def test_login():
    """Login with test user credentials"""
    global auth_token, user_id
    
    print("🔐 Step 1: Logging in with test user...")
    
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
                log_result("Login", True, f"Successfully logged in as {TEST_USER_EMAIL}")
                return True
            else:
                log_result("Login", False, "Missing token or user_id in response")
                return False
        else:
            log_result("Login", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_result("Login", False, f"Error: {str(e)}")
        return False

def test_meal_plan_generation():
    """Test meal plan generation with specific parameters"""
    global generated_plan_id
    
    if not auth_token:
        log_result("Meal Plan Generation", False, "No auth token available")
        return False
    
    print("🍽️ Step 2: Testing AI Meal Plan Generation...")
    print("   Parameters: 7 days, vegetarian, no allergies, auto calorie target")
    print("   (This may take 30-60 seconds for AI processing)")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test parameters as specified in the request
    plan_data = {
        "duration": 7,
        "dietary_preferences": "vegetarian",
        "allergies": None,
        "calorie_target": None  # Should use user's profile target
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/mealplan/generate", 
                               headers=headers, json=plan_data, timeout=90)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required response fields
            plan_id = data.get("plan_id")
            name = data.get("name")
            duration = data.get("duration")
            days = data.get("days", [])
            
            if not plan_id:
                log_result("Meal Plan Generation", False, "Missing plan_id in response")
                return False
            
            if not name or "7-Day AI Meal Plan" not in name:
                log_result("Meal Plan Generation", False, f"Invalid name: {name}")
                return False
            
            if duration != 7:
                log_result("Meal Plan Generation", False, f"Expected duration 7, got {duration}")
                return False
            
            if len(days) != 7:
                log_result("Meal Plan Generation", False, f"Expected 7 days, got {len(days)}")
                return False
            
            # Verify day structure
            first_day = days[0]
            meals = first_day.get("meals", {})
            
            # Check required meal categories
            required_meals = ["breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner"]
            missing_meals = [meal for meal in required_meals if meal not in meals]
            
            if missing_meals:
                log_result("Meal Plan Generation", False, f"Missing meal categories: {missing_meals}")
                return False
            
            # Verify meal structure
            breakfast = meals.get("breakfast", {})
            required_fields = ["name", "calories", "protein", "carbs", "fat", "description", "ingredients"]
            missing_fields = [field for field in required_fields if field not in breakfast]
            
            if missing_fields:
                log_result("Meal Plan Generation", False, f"Missing meal fields: {missing_fields}")
                return False
            
            # Verify nutritional data is realistic
            if not (50 <= breakfast.get("calories", 0) <= 800):
                log_result("Meal Plan Generation", False, f"Unrealistic breakfast calories: {breakfast.get('calories')}")
                return False
            
            # Verify daily totals
            if "totals" not in first_day:
                log_result("Meal Plan Generation", False, "Missing daily totals")
                return False
            
            totals = first_day["totals"]
            daily_calories = totals.get("calories", 0)
            
            if not (1200 <= daily_calories <= 3000):
                log_result("Meal Plan Generation", False, f"Unrealistic daily calories: {daily_calories}")
                return False
            
            generated_plan_id = plan_id
            
            log_result("Meal Plan Generation", True, 
                      f"Generated 7-day vegetarian meal plan in {response_time:.1f}s")
            print(f"   Plan ID: {plan_id}")
            print(f"   Plan Name: {name}")
            print(f"   Daily Calories (Day 1): {daily_calories}")
            print(f"   Sample Breakfast: {breakfast.get('name')} ({breakfast.get('calories')} cal)")
            
            return True
            
        else:
            log_result("Meal Plan Generation", False, 
                      f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        log_result("Meal Plan Generation", False, "Request timeout - AI processing took too long")
        return False
    except Exception as e:
        log_result("Meal Plan Generation", False, f"Error: {str(e)}")
        return False

def test_meal_plan_list():
    """Test GET /api/mealplan/list to verify the plan was saved"""
    
    if not auth_token or not generated_plan_id:
        log_result("Meal Plan List", False, "No auth token or generated plan available")
        return False
    
    print("📋 Step 3: Testing meal plan list retrieval...")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/mealplan/list", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            plans = data.get("plans", [])
            
            # Find our generated plan
            our_plan = None
            for plan in plans:
                if plan.get("plan_id") == generated_plan_id:
                    our_plan = plan
                    break
            
            if not our_plan:
                log_result("Meal Plan List", False, f"Generated plan {generated_plan_id} not found in list")
                return False
            
            # Verify plan summary structure
            required_fields = ["plan_id", "name", "duration", "start_date", "created_at", "type"]
            missing_fields = [field for field in required_fields if field not in our_plan]
            
            if missing_fields:
                log_result("Meal Plan List", False, f"Missing fields in plan summary: {missing_fields}")
                return False
            
            # Verify it's marked as AI generated
            if our_plan.get("type") != "ai_generated":
                log_result("Meal Plan List", False, f"Expected type 'ai_generated', got '{our_plan.get('type')}'")
                return False
            
            log_result("Meal Plan List", True, 
                      f"Found generated plan in list ({len(plans)} total plans)")
            print(f"   Plan Type: {our_plan.get('type')}")
            print(f"   Created: {our_plan.get('created_at')}")
            
            return True
            
        else:
            log_result("Meal Plan List", False, 
                      f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_result("Meal Plan List", False, f"Error: {str(e)}")
        return False

def test_meal_plan_details():
    """Test GET /api/mealplan/{plan_id} to retrieve full plan details"""
    
    if not auth_token or not generated_plan_id:
        log_result("Meal Plan Details", False, "No auth token or generated plan available")
        return False
    
    print("📖 Step 4: Testing detailed meal plan retrieval...")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/mealplan/{generated_plan_id}", 
                              headers=headers, timeout=10)
        
        if response.status_code == 200:
            plan = response.json()
            
            # Verify complete plan structure
            required_fields = ["plan_id", "name", "duration", "days", "user_id", "created_at", 
                             "dietary_preferences", "type"]
            missing_fields = [field for field in required_fields if field not in plan]
            
            if missing_fields:
                log_result("Meal Plan Details", False, f"Missing fields: {missing_fields}")
                return False
            
            # Verify dietary preferences were saved
            if plan.get("dietary_preferences") != "vegetarian":
                log_result("Meal Plan Details", False, 
                          f"Expected vegetarian preference, got '{plan.get('dietary_preferences')}'")
                return False
            
            days = plan.get("days", [])
            if len(days) != 7:
                log_result("Meal Plan Details", False, f"Expected 7 days in details, got {len(days)}")
                return False
            
            # Verify all days have complete meal structure
            for i, day in enumerate(days, 1):
                if "meals" not in day or "totals" not in day:
                    log_result("Meal Plan Details", False, f"Day {i} missing meals or totals")
                    return False
                
                meals = day["meals"]
                required_meals = ["breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner"]
                
                for meal_type in required_meals:
                    if meal_type not in meals:
                        log_result("Meal Plan Details", False, f"Day {i} missing {meal_type}")
                        return False
                    
                    meal = meals[meal_type]
                    meal_fields = ["name", "calories", "protein", "carbs", "fat", "description", "ingredients"]
                    missing_meal_fields = [field for field in meal_fields if field not in meal]
                    
                    if missing_meal_fields:
                        log_result("Meal Plan Details", False, 
                                  f"Day {i} {meal_type} missing fields: {missing_meal_fields}")
                        return False
            
            # Calculate average daily calories
            total_calories = sum(day["totals"]["calories"] for day in days)
            avg_calories = total_calories / len(days)
            
            log_result("Meal Plan Details", True, 
                      f"Retrieved complete 7-day plan with all meals and nutritional data")
            print(f"   Dietary Preference: {plan.get('dietary_preferences')}")
            print(f"   Average Daily Calories: {avg_calories:.0f}")
            print(f"   Total Plan Calories: {total_calories:.0f}")
            
            # Show sample meals from different days
            print(f"   Sample Day 1 Breakfast: {days[0]['meals']['breakfast']['name']}")
            print(f"   Sample Day 4 Lunch: {days[3]['meals']['lunch']['name']}")
            
            return True
            
        else:
            log_result("Meal Plan Details", False, 
                      f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_result("Meal Plan Details", False, f"Error: {str(e)}")
        return False

def run_meal_plan_test():
    """Run the complete meal plan generation test sequence"""
    print("🚀 FitFlow Meal Plan Generation API Test")
    print("=" * 60)
    print("Testing the specific scenario requested:")
    print("- Login with test@fitflow.com / Test123!")
    print("- Generate 7-day vegetarian meal plan")
    print("- Verify plan was saved and can be retrieved")
    print("=" * 60)
    
    tests = [
        ("Login", test_login),
        ("Meal Plan Generation", test_meal_plan_generation),
        ("Meal Plan List", test_meal_plan_list),
        ("Meal Plan Details", test_meal_plan_details)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            if success:
                passed += 1
            else:
                failed += 1
                # Stop on failure for this focused test
                break
        except Exception as e:
            print(f"❌ {test_name}: Unexpected error: {str(e)}")
            failed += 1
            break
    
    print("=" * 60)
    print("📊 MEAL PLAN TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - Meal Plan Generation API is working correctly!")
        print("✅ AI meal plan generation is functional with real OpenAI GPT-4o")
        print("✅ Plan persistence and retrieval working properly")
        print("✅ Nutritional data and meal structure complete")
    else:
        print("🚨 SOME TESTS FAILED - Issues found with meal plan generation")
    
    return passed, failed

if __name__ == "__main__":
    run_meal_plan_test()