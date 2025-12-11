#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor

def check_subjects():
    conn = psycopg2.connect(
        host='localhost',
        database='edu',
        user='postgres',
        password='1111',
        cursor_factory=RealDictCursor
    )
    cur = conn.cursor()

    # Get all tables with 'subject' in name
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%subject%' 
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print('Subject-related tables:')
    for table in tables:
        print(f'- {table["table_name"]}')

    # Check if there's a subjects or education_plan_subject table
    if tables:
        table_name = tables[0]["table_name"]
        print(f'\nSample data from {table_name}:')
        cur.execute(f"SELECT * FROM {table_name} LIMIT 10;")
        samples = cur.fetchall()
        for sample in samples:
            print(sample)

    # Also check regular subjects patterns in course data
    print('\nChecking course/class table names:')
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%course%' OR table_name LIKE '%class%' OR table_name LIKE '%schedule%')
        ORDER BY table_name;
    """)
    course_tables = cur.fetchall()
    for table in course_tables:
        print(f'- {table["table_name"]}')

    # Try to find the main course table and check subjects
    if course_tables:
        # Try the most likely table name
        main_table = 'schedule'  # Based on API endpoints
        print(f'\nChecking subject patterns in {main_table}:')
        try:
            cur.execute(f"""
                SELECT subject_name, COUNT(*) as count 
                FROM {main_table}
                WHERE subject_name IS NOT NULL 
                GROUP BY subject_name 
                ORDER BY count DESC 
                LIMIT 10;
            """)
            subjects = cur.fetchall()
            for subject in subjects:
                print(f'{subject["subject_name"]}: {subject["count"]} courses')
        except Exception as e:
            print(f'Error accessing {main_table}: {e}')
    
    # Check subject_catalog table
    print('\nSample subjects from subject_catalog:')
    cur.execute("SELECT subject FROM subject_catalog ORDER BY subject LIMIT 20;")
    subjects = cur.fetchall()
    for subject in subjects:
        print(f'- {subject["subject"]}')

    cur.close()
    conn.close()

if __name__ == "__main__":
    check_subjects()