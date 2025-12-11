#!/usr/bin/env python3
"""
Check database for test users and PIN codes
"""
import sys
sys.path.append('.')

from app.core.database import SessionLocal
from sqlalchemy import text

def check_users():
    db = SessionLocal()
    try:
        # Check for our test users
        query = """SELECT a.id, a.username, p.firstname, p.lastname, p.pincode 
                   FROM accounts a 
                   LEFT JOIN persons p ON a.person_id = p.id 
                   WHERE a.username IN ('admin', 'teacher1', 'student1')"""
        result = db.execute(text(query))
        rows = result.fetchall()
        
        print('=== TEST USERS WITH PIN CODES ===')
        if rows:
            for row in rows:
                print(f'Account ID: {row[0]}')
                print(f'Username: {row[1]}')
                print(f'Name: {row[2]} {row[3]}' if row[2] else 'No person linked')
                print(f'PIN Code: {row[4]}' if row[4] else 'No PIN code')
                print('---')
        else:
            print('No test users found with those usernames')
            
        # Let's also check what usernames actually exist
        print('\n=== ALL USERNAMES IN DATABASE ===')
        result = db.execute(text("SELECT username FROM accounts ORDER BY username LIMIT 10"))
        usernames = result.fetchall()
        for username in usernames:
            print(f'Username: {username[0]}')
            
    except Exception as e:
        print(f'Error: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    check_users()