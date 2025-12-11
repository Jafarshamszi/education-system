#!/usr/bin/env python3
"""
Check password format of real users
"""
import sys
sys.path.append('.')

from app.core.database import SessionLocal
from sqlalchemy import text

def check_password_format():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT username, password FROM accounts WHERE username = '783QLRA'"))
        row = result.fetchone()
        if row:
            print(f'Username: {row[0]}')
            print(f'Password (first 50 chars): {row[1][:50]}...')
            print(f'Password length: {len(row[1]) if row[1] else 0}')
            if row[1]:
                print(f'Starts with: {row[1][:10]}')
        else:
            print('User not found')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    check_password_format()