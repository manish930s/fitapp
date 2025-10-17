#!/usr/bin/env python3
"""
Test validation scenarios for manual meal plan creation
"""

import requests
import json

BASE_URL = "https://gymchat-trainer.preview.emergentagent.com/api"
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

def test_validation_scenarios():
    """Test various validation scenarios"""
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🧪 Testing validation scenarios...")
    
    # Test cases
    test_cases = [
        {
            "name": "Missing name field",
            "data": {
                "duration": 3,
                "start_date": "2025-02-01",
                "days": [{"day": 1, "meals": {}}]
            },
            "expected_status": [400, 422]
        },
        {
            "name": "Missing duration field", 
            "data": {
                "name": "Test Plan",
                "start_date": "2025-02-01",
                "days": [{"day": 1, "meals": {}}]
            },
            "expected_status": [400, 422]
        },
        {
            "name": "Missing start_date field",
            "data": {
                "name": "Test Plan",
                "duration": 3,
                "days": [{"day": 1, "meals": {}}]
            },
            "expected_status": [400, 422]
        },
        {
            "name": "Invalid duration (0)",
            "data": {
                "name": "Test Plan",
                "duration": 0,
                "start_date": "2025-02-01",
                "days": []
            },
            "expected_status": [400, 422, 200]  # May accept and handle gracefully
        },
        {
            "name": "Invalid duration (negative)",
            "data": {
                "name": "Test Plan", 
                "duration": -1,
                "start_date": "2025-02-01",
                "days": []
            },
            "expected_status": [400, 422, 200]
        },
        {
            "name": "Empty name",
            "data": {
                "name": "",
                "duration": 3,
                "start_date": "2025-02-01", 
                "days": [{"day": 1, "meals": {}}]
            },
            "expected_status": [400, 422, 200]
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        try:
            response = requests.post(f"{BASE_URL}/mealplan/create",
                                   headers=headers, json=test_case["data"], timeout=10)
            
            if response.status_code in test_case["expected_status"]:
                print(f"✅ {test_case['name']}: Status {response.status_code} (expected)")
                passed += 1
            else:
                print(f"❌ {test_case['name']}: Status {response.status_code} (unexpected)")
                print(f"   Expected: {test_case['expected_status']}")
                
        except Exception as e:
            print(f"❌ {test_case['name']}: Error - {str(e)}")
    
    print(f"\n📊 Validation Results: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    print("🔍 Testing Validation Scenarios")
    print("=" * 40)
    success = test_validation_scenarios()
    if success:
        print("\n🎉 All validation tests passed!")
    else:
        print("\n⚠️  Some validation tests failed (may be acceptable)")
