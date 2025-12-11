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

def find_person_tables():
    """Find tables related to person data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Find tables with person in name or similar
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name ILIKE '%person%' 
               OR table_name ILIKE '%people%'
               OR table_name ILIKE '%user%'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print("Tables related to person/user:")
        for table in tables:
            print(f"  {table['table_name']}")
            
            # Get column info for each table
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
                LIMIT 10
            """, (table['table_name'],))
            columns = cursor.fetchall()
            
            print(f"    Columns: {[col['column_name'] for col in columns]}")
            print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_person_tables()