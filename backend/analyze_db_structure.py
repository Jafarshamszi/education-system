#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

def analyze_database():
    conn = psycopg2.connect(
        host='localhost', 
        database='edu', 
        user='postgres', 
        password='1111', 
        cursor_factory=RealDictCursor
    )
    cur = conn.cursor()

    print("=== ANALYZING DATABASE STRUCTURE ===")
    
    # 1. Find class/group related tables
    print("\n1. CLASS/GROUP RELATED TABLES:")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%class%' OR table_name LIKE '%group%' OR table_name LIKE '%student%')
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    for table in tables[:15]:  # Show first 15
        print(f"- {table['table_name']}")
    
    # 2. Find semester/term related tables
    print("\n2. SEMESTER/TERM RELATED TABLES:")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%semester%' OR table_name LIKE '%term%' OR table_name LIKE '%period%')
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    for table in tables:
        print(f"- {table['table_name']}")
    
    # 3. Find language related tables
    print("\n3. LANGUAGE RELATED TABLES:")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%lang%' OR table_name LIKE '%language%')
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    for table in tables:
        print(f"- {table['table_name']}")
    
    # 4. Check student groups structure
    print("\n4. STUDENT GROUPS TABLE STRUCTURE:")
    try:
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'student_groups' ORDER BY ordinal_position;")
        cols = cur.fetchall()
        if cols:
            for col in cols:
                print(f"- {col['column_name']}: {col['data_type']}")
            
            # Sample data
            print("\nSample student_groups data:")
            cur.execute("SELECT * FROM student_groups LIMIT 3;")
            samples = cur.fetchall()
            for sample in samples:
                print(sample)
    except Exception as e:
        print(f"Error with student_groups: {e}")
    
    # 5. Check education years/semesters
    print("\n5. EDUCATION YEARS/SEMESTERS:")
    try:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%edu%year%' OR table_name LIKE '%semester%')
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        for table in tables:
            print(f"- {table['table_name']}")
        
        # Check edu_years table
        if any('edu_years' in str(t['table_name']) for t in tables):
            print("\nSample edu_years data:")
            cur.execute("SELECT name FROM edu_years WHERE active = 1 LIMIT 5;")
            years = cur.fetchall()
            for year in years:
                print(f"- {year['name']}")
    except Exception as e:
        print(f"Error with years/semesters: {e}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    analyze_database()