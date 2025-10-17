#!/usr/bin/env python3
"""
Test meal plan listing to verify manual plans appear correctly
"""

import requests
import json

BASE_URL = "https://smart-meal-entry.preview.emergentagent.com/api"
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

def test_meal_plan_listing():
    """Test meal plan listing functionality"""
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("📋 Testing meal plan listing...")
    
    try:
        response = requests.get(f"{BASE_URL}/mealplan/list", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            plans = data.get("plans", [])
            
            print(f"✅ Retrieved {len(plans)} meal plans")
            
            manual_plans = [plan for plan in plans if plan.get("type") == "manual"]
            ai_plans = [plan for plan in plans if plan.get("type") == "ai_generated"]
            
            print(f"   Manual plans: {len(manual_plans)}")
            print(f"   AI plans: {len(ai_plans)}")
            
            # Show details of manual plans
            for i, plan in enumerate(manual_plans, 1):
                print(f"\n   Manual Plan {i}:")
                print(f"     ID: {plan.get('plan_id', '')[:8]}...")
                print(f"     Name: {plan.get('name')}")
                print(f"     Duration: {plan.get('duration')} days")
                print(f"     Type: {plan.get('type')} (should show ✍️ icon)")
                print(f"     Created: {plan.get('created_at')}")
            
            if manual_plans:
                print(f"\n✅ Manual meal plans are correctly identified with type 'manual'")
                return True
            else:
                print(f"\n❌ No manual meal plans found in list")
                return False
                
        else:
            print(f"❌ Failed to retrieve meal plan list: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("📋 Testing Meal Plan Listing")
    print("=" * 40)
    success = test_meal_plan_listing()
    if success:
        print("\n🎉 Meal plan listing working correctly!")
    else:
        print("\n❌ Meal plan listing test failed!")
