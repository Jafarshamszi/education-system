#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='edu',
        user='postgres',
        password='1111',
        port=5432
    )

def check_teachers_table():
    """Check the teachers table structure"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if teachers table exists and its structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'teachers' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        if columns:
            print("Teachers table structure:")
            for col in columns:
                print(f"  {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
                
            # Get some sample teacher data
            cursor.execute("SELECT * FROM teachers LIMIT 5")
            teachers = cursor.fetchall()
            print(f"\nSample teachers data ({len(teachers)} rows):")
            for teacher in teachers:
                print(f"  {dict(teacher)}")
        else:
            print("Teachers table not found. Checking for similar tables...")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name ILIKE '%teach%' OR table_name ILIKE '%person%'
                ORDER BY table_name
            """)
            similar_tables = cursor.fetchall()
            print("Similar tables:")
            for table in similar_tables:
                print(f"  {table['table_name']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_teachers_table()