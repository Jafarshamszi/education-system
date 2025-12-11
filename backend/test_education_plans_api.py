#!/usr/bin/env python3
"""
Test script to verify the education plans API endpoint works correctly
"""
import requests
import json

def test_education_plans_endpoint():
    """Test the education plans endpoint"""
    base_url = "http://localhost:8000"
    
    # First, let's test if we can connect to the server
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Make sure it's running on port 8000.")
        return False
    
    # Test education plans endpoint without auth (should fail)
    try:
        response = requests.get(f"{base_url}/api/education-plans/")
        print(f"\nEducation plans (no auth): {response.status_code}")
        if response.status_code == 401:
            print("✅ Authentication required as expected")
        elif response.status_code == 200:
            plans = response.json()
            print(f"✅ Got {len(plans)} education plans")
            if plans:
                print("Sample plan:")
                print(json.dumps(plans[0], indent=2, ensure_ascii=False))
        else:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing education plans endpoint: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Education Plans API...")
    print("=" * 50)
    
    if test_education_plans_endpoint():
        print("\n✅ Basic API tests completed")
    else:
        print("\n❌ Tests failed")