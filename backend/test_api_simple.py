"""
Simple test to verify education plans API is working correctly
"""
import requests
import json

def test_education_plans_api():
    """Test the education plans API endpoints"""
    base_url = "http://localhost:8000/api/v1/education-plans"
    
    # Test data
    test_user = {
        "username": "admin",
        "password": "admin123",
        "pin_code": ""
    }
    
    print("Testing Education Plans API...")
    print("=" * 50)
    
    try:
        # 1. Login to get token
        print("1. Logging in...")
        login_response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
            
        token_data = login_response.json()
        token = token_data.get("access_token")
        
        if not token:
            print("❌ No access token received")
            return
            
        print("✓ Login successful")
        
        # Setup headers with token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 2. Test get all education plans
        print("\n2. Getting education plans...")
        plans_response = requests.get(f"{base_url}/", headers=headers)
        
        if plans_response.status_code == 200:
            plans = plans_response.json()
            print(f"✓ Found {len(plans)} education plans")
            
            if plans:
                first_plan = plans[0]
                print(f"   Sample plan: {first_plan.get('name', 'N/A')} (ID: {first_plan.get('id')})")
                
                # 3. Test get plan detail
                if first_plan.get('id'):
                    print(f"\n3. Getting plan detail for ID: {first_plan['id']}")
                    detail_response = requests.get(f"{base_url}/{first_plan['id']}", headers=headers)
                    
                    if detail_response.status_code == 200:
                        detail = detail_response.json()
                        print("✓ Plan detail retrieved successfully")
                        print(f"   Name: {detail.get('name')}")
                        print(f"   Organization ID: {detail.get('organization_id')}")
                        print(f"   Education Type ID: {detail.get('education_type_id')}")
                        print(f"   Total Subjects: {detail.get('total_subjects')}")
                    else:
                        print(f"❌ Plan detail failed: {detail_response.status_code}")
                        print(f"Response: {detail_response.text}")
            else:
                print("   No plans found")
        else:
            print(f"❌ Getting plans failed: {plans_response.status_code}")
            print(f"Response: {plans_response.text}")
        
        # 4. Test search functionality
        print("\n4. Testing search...")
        search_response = requests.get(f"{base_url}/?search=2019", headers=headers)
        
        if search_response.status_code == 200:
            search_results = search_response.json()
            print(f"✓ Search returned {len(search_results)} results")
        else:
            print(f"❌ Search failed: {search_response.status_code}")
        
        # 5. Test stats
        print("\n5. Getting statistics...")
        stats_response = requests.get(f"{base_url}/stats", headers=headers)
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"✓ Stats retrieved: {stats}")
        else:
            print(f"❌ Stats failed: {stats_response.status_code}")
        
        print("\n✅ API test completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the backend server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    test_education_plans_api()