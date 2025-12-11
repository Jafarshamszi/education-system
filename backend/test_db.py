#!/usr/bin/env python3
"""
Check test account password and database
"""

from app.core.database import sync_engine
from sqlalchemy import text

print("Checking test account...")

try:
    with sync_engine.connect() as conn:
        result = conn.execute(text("SELECT username, password, active FROM accounts WHERE username = '783QLRA'")).fetchone()
        if result:
            print(f"Username: {result[0]}")
            print(f"Password (first 20 chars): {result[1][:20] if result[1] else 'None'}...")
            print(f"Active: {result[2]}")
        else:
            print("Account not found")
        
except Exception as e:
    print(f"Error: {e}")