#!/usr/bin/env python3

import requests
import json

def test_education_groups():
    """Test the education groups endpoint"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1/class-schedule/education-groups")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} education groups")
            for group in data[:3]:  # Show first 3
                print(f"  Group: {group}")
    except Exception as e:
        print(f"Error testing education groups: {e}")

def test_education_languages():
    """Test the education languages endpoint"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1/class-schedule/education-languages")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} education languages")
            for lang in data:
                print(f"  Language: {lang}")
    except Exception as e:
        print(f"Error testing education languages: {e}")

def test_semesters():
    """Test the semesters endpoint"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1/class-schedule/semesters")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} semesters")
            for semester in data:
                print(f"  Semester: {semester}")
    except Exception as e:
        print(f"Error testing semesters: {e}")


def test_teachers():
    """Test the teachers endpoint"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1/class-schedule/teachers")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} teachers")
            for teacher in data[:3]:  # Show first 3
                print(f"  Teacher: {teacher}")
    except Exception as e:
        print(f"Error testing teachers: {e}")


if __name__ == "__main__":
    print("Testing new class schedule endpoints...")
    print("\n=== Testing Education Groups ===")
    test_education_groups()
    
    print("\n=== Testing Education Languages ===")
    test_education_languages()
    
    print("\n=== Testing Semesters ===")
    test_semesters()
    
    print("\n=== Testing Teachers ===")
    test_teachers()