#!/usr/bin/env python3
"""
FitFlow Backend API Testing Suite
Tests all backend endpoints with focus on AI food scanning integration
"""

import requests
import json
import base64
import time
from datetime import datetime
import os

# Configuration
BASE_URL = "https://fitnessai-hub-2.preview.emergentagent.com/api"
TEST_USER_EMAIL = "fitflow.tester@example.com"
TEST_USER_PASSWORD = "SecureTest123!"
TEST_USER_NAME = "FitFlow Tester"

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

def get_sample_food_image_base64():
    """Get a sample food image as base64 for testing"""
    # This is a small sample image of an apple (1x1 pixel PNG for testing)
    # In real testing, you'd use an actual food image
    sample_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    return sample_image

def test_health_check():
    """Test the health check endpoint"""
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

def test_user_registration():
    """Test user registration endpoint"""
    global auth_token, user_id
    
    user_data = {
        "name": TEST_USER_NAME,
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
            daily_calories = data.get("daily_calories")
            
            if auth_token and user_id:
                log_test("User Registration", True, 
                        f"User registered successfully. Daily calories: {daily_calories}")
                return True
            else:
                log_test("User Registration", False, "Missing token or user_id in response")
                return False
        elif response.status_code == 400 and "already registered" in response.text:
            # User already exists, try to login instead
            log_test("User Registration", True, "User already exists (expected for repeated tests)")
            return test_user_login()
        else:
            log_test("User Registration", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("User Registration", False, f"Error: {str(e)}")
        return False

def test_user_login():
    """Test user login endpoint"""
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
        else:
            log_test("User Login", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("User Login", False, f"Error: {str(e)}")
        return False

def test_get_user_profile():
    """Test getting user profile with calorie calculations"""
    if not auth_token:
        log_test("Get User Profile", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/user/profile", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            daily_calories = data.get("daily_calories")
            
            if daily_calories and "daily_target" in daily_calories:
                log_test("Get User Profile", True, 
                        f"Profile retrieved. Daily target: {daily_calories['daily_target']} calories")
                return True
            else:
                log_test("Get User Profile", False, "Missing daily calorie calculations")
                return False
        else:
            log_test("Get User Profile", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Get User Profile", False, f"Error: {str(e)}")
        return False

def test_update_user_profile():
    """Test updating user profile"""
    if not auth_token:
        log_test("Update User Profile", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    profile_data = {
        "weight": 69.5,
        "goal_weight": 67.0
    }
    
    try:
        response = requests.put(f"{BASE_URL}/user/profile", 
                              headers=headers, json=profile_data, timeout=10)
        
        if response.status_code == 200:
            log_test("Update User Profile", True, "Profile updated successfully")
            return True
        else:
            log_test("Update User Profile", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Update User Profile", False, f"Error: {str(e)}")
        return False

def test_food_scan_ai():
    """Test the critical AI food scanning functionality"""
    if not auth_token:
        log_test("AI Food Scan", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Get sample image
    sample_image = get_sample_food_image_base64()
    
    # Test with form data as expected by the endpoint
    form_data = {"image": sample_image}
    
    try:
        print("🔍 Testing AI Food Scanning (this may take 10-30 seconds)...")
        response = requests.post(f"{BASE_URL}/food/scan", 
                               headers=headers, data=form_data, timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["food_name", "calories", "protein", "carbs", "fat", "portion_size"]
            
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                log_test("AI Food Scan", True, 
                        f"Food analyzed: {data['food_name']}, "
                        f"Calories: {data['calories']}, "
                        f"Portion: {data['portion_size']}")
                return True
            else:
                log_test("AI Food Scan", False, 
                        f"Missing fields in response: {missing_fields}")
                return False
        else:
            log_test("AI Food Scan", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        log_test("AI Food Scan", False, "Request timeout - OpenRouter API may be slow")
        return False
    except Exception as e:
        log_test("AI Food Scan", False, f"Error: {str(e)}")
        return False

def test_food_history():
    """Test getting food scan history"""
    if not auth_token:
        log_test("Food History", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/food/history", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            history = data.get("history", [])
            log_test("Food History", True, f"Retrieved {len(history)} food scan records")
            return True
        else:
            log_test("Food History", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Food History", False, f"Error: {str(e)}")
        return False

def test_today_food_summary():
    """Test getting today's food summary"""
    if not auth_token:
        log_test("Today Food Summary", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/food/today", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["total_calories", "total_protein", "total_carbs", "total_fat", "meal_count"]
            
            if all(field in data for field in required_fields):
                log_test("Today Food Summary", True, 
                        f"Today's totals - Calories: {data['total_calories']}, "
                        f"Meals: {data['meal_count']}")
                return True
            else:
                log_test("Today Food Summary", False, "Missing fields in response")
                return False
        else:
            log_test("Today Food Summary", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Today Food Summary", False, f"Error: {str(e)}")
        return False

def test_daily_stats():
    """Test daily stats endpoints"""
    if not auth_token:
        log_test("Daily Stats", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test updating daily stats
    stats_data = {
        "steps": 8500,
        "calories_burned": 350,
        "active_minutes": 45,
        "water_intake": 6,
        "sleep_hours": 7.5
    }
    
    try:
        # Update stats
        response = requests.post(f"{BASE_URL}/stats/daily", 
                               headers=headers, json=stats_data, timeout=10)
        
        if response.status_code != 200:
            log_test("Daily Stats Update", False, 
                    f"Update failed - Status: {response.status_code}")
            return False
        
        # Get stats
        response = requests.get(f"{BASE_URL}/stats/daily", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("steps") == 8500:
                log_test("Daily Stats", True, f"Stats updated and retrieved successfully")
                return True
            else:
                log_test("Daily Stats", False, "Stats not properly saved/retrieved")
                return False
        else:
            log_test("Daily Stats", False, 
                    f"Get failed - Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Daily Stats", False, f"Error: {str(e)}")
        return False

def test_streak_calculation():
    """Test streak calculation"""
    if not auth_token:
        log_test("Streak Calculation", False, "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/stats/streak", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "streak_days" in data:
                log_test("Streak Calculation", True, 
                        f"Current streak: {data['streak_days']} days")
                return True
            else:
                log_test("Streak Calculation", False, "Missing streak_days in response")
                return False
        else:
            log_test("Streak Calculation", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Streak Calculation", False, f"Error: {str(e)}")
        return False

def run_all_tests():
    """Run all backend tests in order"""
    print("🚀 Starting FitFlow Backend API Tests")
    print("=" * 50)
    
    # Test order based on dependencies
    tests = [
        ("Health Check", test_health_check),
        ("User Registration", test_user_registration),
        ("User Login", test_user_login),
        ("Get User Profile", test_get_user_profile),
        ("Update User Profile", test_update_user_profile),
        ("AI Food Scan (CRITICAL)", test_food_scan_ai),
        ("Food History", test_food_history),
        ("Today Food Summary", test_today_food_summary),
        ("Daily Stats", test_daily_stats),
        ("Streak Calculation", test_streak_calculation)
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
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    # Show critical failures
    critical_tests = ["AI Food Scan (CRITICAL)", "User Registration", "User Login"]
    critical_failures = []
    
    for test_name in critical_tests:
        if test_name in test_results and not test_results[test_name]["success"]:
            critical_failures.append(test_name)
    
    if critical_failures:
        print(f"\n🚨 CRITICAL FAILURES: {', '.join(critical_failures)}")
    
    return passed, failed, test_results

if __name__ == "__main__":
    passed, failed, results = run_all_tests()
    
    # Save detailed results
    with open("/app/test_results_detailed.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/test_results_detailed.json")