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

def check_person_table():
    """Check the person table for teacher name data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check person table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'person' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        if columns:
            print("Person table structure:")
            for col in columns:
                print(f"  {col['column_name']}: {col['data_type']}")
                
            # Get sample data with teacher join
            cursor.execute("""
                SELECT 
                    t.id as teacher_id,
                    p.name_az,
                    p.surname_az,
                    CONCAT(p.name_az, ' ', p.surname_az) as full_name
                FROM teachers t
                INNER JOIN person p ON t.person_id = p.id
                WHERE t.active = 1 AND t.teaching = 1
                LIMIT 10
            """)
            teachers = cursor.fetchall()
            print(f"\nSample teachers with names ({len(teachers)} rows):")
            for teacher in teachers:
                print(f"  {dict(teacher)}")
        else:
            print("Person table not found")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_person_table()