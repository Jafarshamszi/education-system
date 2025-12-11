import requests
import json

# Test credentials for student user
LOGIN_URL = "http://localhost:8000/api/v1/auth/login"
SCHEDULE_URL = "http://localhost:8000/api/v1/students/me/schedule"

# Login to get token
print("Logging in as student 783QLRA...")
login_response = requests.post(LOGIN_URL, json={
    "username": "783QLRA",
    "password": "12345"
})

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"✅ Login successful! Token: {token[:20]}...")
    
    # Test 1: Default range (no parameters)
    print("\n" + "="*60)
    print("TEST 1: Default range (current week + 4 weeks)")
    print("="*60)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(SCHEDULE_URL, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        events = data.get("schedule_events", [])
        print(f"✅ Success! Received {len(events)} events")
        
        if events:
            # Show first 3 events
            print("\nFirst 3 events:")
            for i, event in enumerate(events[:3], 1):
                print(f"\n{i}. {event['course_code']} - {event['course_name']}")
                print(f"   Date: {event['start'][:10]}")
                print(f"   Time: {event['start'][11:16]} - {event['end'][11:16]}")
                print(f"   Day: {event['day_name']}")
                print(f"   Room: {event.get('room', 'N/A')}")
                print(f"   Type: {event.get('schedule_type', 'N/A')}")
                print(f"   Color: {event['background_color']}")
            
            # Show date range
            dates = sorted(set(e['start'][:10] for e in events))
            print(f"\nDate range: {dates[0]} to {dates[-1]}")
            print(f"Total unique dates: {len(dates)}")
            
            # Count by course
            courses = {}
            for event in events:
                code = event['course_code']
                courses[code] = courses.get(code, 0) + 1
            print(f"\nEvents per course:")
            for code, count in sorted(courses.items()):
                print(f"  {code}: {count} events")
        else:
            print("⚠️ No events returned")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text[:500])
    
    # Test 2: Specific 1-month range
    print("\n" + "="*60)
    print("TEST 2: September 15 - October 15, 2024 (1 month)")
    print("="*60)
    params = {
        "start_date": "2024-09-15",
        "end_date": "2024-10-15"
    }
    response = requests.get(SCHEDULE_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        events = data.get("schedule_events", [])
        print(f"✅ Success! Received {len(events)} events")
        
        if events:
            dates = sorted(set(e['start'][:10] for e in events))
            print(f"Date range: {dates[0]} to {dates[-1]}")
            print(f"Total unique dates: {len(dates)}")
            
            # Count by day of week
            days = {}
            for event in events:
                day = event['day_name']
                days[day] = days.get(day, 0) + 1
            print(f"\nEvents per day of week:")
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                if day in days:
                    print(f"  {day}: {days[day]} events")
        else:
            print("⚠️ No events returned")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text[:500])
    
    # Test 3: Full semester
    print("\n" + "="*60)
    print("TEST 3: Full semester (Sep 15, 2024 - Jun 14, 2025)")
    print("="*60)
    params = {
        "start_date": "2024-09-15",
        "end_date": "2025-06-14"
    }
    response = requests.get(SCHEDULE_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        events = data.get("schedule_events", [])
        print(f"✅ Success! Received {len(events)} events")
        
        if events:
            dates = sorted(set(e['start'][:10] for e in events))
            print(f"Date range: {dates[0]} to {dates[-1]}")
            print(f"Total unique dates: {len(dates)}")
            print(f"Total weeks: ~{len(dates) // 5}")  # Rough estimate
            
            courses = {}
            for event in events:
                code = event['course_code']
                courses[code] = courses.get(code, 0) + 1
            print(f"\nEvents per course (full semester):")
            for code, count in sorted(courses.items()):
                print(f"  {code}: {count} events")
        else:
            print("⚠️ No events returned")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text[:500])

else:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text[:500])
