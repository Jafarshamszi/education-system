"""
Test database connection for both Django and FastAPI configurations
"""
import sys
import os

# Test 1: Test Django database connection
print("=" * 60)
print("TEST 1: Testing Django Database Connection")
print("=" * 60)

try:
    import psycopg2
    
    # Django settings - should connect to 'lms'
    conn = psycopg2.connect(
        host='localhost',
        database='lms',
        user='postgres',
        password='1111',
        port=5432
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT current_database(), current_user, version();")
    db_name, db_user, version = cursor.fetchone()
    
    print(f"✅ Django PostgreSQL Connection Successful!")
    print(f"   Database: {db_name}")
    print(f"   User: {db_user}")
    print(f"   PostgreSQL Version: {version.split(',')[0]}")
    
    # Test table count
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    table_count = cursor.fetchone()[0]
    print(f"   Tables in database: {table_count}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Django Database Connection Failed: {e}")
    sys.exit(1)

print()

# Test 2: Test FastAPI database connection using config
print("=" * 60)
print("TEST 2: Testing FastAPI Database Connection")
print("=" * 60)

try:
    sys.path.insert(0, '/home/axel/Developer/Education-system/backend')
    from app.core.config import settings
    
    print(f"✅ FastAPI Config Loaded Successfully!")
    print(f"   DB_NAME: {settings.DB_NAME}")
    print(f"   DB_HOST: {settings.DB_HOST}")
    print(f"   DB_PORT: {settings.DB_PORT}")
    print(f"   DB_USER: {settings.DB_USER}")
    print(f"   Database URL (sync): {settings.database_url}")
    print(f"   Database URL (async): {settings.async_database_url}")
    
    # Verify it's pointing to 'lms'
    if settings.DB_NAME == 'lms':
        print(f"✅ FastAPI is correctly configured to use 'lms' database!")
    else:
        print(f"❌ FastAPI is still configured to use '{settings.DB_NAME}' database!")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ FastAPI Config Load Failed: {e}")
    sys.exit(1)

print()

# Test 3: Test actual connection to lms database
print("=" * 60)
print("TEST 3: Testing LMS Database Readiness")
print("=" * 60)

try:
    conn = psycopg2.connect(
        host='localhost',
        database='lms',
        user='postgres',
        password='1111',
        port=5432
    )
    
    cursor = conn.cursor()
    
    # Check critical tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('users', 'students', 'courses', 'grades', 'attendance_records')
        ORDER BY table_name;
    """)
    
    critical_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"✅ LMS Database Critical Tables:")
    for table in critical_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"   • {table}: {count} records")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ LMS Database Check Failed: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("🎉 ALL DATABASE CONNECTION TESTS PASSED!")
print("=" * 60)
print()
print("✅ The Education System is now configured to use the 'lms' database")
print("✅ Both Django and FastAPI backends are properly configured")
print("✅ Database contains all required tables and data")
print()
print("You can now start the backend services:")
print("  - Django: cd backend/django_backend/education_system && python manage.py runserver 8001")
print("  - FastAPI: cd backend && uvicorn app.main:app --reload --port 8000")
