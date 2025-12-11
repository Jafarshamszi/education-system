#!/usr/bin/env python3
"""
Comprehensive PostgreSQL connection test
"""

from app.core.database import sync_engine
from app.core.config import settings
from sqlalchemy import text
import sys

def test_postgresql_connection():
    """Test PostgreSQL connection and database integrity"""
    
    print("🔍 PostgreSQL Connection Test")
    print("=" * 50)
    
    try:
        # Basic connection test
        print("📡 Testing connection...")
        with sync_engine.connect() as conn:
            
            # Database info
            result = conn.execute(text("SELECT version()"))
            postgres_version = result.fetchone()[0]
            print(f"✅ PostgreSQL Version: {postgres_version}")
            
            result = conn.execute(text("SELECT current_database()"))
            current_db = result.fetchone()[0]
            print(f"✅ Current Database: {current_db}")
            
            result = conn.execute(text("SELECT current_user"))
            current_user = result.fetchone()[0]
            print(f"✅ Current User: {current_user}")
            
            # Configuration check
            print(f"✅ Database URL: {settings.database_url}")
            
            # Table existence and data
            print("\n📊 Database Tables Status:")
            
            # Check accounts table
            result = conn.execute(text("SELECT COUNT(*) FROM accounts"))
            accounts_count = result.fetchone()[0]
            print(f"   👥 Accounts table: {accounts_count} records")
            
            # Check persons table
            result = conn.execute(text("SELECT COUNT(*) FROM persons"))
            persons_count = result.fetchone()[0]
            print(f"   👤 Persons table: {persons_count} records")
            
            # Check PIN code availability
            result = conn.execute(text("""
                SELECT COUNT(*) FROM accounts a 
                JOIN persons p ON a.person_id = p.id 
                WHERE p.pincode IS NOT NULL
            """))
            pin_codes_count = result.fetchone()[0]
            print(f"   🔐 Accounts with PIN codes: {pin_codes_count}")
            
            # Test authentication data
            print("\n🔐 Authentication Test:")
            result = conn.execute(text("""
                SELECT a.username, p.pincode, a.active 
                FROM accounts a 
                LEFT JOIN persons p ON a.person_id = p.id 
                WHERE a.username = '783QLRA'
            """))
            test_user = result.fetchone()
            
            if test_user:
                print(f"   ✅ Test user found: {test_user[0]}")
                print(f"   🆔 PIN Code: {test_user[1]}")
                print(f"   🟢 Active Status: {test_user[2]}")
            else:
                print("   ❌ Test user not found")
            
            # Connection pool status
            print(f"\n🏊 Connection Pool:")
            print(f"   Pool size: {sync_engine.pool.size()}")
            print(f"   Pool checked in: {sync_engine.pool.checkedin()}")
            print(f"   Pool checked out: {sync_engine.pool.checkedout()}")
            
        print("\n✅ All PostgreSQL tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ PostgreSQL connection test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_postgresql_connection()
    sys.exit(0 if success else 1)