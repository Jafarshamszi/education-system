#!/usr/bin/env python3
"""
Add teacher 5GK3GY7 as instructor for redistributed sections
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'lms',
    'user': 'postgres',
    'password': '1111'
}

# Teacher username
TEACHER_USERNAME = '5GK3GY7'

# New sections where students were moved (need instructor access)
NEW_SECTIONS = [
    '7a277f19-f137-4f7c-9f3b-5eef350e7095',  # 2024/2025_PY_HF- B03
    '95cad416-8ed3-4f3b-9fc2-b4fd5837429f',  # 2023/2024_PY_HF- B03
    '3e2119cd-9fea-41c6-a331-21b8fd171307',  # 2022/2023_YZ_HF- B03
    '8e414620-bb34-49bc-9ccc-59bf44ad6b30',  # 2023/2024_PY_HF – B0
    '45d9db2e-5722-43d5-88df-c4247f8857e8',  # 2024/2025_PY_HF – B0
]


def main():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    try:
        # Get teacher user ID
        cur.execute("SELECT id FROM users WHERE username = %s", [TEACHER_USERNAME])
        teacher = cur.fetchone()
        
        if not teacher:
            print(f"❌ Teacher {TEACHER_USERNAME} not found!")
            return
        
        teacher_id = teacher['id']
        print(f"Teacher ID: {teacher_id}\n")
        
        # Add instructor assignments
        for section_id in NEW_SECTIONS:
            # Get section info
            cur.execute("""
                SELECT section_code
                FROM course_offerings
                WHERE id = %s
            """, [section_id])
            
            section = cur.fetchone()
            
            if not section:
                print(f"❌ Section {section_id} not found!")
                continue
            
            # Check if assignment already exists
            cur.execute("""
                SELECT id
                FROM course_instructors
                WHERE course_offering_id = %s AND instructor_id = %s
            """, [section_id, teacher_id])
            
            existing = cur.fetchone()
            
            if existing:
                print(f"✓ {section['section_code']} - Already assigned")
            else:
                # Insert new instructor assignment
                cur.execute("""
                    INSERT INTO course_instructors (
                        course_offering_id, instructor_id, role
                    )
                    VALUES (%s, %s, 'primary')
                """, [section_id, teacher_id])
                
                print(f"✅ {section['section_code']} - Instructor added")
        
        conn.commit()
        print("\n✅ All instructor assignments complete!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
