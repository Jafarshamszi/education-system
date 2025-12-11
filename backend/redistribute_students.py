#!/usr/bin/env python3
"""
Redistribute students from overcrowded SUBJ00691 course section
Move 1,417 students to other sections, keeping only 100 in the original
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

# Original overcrowded section
ORIGINAL_SECTION_ID = '0f9e0ee4-3ff4-41d5-8ad1-8bee4c518163'

# Target sections to distribute students to (different years)
TARGET_SECTIONS = [
    '7a277f19-f137-4f7c-9f3b-5eef350e7095',  # 2024/2025_PY_HF- B03
    '95cad416-8ed3-4f3b-9fc2-b4fd5837429f',  # 2023/2024_PY_HF- B03
    'b695f1de-9540-44ff-9ec9-5a9821c44a9a',  # 2022/2023_PY_HF- B03
    '3e2119cd-9fea-41c6-a331-21b8fd171307',  # 2022/2023_YZ_HF- B03
    '8e414620-bb34-49bc-9ccc-59bf44ad6b30',  # 2023/2024_PY_HF – B0
    '45d9db2e-5722-43d5-88df-c4247f8857e8',  # 2024/2025_PY_HF – B0
]

STUDENTS_TO_KEEP = 100

def main():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    try:
        # Get current enrollment count
        cur.execute("""
            SELECT COUNT(*) as total
            FROM course_enrollments
            WHERE course_offering_id = %s
        """, [ORIGINAL_SECTION_ID])
        
        current_total = cur.fetchone()['total']
        print(f"Current enrollment: {current_total} students")
        
        students_to_move = current_total - STUDENTS_TO_KEEP
        print(f"Students to move: {students_to_move}")
        print(f"Students to keep: {STUDENTS_TO_KEEP}")
        
        if students_to_move <= 0:
            print("No students to move!")
            return
        
        # Get student IDs to move (all except first 100)
        cur.execute("""
            SELECT id, student_id
            FROM course_enrollments
            WHERE course_offering_id = %s
            ORDER BY enrollment_date, id
            OFFSET %s
        """, [ORIGINAL_SECTION_ID, STUDENTS_TO_KEEP])
        
        students_to_redistribute = cur.fetchall()
        print(f"Found {len(students_to_redistribute)} enrollment records to move")
        
        # Distribute students evenly across target sections
        students_per_section = len(students_to_redistribute) // len(TARGET_SECTIONS)
        remainder = len(students_to_redistribute) % len(TARGET_SECTIONS)
        
        print(f"\nDistribution plan:")
        print(f"  Base per section: {students_per_section}")
        print(f"  Remainder to distribute: {remainder}")
        
        moved_count = 0
        start_idx = 0
        
        for i, target_section_id in enumerate(TARGET_SECTIONS):
            # Calculate how many students for this section
            count = students_per_section + (1 if i < remainder else 0)
            
            if count == 0:
                continue
                
            end_idx = start_idx + count
            batch = students_to_redistribute[start_idx:end_idx]
            
            print(f"\nMoving {len(batch)} students to section {i+1}")
            
            # Update enrollments to new section
            for enrollment in batch:
                cur.execute("""
                    UPDATE course_enrollments
                    SET course_offering_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, [target_section_id, enrollment['id']])
                
                moved_count += 1
                
                if moved_count % 100 == 0:
                    print(f"  Moved {moved_count}/{len(students_to_redistribute)}...")
            
            start_idx = end_idx
        
        # Commit the transaction
        conn.commit()
        
        print(f"\n✅ Successfully moved {moved_count} students")
        
        # Verify final counts
        print("\n📊 Final enrollment counts:")
        
        cur.execute("""
            SELECT COUNT(*) as count
            FROM course_enrollments
            WHERE course_offering_id = %s
        """, [ORIGINAL_SECTION_ID])
        
        original_count = cur.fetchone()['count']
        print(f"  Original section: {original_count} students")
        
        for i, target_id in enumerate(TARGET_SECTIONS):
            cur.execute("""
                SELECT COUNT(*) as count
                FROM course_enrollments
                WHERE course_offering_id = %s
            """, [target_id])
            
            target_count = cur.fetchone()['count']
            if target_count > 0:
                print(f"  Target section {i+1}: {target_count} students")
        
        # Update current_enrollment counts and max_enrollment capacity
        print("\n🔄 Updating enrollment counts and capacity in course_offerings...")
        
        all_sections = [ORIGINAL_SECTION_ID] + TARGET_SECTIONS
        for section_id in all_sections:
            # Get actual enrollment count
            cur.execute("""
                SELECT COUNT(*) as count
                FROM course_enrollments
                WHERE course_offering_id = %s
                AND enrollment_status = 'enrolled'
            """, [section_id])
            
            actual_count = cur.fetchone()['count']
            
            # Update both current_enrollment and max_enrollment
            # Set max_enrollment to be at least equal to current enrollment
            cur.execute("""
                UPDATE course_offerings
                SET current_enrollment = %s,
                    max_enrollment = GREATEST(max_enrollment, %s)
                WHERE id = %s
            """, [actual_count, actual_count, section_id])
        
        conn.commit()
        print("✅ Enrollment counts and capacities updated")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Student Redistribution Script")
    print("=" * 60)
    print()
    
    response = input("This will move 1,417 students to other sections. Continue? (yes/no): ")
    
    if response.lower() == 'yes':
        main()
        print("\n✅ Redistribution complete!")
    else:
        print("❌ Operation cancelled")
