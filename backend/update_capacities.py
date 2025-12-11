#!/usr/bin/env python3
"""
Update course offering capacities after redistribution
"""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'lms',
    'user': 'postgres',
    'password': '1111'
}

# All affected sections
ALL_SECTIONS = [
    '0f9e0ee4-3ff4-41d5-8ad1-8bee4c518163',  # Original
    '7a277f19-f137-4f7c-9f3b-5eef350e7095',  # 2024/2025_PY_HF- B03
    '95cad416-8ed3-4f3b-9fc2-b4fd5837429f',  # 2023/2024_PY_HF- B03
    'b695f1de-9540-44ff-9ec9-5a9821c44a9a',  # 2022/2023_PY_HF- B03
    '3e2119cd-9fea-41c6-a331-21b8fd171307',  # 2022/2023_YZ_HF- B03
    '8e414620-bb34-49bc-9ccc-59bf44ad6b30',  # 2023/2024_PY_HF – B0
    '45d9db2e-5722-43d5-88df-c4247f8857e8',  # 2024/2025_PY_HF – B0
]

def main():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    try:
        print("Updating enrollment counts and capacities...\n")
        
        for section_id in ALL_SECTIONS:
            # Get actual enrollment count
            cur.execute("""
                SELECT COUNT(*) as count
                FROM course_enrollments
                WHERE course_offering_id = %s
                AND enrollment_status = 'enrolled'
            """, [section_id])
            
            actual_count = cur.fetchone()['count']
            
            # Get section info
            cur.execute("""
                SELECT co.section_code, co.max_enrollment, co.current_enrollment
                FROM course_offerings co
                WHERE co.id = %s
            """, [section_id])
            
            section = cur.fetchone()
            print(f"Section: {section['section_code']}")
            print(f"  Old: max={section['max_enrollment']}, current={section['current_enrollment']}")
            print(f"  Actual enrollments: {actual_count}")
            
            # Update both current_enrollment and max_enrollment
            new_max = max(section['max_enrollment'] or 0, actual_count)
            
            cur.execute("""
                UPDATE course_offerings
                SET current_enrollment = %s,
                    max_enrollment = %s
                WHERE id = %s
            """, [actual_count, new_max, section_id])
            
            print(f"  New: max={new_max}, current={actual_count}")
            print()
        
        conn.commit()
        print("✅ All capacities updated successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
