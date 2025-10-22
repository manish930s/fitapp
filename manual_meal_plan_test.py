#!/usr/bin/env python3
"""
Manual Meal Plan Creation Testing Suite for FitFlow
Tests the POST /api/mealplan/create endpoint with comprehensive scenarios
"""

import requests
import json
import time
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "https://undefined-stats-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "test@fitflow.com"
TEST_USER_PASSWORD = "Test123!"

# Global variables
auth_token = None
user_id = None
created_plan_ids = []

def log_test(test_name, success, message="", details=None):
    """Log test results with detailed output"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"   {message}")
    if details:
        print(f"   Details: {details}")
    print()

def authenticate():
    """Authenticate and get JWT token"""
    global auth_token, user_id
    
    print("🔐 Authenticating with test credentials...")
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
                log_test("Authentication", True, f"Successfully logged in as {TEST_USER_EMAIL}")
                return True
            else:
                log_test("Authentication", False, "Missing token or user_id in response")
                return False
        else:
            log_test("Authentication", False, f"Login failed - Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Authentication", False, f"Authentication error: {str(e)}")
        return False

def test_manual_meal_plan_basic():
    """Test basic manual meal plan creation with 3 days"""
    if not auth_token:
        log_test("Manual Meal Plan - Basic", False, "No authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create a 3-day manual meal plan with realistic data
    manual_plan_data = {
        "name": "My Manual Meal Plan",
        "duration": 3,
        "start_date": "2025-02-01",
        "days": [
            {
                "day": 1,
                "meals": {
                    "breakfast": {
                        "name": "Oatmeal with Berries",
                        "calories": 350,
                        "protein": 12,
                        "carbs": 60,
                        "fat": 8,
                        "description": "Healthy breakfast with rolled oats, mixed berries, and milk",
                        "ingredients": ["oats", "berries", "milk", "honey"]
                    },
                    "morning_snack": {
                        "name": "",
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    },
                    "lunch": {
                        "name": "Grilled Chicken Salad",
                        "calories": 450,
                        "protein": 35,
                        "carbs": 30,
                        "fat": 18,
                        "description": "Fresh salad with grilled chicken breast",
                        "ingredients": ["chicken breast", "mixed greens", "tomatoes", "cucumber", "olive oil"]
                    },
                    "afternoon_snack": {
                        "name": "",
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    },
                    "dinner": {
                        "name": "Salmon with Vegetables",
                        "calories": 500,
                        "protein": 40,
                        "carbs": 35,
                        "fat": 22,
                        "description": "Baked salmon with roasted vegetables",
                        "ingredients": ["salmon fillet", "broccoli", "carrots", "sweet potato"]
                    }
                }
            },
            {
                "day": 2,
                "meals": {
                    "breakfast": {
                        "name": "Scrambled Eggs",
                        "calories": 300,
                        "protein": 20,
                        "carbs": 5,
                        "fat": 15,
                        "description": "Fluffy scrambled eggs with herbs",
                        "ingredients": ["eggs", "butter", "chives", "salt", "pepper"]
                    },
                    "morning_snack": {
                        "name": "",
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    },
                    "lunch": {
                        "name": "Turkey Sandwich",
                        "calories": 400,
                        "protein": 25,
                        "carbs": 45,
                        "fat": 12,
                        "description": "Whole grain turkey sandwich with vegetables",
                        "ingredients": ["whole grain bread", "turkey slices", "lettuce", "tomato", "mustard"]
                    },
                    "afternoon_snack": {
                        "name": "",
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    },
                    "dinner": {
                        "name": "Beef Stir Fry",
                        "calories": 550,
                        "protein": 35,
                        "carbs": 40,
                        "fat": 25,
                        "description": "Lean beef stir-fried with mixed vegetables",
                        "ingredients": ["beef strips", "bell peppers", "onions", "soy sauce", "rice"]
                    }
                }
            },
            {
                "day": 3,
                "meals": {
                    "breakfast": {
                        "name": "Greek Yogurt Parfait",
                        "calories": 320,
                        "protein": 18,
                        "carbs": 45,
                        "fat": 8,
                        "description": "Layered Greek yogurt with granola and fruit",
                        "ingredients": ["Greek yogurt", "granola", "strawberries", "blueberries"]
                    },
                    "morning_snack": {
                        "name": "",
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    },
                    "lunch": {
                        "name": "Pasta with Tomato Sauce",
                        "calories": 480,
                        "protein": 15,
                        "carbs": 75,
                        "fat": 12,
                        "description": "Whole wheat pasta with homemade tomato sauce",
                        "ingredients": ["whole wheat pasta", "tomatoes", "garlic", "basil", "olive oil"]
                    },
                    "afternoon_snack": {
                        "name": "",
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    },
                    "dinner": {
                        "name": "Roasted Chicken Breast",
                        "calories": 420,
                        "protein": 45,
                        "carbs": 20,
                        "fat": 15,
                        "description": "Herb-roasted chicken breast with quinoa",
                        "ingredients": ["chicken breast", "quinoa", "herbs", "lemon", "olive oil"]
                    }
                }
            }
        ]
    }
    
    try:
        print("📝 Creating 3-day manual meal plan...")
        response = requests.post(f"{BASE_URL}/mealplan/create", 
                               headers=headers, json=manual_plan_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            plan_id = data.get("plan_id")
            name = data.get("name")
            duration = data.get("duration")
            start_date = data.get("start_date")
            days = data.get("days", [])
            
            # Verify response structure
            if not plan_id:
                log_test("Manual Meal Plan - Basic", False, "No plan_id in response")
                return False
            
            # Verify UUID format
            try:
                uuid.UUID(plan_id)
            except ValueError:
                log_test("Manual Meal Plan - Basic", False, f"plan_id is not valid UUID: {plan_id}")
                return False
            
            if name != "My Manual Meal Plan":
                log_test("Manual Meal Plan - Basic", False, f"Name mismatch: expected 'My Manual Meal Plan', got '{name}'")
                return False
            
            if duration != 3:
                log_test("Manual Meal Plan - Basic", False, f"Duration mismatch: expected 3, got {duration}")
                return False
            
            if start_date != "2025-02-01":
                log_test("Manual Meal Plan - Basic", False, f"Start date mismatch: expected '2025-02-01', got '{start_date}'")
                return False
            
            if len(days) != 3:
                log_test("Manual Meal Plan - Basic", False, f"Expected 3 days, got {len(days)}")
                return False
            
            # Verify day structure and totals calculation
            for i, day in enumerate(days, 1):
                if day.get("day") != i:
                    log_test("Manual Meal Plan - Basic", False, f"Day number mismatch: expected {i}, got {day.get('day')}")
                    return False
                
                meals = day.get("meals", {})
                totals = day.get("totals", {})
                
                # Check all meal categories exist
                required_meals = ["breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner"]
                for meal_type in required_meals:
                    if meal_type not in meals:
                        log_test("Manual Meal Plan - Basic", False, f"Missing meal type '{meal_type}' in day {i}")
                        return False
                
                # Verify totals calculation
                expected_calories = sum(meal.get("calories", 0) for meal in meals.values())
                expected_protein = sum(meal.get("protein", 0) for meal in meals.values())
                expected_carbs = sum(meal.get("carbs", 0) for meal in meals.values())
                expected_fat = sum(meal.get("fat", 0) for meal in meals.values())
                
                if abs(totals.get("calories", 0) - expected_calories) > 1:
                    log_test("Manual Meal Plan - Basic", False, 
                            f"Day {i} calories total mismatch: expected {expected_calories}, got {totals.get('calories')}")
                    return False
                
                if abs(totals.get("protein", 0) - expected_protein) > 1:
                    log_test("Manual Meal Plan - Basic", False, 
                            f"Day {i} protein total mismatch: expected {expected_protein}, got {totals.get('protein')}")
                    return False
            
            created_plan_ids.append(plan_id)
            
            log_test("Manual Meal Plan - Basic", True, 
                    f"Successfully created 3-day manual meal plan (ID: {plan_id[:8]}...)")
            log_test("Response Validation", True, 
                    f"All fields validated: name, duration, start_date, days structure, daily totals")
            return True
            
        else:
            log_test("Manual Meal Plan - Basic", False, 
                    f"Creation failed - Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Manual Meal Plan - Basic", False, f"Error: {str(e)}")
        return False

def test_manual_meal_plan_7_days():
    """Test creating a 7-day manual meal plan"""
    if not auth_token:
        log_test("Manual Meal Plan - 7 Days", False, "No authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create a 7-day meal plan with at least 3 meals per day
    days_data = []
    meal_names = [
        ["Avocado Toast", "Chicken Caesar Salad", "Grilled Salmon"],
        ["Protein Smoothie", "Quinoa Bowl", "Beef Tacos"],
        ["Pancakes", "Tuna Sandwich", "Pork Chops"],
        ["Yogurt Bowl", "Veggie Wrap", "Pasta Primavera"],
        ["Eggs Benedict", "Chicken Soup", "Steak Dinner"],
        ["Fruit Salad", "Fish Tacos", "Lamb Curry"],
        ["French Toast", "Club Sandwich", "Roast Chicken"]
    ]
    
    for day_num in range(1, 8):
        day_meals = meal_names[day_num - 1]
        day_data = {
            "day": day_num,
            "meals": {
                "breakfast": {
                    "name": day_meals[0],
                    "calories": 350 + (day_num * 10),
                    "protein": 15 + day_num,
                    "carbs": 40 + day_num,
                    "fat": 12 + day_num,
                    "description": f"Day {day_num} breakfast meal",
                    "ingredients": ["ingredient1", "ingredient2", "ingredient3"]
                },
                "morning_snack": {
                    "name": "",
                    "calories": 0,
                    "protein": 0,
                    "carbs": 0,
                    "fat": 0
                },
                "lunch": {
                    "name": day_meals[1],
                    "calories": 450 + (day_num * 15),
                    "protein": 25 + day_num,
                    "carbs": 35 + day_num,
                    "fat": 18 + day_num,
                    "description": f"Day {day_num} lunch meal",
                    "ingredients": ["ingredient1", "ingredient2", "ingredient3", "ingredient4"]
                },
                "afternoon_snack": {
                    "name": "",
                    "calories": 0,
                    "protein": 0,
                    "carbs": 0,
                    "fat": 0
                },
                "dinner": {
                    "name": day_meals[2],
                    "calories": 500 + (day_num * 20),
                    "protein": 35 + day_num,
                    "carbs": 30 + day_num,
                    "fat": 20 + day_num,
                    "description": f"Day {day_num} dinner meal",
                    "ingredients": ["ingredient1", "ingredient2", "ingredient3", "ingredient4", "ingredient5"]
                }
            }
        }
        days_data.append(day_data)
    
    plan_data = {
        "name": "7-Day Manual Fitness Plan",
        "duration": 7,
        "start_date": "2025-02-03",
        "days": days_data
    }
    
    try:
        print("📅 Creating 7-day manual meal plan...")
        response = requests.post(f"{BASE_URL}/mealplan/create", 
                               headers=headers, json=plan_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            plan_id = data.get("plan_id")
            
            # Verify UUID format
            try:
                uuid.UUID(plan_id)
            except ValueError:
                log_test("Manual Meal Plan - 7 Days", False, f"Invalid UUID format: {plan_id}")
                return False
            
            if data.get("duration") != 7:
                log_test("Manual Meal Plan - 7 Days", False, f"Duration mismatch: expected 7, got {data.get('duration')}")
                return False
            
            days = data.get("days", [])
            if len(days) != 7:
                log_test("Manual Meal Plan - 7 Days", False, f"Expected 7 days, got {len(days)}")
                return False
            
            created_plan_ids.append(plan_id)
            
            log_test("Manual Meal Plan - 7 Days", True, 
                    f"Successfully created 7-day manual meal plan (ID: {plan_id[:8]}...)")
            return True
            
        else:
            log_test("Manual Meal Plan - 7 Days", False, 
                    f"Creation failed - Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Manual Meal Plan - 7 Days", False, f"Error: {str(e)}")
        return False

def test_retrieve_manual_meal_plans():
    """Test retrieving manual meal plans from the list"""
    if not auth_token:
        log_test("Retrieve Manual Meal Plans", False, "No authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        print("📋 Retrieving meal plan list...")
        response = requests.get(f"{BASE_URL}/mealplan/list", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            plans = data.get("plans", [])
            
            # Find our manual plans
            manual_plans = [plan for plan in plans if plan.get("type") == "manual"]
            
            if len(manual_plans) < len(created_plan_ids):
                log_test("Retrieve Manual Meal Plans", False, 
                        f"Expected at least {len(created_plan_ids)} manual plans, found {len(manual_plans)}")
                return False
            
            # Verify manual plans have correct type and icon indicator
            for plan in manual_plans:
                if plan.get("type") != "manual":
                    log_test("Retrieve Manual Meal Plans", False, 
                            f"Plan type should be 'manual', got '{plan.get('type')}'")
                    return False
            
            log_test("Retrieve Manual Meal Plans", True, 
                    f"Found {len(manual_plans)} manual meal plans with correct type 'manual' (✍️ icon)")
            return True
            
        else:
            log_test("Retrieve Manual Meal Plans", False, 
                    f"List retrieval failed - Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Retrieve Manual Meal Plans", False, f"Error: {str(e)}")
        return False

def test_get_manual_meal_plan_details():
    """Test getting detailed manual meal plan information"""
    if not auth_token or not created_plan_ids:
        log_test("Get Manual Meal Plan Details", False, "No authentication token or created plans")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test getting details for the first created manual plan
        plan_id = created_plan_ids[0]
        print(f"🔍 Getting details for manual meal plan {plan_id[:8]}...")
        
        response = requests.get(f"{BASE_URL}/mealplan/{plan_id}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            plan = response.json()
            
            # Verify it's marked as manual type
            if plan.get("type") != "manual":
                log_test("Get Manual Meal Plan Details", False, 
                        f"Plan type should be 'manual', got '{plan.get('type')}'")
                return False
            
            # Verify all days are present
            days = plan.get("days", [])
            expected_days = 3  # First plan was 3 days
            if len(days) != expected_days:
                log_test("Get Manual Meal Plan Details", False, 
                        f"Expected {expected_days} days, got {len(days)}")
                return False
            
            # Verify meal structure and nutritional data
            first_day = days[0]
            meals = first_day.get("meals", {})
            
            # Check breakfast meal details
            breakfast = meals.get("breakfast", {})
            if breakfast.get("name") != "Oatmeal with Berries":
                log_test("Get Manual Meal Plan Details", False, 
                        f"Breakfast name mismatch: expected 'Oatmeal with Berries', got '{breakfast.get('name')}'")
                return False
            
            if breakfast.get("calories") != 350:
                log_test("Get Manual Meal Plan Details", False, 
                        f"Breakfast calories mismatch: expected 350, got {breakfast.get('calories')}")
                return False
            
            if breakfast.get("protein") != 12:
                log_test("Get Manual Meal Plan Details", False, 
                        f"Breakfast protein mismatch: expected 12, got {breakfast.get('protein')}")
                return False
            
            # Verify daily totals are calculated correctly
            totals = first_day.get("totals", {})
            expected_calories = 350 + 0 + 450 + 0 + 500  # breakfast + morning_snack + lunch + afternoon_snack + dinner
            if abs(totals.get("calories", 0) - expected_calories) > 1:
                log_test("Get Manual Meal Plan Details", False, 
                        f"Daily totals mismatch: expected {expected_calories} calories, got {totals.get('calories')}")
                return False
            
            log_test("Get Manual Meal Plan Details", True, 
                    f"Retrieved complete manual meal plan with all nutritional data and correct daily totals")
            return True
            
        else:
            log_test("Get Manual Meal Plan Details", False, 
                    f"Details retrieval failed - Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Get Manual Meal Plan Details", False, f"Error: {str(e)}")
        return False

def test_data_persistence():
    """Test that manual meal plan data persists correctly"""
    if not auth_token or not created_plan_ids:
        log_test("Data Persistence", False, "No authentication token or created plans")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Get the plan details
        plan_id = created_plan_ids[0]
        response = requests.get(f"{BASE_URL}/mealplan/{plan_id}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            plan = response.json()
            
            # Verify specific meal data matches what we submitted
            day1 = plan.get("days", [])[0]
            lunch = day1.get("meals", {}).get("lunch", {})
            
            # Check all nutritional values match
            expected_lunch = {
                "name": "Grilled Chicken Salad",
                "calories": 450,
                "protein": 35,
                "carbs": 30,
                "fat": 18
            }
            
            for field, expected_value in expected_lunch.items():
                actual_value = lunch.get(field)
                if actual_value != expected_value:
                    log_test("Data Persistence", False, 
                            f"Lunch {field} mismatch: expected {expected_value}, got {actual_value}")
                    return False
            
            # Verify ingredients and description are preserved
            if "chicken breast" not in lunch.get("ingredients", []):
                log_test("Data Persistence", False, "Lunch ingredients not preserved correctly")
                return False
            
            if "Fresh salad with grilled chicken breast" != lunch.get("description"):
                log_test("Data Persistence", False, "Lunch description not preserved correctly")
                return False
            
            log_test("Data Persistence", True, 
                    "All meal names, calories, protein, carbs, fat, ingredients, and descriptions match submitted data")
            return True
            
        else:
            log_test("Data Persistence", False, 
                    f"Failed to retrieve plan for persistence check - Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Data Persistence", False, f"Error: {str(e)}")
        return False

def test_validation_errors():
    """Test validation for manual meal plan creation"""
    if not auth_token:
        log_test("Validation Testing", False, "No authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    validation_tests = [
        {
            "name": "Missing name field",
            "data": {
                "duration": 3,
                "start_date": "2025-02-01",
                "days": []
            }
        },
        {
            "name": "Missing duration field",
            "data": {
                "name": "Test Plan",
                "start_date": "2025-02-01",
                "days": []
            }
        },
        {
            "name": "Missing start_date field",
            "data": {
                "name": "Test Plan",
                "duration": 3,
                "days": []
            }
        },
        {
            "name": "Empty days array",
            "data": {
                "name": "Test Plan",
                "duration": 3,
                "start_date": "2025-02-01",
                "days": []
            }
        }
    ]
    
    validation_passed = 0
    validation_total = len(validation_tests)
    
    for test_case in validation_tests:
        try:
            response = requests.post(f"{BASE_URL}/mealplan/create", 
                                   headers=headers, json=test_case["data"], timeout=10)
            
            # Should return 400 or 422 for validation errors
            if response.status_code in [400, 422]:
                validation_passed += 1
                print(f"   ✅ {test_case['name']}: Correctly rejected with status {response.status_code}")
            else:
                print(f"   ❌ {test_case['name']}: Expected 400/422, got {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test_case['name']}: Error - {str(e)}")
    
    if validation_passed == validation_total:
        log_test("Validation Testing", True, 
                f"All {validation_total} validation tests passed - appropriate error responses for missing fields")
        return True
    else:
        log_test("Validation Testing", False, 
                f"Only {validation_passed}/{validation_total} validation tests passed")
        return False

def run_manual_meal_plan_tests():
    """Run all manual meal plan tests"""
    print("🍽️ Manual Meal Plan Creation Testing Suite")
    print("=" * 60)
    print(f"Testing endpoint: {BASE_URL}/mealplan/create")
    print(f"Test credentials: {TEST_USER_EMAIL} / {TEST_USER_PASSWORD}")
    print("=" * 60)
    
    # Authenticate first
    if not authenticate():
        print("❌ Authentication failed - cannot proceed with tests")
        return
    
    # Test scenarios in order
    tests = [
        ("Manual Meal Plan - Basic (3 days)", test_manual_meal_plan_basic),
        ("Manual Meal Plan - 7 Days", test_manual_meal_plan_7_days),
        ("Retrieve Manual Meal Plans", test_retrieve_manual_meal_plans),
        ("Get Manual Meal Plan Details", test_get_manual_meal_plan_details),
        ("Data Persistence", test_data_persistence),
        ("Validation Testing", test_validation_errors)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 40)
        try:
            success = test_func()
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            log_test(test_name, False, f"Unexpected error: {str(e)}")
            failed += 1
        
        time.sleep(0.5)  # Small delay between tests
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MANUAL MEAL PLAN TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if created_plan_ids:
        print(f"\n📝 Created meal plan IDs: {[pid[:8] + '...' for pid in created_plan_ids]}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Manual meal plan creation is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")
    
    return passed, failed

if __name__ == "__main__":
    run_manual_meal_plan_tests()