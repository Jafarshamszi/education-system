#!/usr/bin/env python3
"""
Test script for FastAPI authentication endpoints
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_api_root():
    """Test the API root endpoint"""
    try:
        response = requests.get("http://127.0.0.1:8000/")
        print(f"🧪 API Root: {response.status_code} - {response.text[:100]}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ API Root test failed: {e}")
        return False

def test_docs():
    """Test the docs endpoint"""
    try:
        response = requests.get("http://127.0.0.1:8000/docs")
        print(f"🧪 Docs: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Docs test failed: {e}")
        return False

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"🧪 Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_login_invalid():
    """Test login with invalid credentials"""
    try:
        login_data = {
            "username": "invalid_user",
            "password": "invalid_password"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"🧪 Login (Invalid): {response.status_code}")
        if response.status_code == 401:
            print(f"   ✅ Correctly rejected invalid credentials")
            return True
        else:
            print(f"   ❌ Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False

def test_login_valid():
    """Test login with potentially valid credentials"""
    try:
        # Try common admin credentials
        test_credentials = [
            {"username": "admin", "password": "admin"},
            {"username": "administrator", "password": "admin"},
            {"username": "root", "password": "root"},
            {"username": "test", "password": "test"},
        ]
        
        for creds in test_credentials:
            response = requests.post(f"{BASE_URL}/auth/login", json=creds)
            print(f"🧪 Login ({creds['username']}): {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Login successful! Got access token")
                print(f"   📧 User: {data.get('user', {}).get('username')}")
                print(f"   🏷️  Type: {data.get('user', {}).get('user_type')}")
                return data.get('access_token'), data.get('user')
            elif response.status_code == 401:
                print(f"   ❌ Invalid credentials for {creds['username']}")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                print(f"   📝 Response: {response.text}")
        
        print("   ❌ No valid credentials found")
        return None, None
        
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return None, None

def test_protected_endpoint(token):
    """Test accessing a protected endpoint"""
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"🧪 Protected endpoint (/auth/me): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Got user profile:")
            print(f"   👤 Username: {data.get('username')}")
            print(f"   🏷️  User Type: {data.get('user_type')}")
            print(f"   📧 Email: {data.get('email')}")
            return True
        else:
            print(f"   ❌ Failed to access protected endpoint")
            return False
            
    except Exception as e:
        print(f"❌ Protected endpoint test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting API endpoint tests...\n")
    
    # Test basic endpoints
    print("📋 Testing basic endpoints...")
    test_api_root()
    test_docs()
    test_health_check()
    
    print("\n🔐 Testing authentication...")
    
    # Test invalid login
    test_login_invalid()
    
    # Test valid login
    token, user = test_login_valid()
    
    if token:
        print(f"\n🛡️  Testing protected endpoints...")
        test_protected_endpoint(token)
    else:
        print("\n⚠️  Cannot test protected endpoints without valid token")
    
    print("\n✅ API testing complete!")

if __name__ == "__main__":
    main()