#!/usr/bin/env python3
"""
Test the specific manual meal plan data structure from the review request
"""

import requests
import json

BASE_URL = "https://supabase-connect-22.preview.emergentagent.com/api"
TEST_USER_EMAIL = "test@fitflow.com"
TEST_USER_PASSWORD = "Test123!"

def get_auth_token():
    """Get authentication token"""
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
    if response.status_code == 200:
        return response.json().get("token")
    return None

def test_specific_manual_plan():
    """Test the exact manual meal plan structure from the review request"""
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Exact data structure from the review request
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
                        "description": "Healthy breakfast",
                        "ingredients": ["oats", "berries", "milk"]
                    },
                    "morning_snack": {"name": "", "calories": 0, "protein": 0, "carbs": 0, "fat": 0},
                    "lunch": {
                        "name": "Grilled Chicken Salad",
                        "calories": 450,
                        "protein": 35,
                        "carbs": 30,
                        "fat": 18
                    },
                    "afternoon_snack": {"name": "", "calories": 0, "protein": 0, "carbs": 0, "fat": 0},
                    "dinner": {
                        "name": "Salmon with Vegetables",
                        "calories": 500,
                        "protein": 40,
                        "carbs": 35,
                        "fat": 22
                    }
                }
            },
            {
                "day": 2,
                "meals": {
                    "breakfast": {"name": "Scrambled Eggs", "calories": 300, "protein": 20, "carbs": 5, "fat": 15},
                    "morning_snack": {"name": "", "calories": 0, "protein": 0, "carbs": 0, "fat": 0},
                    "lunch": {"name": "Turkey Sandwich", "calories": 400, "protein": 25, "carbs": 45, "fat": 12},
                    "afternoon_snack": {"name": "", "calories": 0, "protein": 0, "carbs": 0, "fat": 0},
                    "dinner": {"name": "Beef Stir Fry", "calories": 550, "protein": 35, "carbs": 40, "fat": 25}
                }
            },
            {
                "day": 3,
                "meals": {
                    "breakfast": {"name": "Greek Yogurt Parfait", "calories": 320, "protein": 18, "carbs": 45, "fat": 8},
                    "morning_snack": {"name": "", "calories": 0, "protein": 0, "carbs": 0, "fat": 0},
                    "lunch": {"name": "Pasta with Tomato Sauce", "calories": 480, "protein": 15, "carbs": 75, "fat": 12},
                    "afternoon_snack": {"name": "", "calories": 0, "protein": 0, "carbs": 0, "fat": 0},
                    "dinner": {"name": "Roasted Chicken Breast", "calories": 420, "protein": 45, "carbs": 20, "fat": 15}
                }
            }
        ]
    }
    
    print("🧪 Testing exact manual meal plan structure from review request...")
    
    try:
        response = requests.post(f"{BASE_URL}/mealplan/create", 
                               headers=headers, json=manual_plan_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            plan_id = data.get("plan_id")
            
            print(f"✅ Manual meal plan created successfully!")
            print(f"   Plan ID: {plan_id}")
            print(f"   Name: {data.get('name')}")
            print(f"   Duration: {data.get('duration')} days")
            print(f"   Start Date: {data.get('start_date')}")
            print(f"   Days: {len(data.get('days', []))}")
            
            # Verify response structure
            days = data.get("days", [])
            for i, day in enumerate(days, 1):
                meals = day.get("meals", {})
                totals = day.get("totals", {})
                print(f"   Day {i}: {totals.get('calories', 0)} calories, {totals.get('protein', 0)}g protein")
            
            # Test retrieval
            print(f"\n🔍 Testing retrieval of created plan...")
            get_response = requests.get(f"{BASE_URL}/mealplan/{plan_id}", headers=headers, timeout=10)
            
            if get_response.status_code == 200:
                retrieved_plan = get_response.json()
                print(f"✅ Plan retrieved successfully!")
                print(f"   Type: {retrieved_plan.get('type')}")
                print(f"   Days in retrieved plan: {len(retrieved_plan.get('days', []))}")
                
                # Verify specific meal data
                day1_breakfast = retrieved_plan.get("days", [])[0].get("meals", {}).get("breakfast", {})
                if day1_breakfast.get("name") == "Oatmeal with Berries" and day1_breakfast.get("calories") == 350:
                    print(f"✅ Meal data persistence verified!")
                else:
                    print(f"❌ Meal data mismatch!")
                    return False
                
                return True
            else:
                print(f"❌ Failed to retrieve plan: {get_response.status_code}")
                return False
                
        else:
            print(f"❌ Failed to create manual meal plan")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🍽️ Testing Specific Manual Meal Plan Structure")
    print("=" * 50)
    success = test_specific_manual_plan()
    if success:
        print("\n🎉 All tests passed! Manual meal plan creation working correctly.")
    else:
        print("\n❌ Tests failed!")
