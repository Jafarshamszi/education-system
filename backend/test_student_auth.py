#!/usr/bin/env python3
"""
Test student authentication and profile endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Test student credentials
username = "783QLRA"
password = "SHVtYXkyMDAy"

print("=" * 60)
print("Testing Student Authentication and Profile")
print("=" * 60)

# Step 1: Login
print("\n1. Testing login...")
login_data = {
    "username": username,
    "password": password,
    "frontend_type": "student"
}

try:
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        login_result = response.json()
        print("Login successful!")
        print(f"User ID: {login_result.get('user_id')}")
        print(f"Username: {login_result.get('username')}")
        print(f"User Type: {login_result.get('user_type')}")
        print(f"Full Name: {login_result.get('full_name')}")
        print(f"Email: {login_result.get('email')}")
        
        access_token = login_result.get('access_token')
        print(f"\nAccess Token (first 50 chars): {access_token[:50]}...")
        
        # Step 2: Test profile endpoint
        print("\n2. Testing profile endpoint...")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        profile_response = requests.get(f"{BASE_URL}/auth/user/", headers=headers)
        print(f"Status: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print("Profile retrieved successfully!")
            print(json.dumps(profile_data, indent=2))
        else:
            print(f"Error: {profile_response.text}")
            
    else:
        print(f"Login failed: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
