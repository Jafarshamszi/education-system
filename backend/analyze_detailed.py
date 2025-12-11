#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

def analyze_detailed():
    conn = psycopg2.connect(
        host='localhost', 
        database='edu', 
        user='postgres', 
        password='1111', 
        cursor_factory=RealDictCursor
    )
    cur = conn.cursor()

    print("=== DETAILED DATABASE ANALYSIS ===")
    
    # 1. Find main student table and its structure
    print("\n1. MAIN STUDENT TABLE:")
    try:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('students', 'student', 'a_students_bak', 'a_students_mag')
            ORDER BY table_name;
        """)
        student_tables = cur.fetchall()
        for table in student_tables:
            print(f"- {table['table_name']}")
            
        # Check main student table structure
        main_table = 'students'  # Try this first
        try:
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{main_table}' ORDER BY ordinal_position LIMIT 10;")
            cols = cur.fetchall()
            if cols:
                print(f"\n{main_table} columns (first 10):")
                for col in cols:
                    print(f"  - {col['column_name']}")
        except:
            print(f"{main_table} table not accessible")
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. Check for groups/classes tables
    print("\n2. GROUPS/CLASSES STRUCTURE:")
    try:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE 'group%' OR table_name = 'groups' OR table_name LIKE '%group' OR table_name LIKE 'class%')
            ORDER BY table_name;
        """)
        group_tables = cur.fetchall()
        for table in group_tables:
            print(f"- {table['table_name']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. Check education language tables
    print("\n3. EDUCATION LANGUAGE:")
    try:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%education%lang%' OR table_name LIKE '%edu%lang%')
            ORDER BY table_name;
        """)
        lang_tables = cur.fetchall()
        for table in lang_tables:
            print(f"- {table['table_name']}")
            
        # Try to find language data
        try:
            cur.execute("SELECT * FROM education_lang LIMIT 5;")
            langs = cur.fetchall()
            print("Sample education languages:")
            for lang in langs:
                print(f"  - {lang}")
        except:
            pass
    except Exception as e:
        print(f"Error: {e}")
    
    # 4. Check semester/term structure
    print("\n4. SEMESTER/TERM DATA:")
    try:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%semester%' OR table_name = 'semesters')
            ORDER BY table_name;
        """)
        semester_tables = cur.fetchall()
        for table in semester_tables:
            print(f"- {table['table_name']}")
            
        # Check if there's semester data in other tables
        try:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE column_name LIKE '%semester%' LIMIT 10;")
            semester_cols = cur.fetchall()
            print("Columns with 'semester' in name:")
            for col in semester_cols:
                print(f"  - {col['column_name']}")
        except:
            pass
    except Exception as e:
        print(f"Error: {e}")
    
    # 5. Check course table structure for semester references
    print("\n5. COURSE TABLE FOREIGN KEYS:")
    try:
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'course' ORDER BY ordinal_position;")
        course_cols = cur.fetchall()
        print("Course table columns:")
        for col in course_cols:
            print(f"  - {col['column_name']}: {col['data_type']}")
    except Exception as e:
        print(f"Error: {e}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    analyze_detailed()