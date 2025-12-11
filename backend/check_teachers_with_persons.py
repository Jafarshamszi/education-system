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

def check_teachers_with_persons():
    """Check teachers with person names"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get sample data with teacher join
        cursor.execute("""
            SELECT 
                t.id as teacher_id,
                p.firstname,
                p.lastname,
                p.patronymic,
                CONCAT(p.firstname, ' ', p.lastname) as full_name
            FROM teachers t
            INNER JOIN persons p ON t.person_id = p.id
            WHERE t.active = 1 AND t.teaching = 1
            LIMIT 10
        """)
        teachers = cursor.fetchall()
        print(f"Sample teachers with names ({len(teachers)} rows):")
        for teacher in teachers:
            print(f"  {dict(teacher)}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_teachers_with_persons()