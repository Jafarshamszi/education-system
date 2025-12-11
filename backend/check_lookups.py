#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

def check_lookup_tables():
    conn = psycopg2.connect(
        host='localhost', 
        database='edu', 
        user='postgres', 
        password='1111', 
        cursor_factory=RealDictCursor
    )
    cur = conn.cursor()

    print("=== LOOKUP TABLES DATA ===")

    # 1. Education Languages
    print("\n1. EDUCATION LANGUAGES:")
    try:
        cur.execute("SELECT * FROM education_lang LIMIT 10;")
        langs = cur.fetchall()
        for lang in langs:
            name = lang.get("name_az") or lang.get("name") or "N/A"
            print(f"  - ID: {lang['id']}, Name: {name}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Education Types
    print("\n2. EDUCATION TYPES:")
    try:
        cur.execute("SELECT * FROM education_type LIMIT 10;")
        types = cur.fetchall()
        for typ in types:
            name = typ.get("name_az") or typ.get("name") or "N/A"
            print(f"  - ID: {typ['id']}, Name: {name}")
    except Exception as e:
        print(f"Error: {e}")

    # 3. Education Levels
    print("\n3. EDUCATION LEVELS:")
    try:
        cur.execute("SELECT * FROM education_level LIMIT 10;")
        levels = cur.fetchall()
        for level in levels:
            name = level.get("name_az") or level.get("name") or "N/A"
            print(f"  - ID: {level['id']}, Name: {name}")
    except Exception as e:
        print(f"Error: {e}")

    # 4. Check if there's a semester table
    print("\n4. SEMESTER DATA:")
    try:
        cur.execute("SELECT * FROM semester LIMIT 5;")
        semesters = cur.fetchall()
        for sem in semesters:
            name = sem.get("name_az") or sem.get("name") or "N/A"
            print(f"  - ID: {sem['id']}, Name: {name}")
    except Exception as e:
        print(f"Error with semester table: {e}")
        
        # Try to find semester data in other places
        try:
            cur.execute("SELECT DISTINCT semester_id FROM course WHERE semester_id IS NOT NULL LIMIT 5;")
            sem_ids = cur.fetchall()
            print("Found semester_ids in course table:")
            for sid in sem_ids:
                print(f"  - {sid['semester_id']}")
        except Exception as e2:
            print(f"Error finding semesters: {e2}")

    # 5. Sample education groups with year info
    print("\n5. EDUCATION GROUPS (with year info):")
    try:
        cur.execute("""
            SELECT eg.name, ey.name as year_name, el.name_az as level_name 
            FROM education_group eg
            LEFT JOIN edu_years ey ON eg.education_year_id = ey.id
            LEFT JOIN education_level el ON eg.education_level_id = el.id
            LIMIT 5;
        """)
        groups = cur.fetchall()
        for group in groups:
            print(f"  - Group: {group['name']}, Year: {group['year_name']}, Level: {group['level_name']}")
    except Exception as e:
        print(f"Error: {e}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    check_lookup_tables()