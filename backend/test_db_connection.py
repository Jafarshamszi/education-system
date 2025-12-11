#!/usr/bin/env python3
"""
Test database connection and verify our models work
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


def test_connection():
    """Test database connection"""
    try:
        print(f"Testing connection to: {settings.database_url}")
        
        # Test the sync session
        for session in get_db():
            # Try to query users table
            from sqlalchemy import text
            result = session.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"✓ Connected successfully! Found {count} users in database")
            break
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    test_connection()