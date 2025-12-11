#!/usr/bin/env python3
"""
Update current_enrollment counts in course_offerings table
based on actual enrollment data in course_enrollments table.
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def update_enrollment_counts():
    """Update current_enrollment counts for all course offerings"""
    print("=" * 80)
    print("UPDATING COURSE ENROLLMENT COUNTS")
    print("=" * 80)
    
    conn = psycopg2.connect(
        dbname="lms",
        user="postgres",
        password="1111",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # First, check current state
    print("\n1. Checking current enrollment counts...")
    cur.execute("""
        SELECT 
            COUNT(*) as total_offerings,
            SUM(current_enrollment) as total_reported_enrollments,
            COUNT(*) FILTER (WHERE current_enrollment = 0) as offerings_with_zero,
            COUNT(*) FILTER (WHERE current_enrollment > 0) as offerings_with_students
        FROM course_offerings;
    """)
    
    current_state = cur.fetchone()
    print(f"\nCurrent state:")
    print(f"  Total course offerings: {current_state['total_offerings']}")
    print(f"  Total reported enrollments: {current_state['total_reported_enrollments']}")
    print(f"  Offerings with 0 enrollment: {current_state['offerings_with_zero']}")
    print(f"  Offerings with > 0 enrollment: {current_state['offerings_with_students']}")
    
    # Check actual enrollments from course_enrollments
    print("\n2. Checking actual enrollments...")
    cur.execute("""
        SELECT 
            COUNT(*) as total_enrollments,
            COUNT(DISTINCT course_offering_id) as offerings_with_enrollments,
            COUNT(DISTINCT student_id) as unique_students
        FROM course_enrollments
        WHERE enrollment_status IN ('enrolled', 'completed');
    """)
    
    actual_state = cur.fetchone()
    print(f"\nActual enrollment data:")
    print(f"  Total enrollments: {actual_state['total_enrollments']}")
    print(f"  Course offerings with enrollments: {actual_state['offerings_with_enrollments']}")
    print(f"  Unique students: {actual_state['unique_students']}")
    
    # Show discrepancy
    discrepancy = (current_state['total_reported_enrollments'] or 0) - actual_state['total_enrollments']
    print(f"\n⚠️  Discrepancy: {abs(discrepancy)} enrollments")
    
    if discrepancy != 0:
        print("\n3. Updating enrollment counts...")
        
        # Update all course offerings with correct counts
        cur.execute("""
            UPDATE course_offerings co
            SET 
                current_enrollment = COALESCE(enrollment_counts.count, 0),
                updated_at = CURRENT_TIMESTAMP
            FROM (
                SELECT 
                    course_offering_id,
                    COUNT(*) as count
                FROM course_enrollments
                WHERE enrollment_status IN ('enrolled', 'completed')
                GROUP BY course_offering_id
            ) as enrollment_counts
            WHERE co.id = enrollment_counts.course_offering_id
            AND co.current_enrollment != enrollment_counts.count;
        """)
        
        updated_count = cur.rowcount
        print(f"  ✅ Updated {updated_count} course offerings")
        
        # Also set to 0 for offerings with no enrollments
        cur.execute("""
            UPDATE course_offerings co
            SET 
                current_enrollment = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE co.current_enrollment != 0
            AND co.id NOT IN (
                SELECT DISTINCT course_offering_id
                FROM course_enrollments
                WHERE enrollment_status IN ('enrolled', 'completed')
            );
        """)
        
        zero_count = cur.rowcount
        print(f"  ✅ Set {zero_count} offerings to 0 enrollment")
        
        conn.commit()
        print("\n✅ Enrollment counts updated successfully!")
    else:
        print("\n✅ Enrollment counts are already correct!")
    
    # Verify the update
    print("\n4. Verifying updated counts...")
    cur.execute("""
        SELECT 
            COUNT(*) as total_offerings,
            SUM(current_enrollment) as total_enrollments,
            COUNT(*) FILTER (WHERE current_enrollment = 0) as offerings_with_zero,
            COUNT(*) FILTER (WHERE current_enrollment > 0) as offerings_with_students,
            MAX(current_enrollment) as max_enrollment_in_offering,
            AVG(current_enrollment) as avg_enrollment
        FROM course_offerings;
    """)
    
    final_state = cur.fetchone()
    print(f"\nFinal state:")
    print(f"  Total course offerings: {final_state['total_offerings']}")
    print(f"  Total enrollments: {final_state['total_enrollments']}")
    print(f"  Offerings with 0 enrollment: {final_state['offerings_with_zero']}")
    print(f"  Offerings with students: {final_state['offerings_with_students']}")
    print(f"  Max enrollment in any offering: {final_state['max_enrollment_in_offering']}")
    print(f"  Average enrollment: {float(final_state['avg_enrollment'] or 0):.2f}")
    
    # Show sample offerings with enrollments
    print("\n5. Sample course offerings with updated counts:")
    cur.execute("""
        SELECT 
            co.id,
            c.code as course_code,
            co.section_code,
            co.current_enrollment,
            co.max_enrollment,
            ROUND((co.current_enrollment::numeric / co.max_enrollment::numeric * 100), 2) as fill_percentage
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.id
        WHERE co.current_enrollment > 0
        ORDER BY co.current_enrollment DESC
        LIMIT 10;
    """)
    
    samples = cur.fetchall()
    print(f"\nTop 10 offerings by enrollment:")
    for sample in samples:
        print(f"  {sample['course_code']} ({sample['section_code']}): "
              f"{sample['current_enrollment']}/{sample['max_enrollment']} "
              f"({sample['fill_percentage']}%)")
    
    # Check teacher's courses
    print("\n6. Checking test teacher's courses...")
    cur.execute("""
        SELECT 
            c.code as course_code,
            c.name->>'az' as course_name,
            co.section_code,
            co.current_enrollment,
            co.max_enrollment
        FROM course_instructors ci
        JOIN staff_members sm ON ci.instructor_id = sm.user_id
        JOIN users u ON sm.user_id = u.id
        JOIN course_offerings co ON ci.course_offering_id = co.id
        JOIN courses c ON co.course_id = c.id
        WHERE u.username = '5GK3GY7'
        ORDER BY c.code;
    """)
    
    teacher_courses = cur.fetchall()
    if teacher_courses:
        print(f"\nTeacher 5GK3GY7's courses ({len(teacher_courses)} total):")
        for course in teacher_courses:
            print(f"  {course['course_code']}: {course['course_name']}")
            print(f"    Section: {course['section_code']}")
            print(f"    Enrollment: {course['current_enrollment']}/{course['max_enrollment']}")
    else:
        print("\n⚠️  No courses found for teacher 5GK3GY7")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("ENROLLMENT COUNT UPDATE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        update_enrollment_counts()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
