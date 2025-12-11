#!/usr/bin/env python3
"""
Fix enrollment counts by adjusting both current_enrollment and max_enrollment
to accommodate actual enrollment data.
"""

import psycopg2
from psycopg2.extras import RealDictCursor


def fix_enrollment_counts():
    """Fix enrollment counts, adjusting max_enrollment if needed"""
    print("=" * 80)
    print("FIXING COURSE ENROLLMENT COUNTS")
    print("=" * 80)
    
    conn = psycopg2.connect(
        dbname="lms",
        user="postgres",
        password="1111",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check for overcapacity courses
    print("\n1. Checking for overcapacity enrollments...")
    cur.execute("""
        SELECT 
            co.id,
            c.code as course_code,
            co.section_code,
            co.max_enrollment,
            COUNT(ce.id) as actual_enrollment
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.id
        LEFT JOIN course_enrollments ce ON co.id = ce.course_offering_id
            AND ce.enrollment_status IN ('enrolled', 'completed')
        GROUP BY co.id, c.code, co.section_code, co.max_enrollment
        HAVING COUNT(ce.id) > co.max_enrollment
        ORDER BY (COUNT(ce.id) - co.max_enrollment) DESC
        LIMIT 20;
    """)
    
    overcapacity = cur.fetchall()
    if overcapacity:
        print(f"\n⚠️  Found {len(overcapacity)} courses over capacity:")
        for course in overcapacity[:10]:
            overflow = course['actual_enrollment'] - course['max_enrollment']
            print(f"  {course['course_code']} ({course['section_code']}): "
                  f"{course['actual_enrollment']}/{course['max_enrollment']} "
                  f"(+{overflow} overflow)")
    
    # Update approach: First adjust max_enrollment, then current_enrollment
    print("\n2. Updating max_enrollment for overcapacity courses...")
    cur.execute("""
        UPDATE course_offerings co
        SET 
            max_enrollment = GREATEST(
                max_enrollment,
                (
                    SELECT COUNT(*)
                    FROM course_enrollments ce
                    WHERE ce.course_offering_id = co.id
                    AND ce.enrollment_status IN ('enrolled', 'completed')
                )
            ),
            updated_at = CURRENT_TIMESTAMP
        WHERE id IN (
            SELECT co2.id
            FROM course_offerings co2
            LEFT JOIN course_enrollments ce ON co2.id = ce.course_offering_id
                AND ce.enrollment_status IN ('enrolled', 'completed')
            GROUP BY co2.id, co2.max_enrollment
            HAVING COUNT(ce.id) > co2.max_enrollment
        );
    """)
    
    adjusted_count = cur.rowcount
    print(f"  ✅ Adjusted max_enrollment for {adjusted_count} courses")
    
    # Now update current_enrollment
    print("\n3. Updating current_enrollment counts...")
    cur.execute("""
        UPDATE course_offerings co
        SET 
            current_enrollment = COALESCE(
                (
                    SELECT COUNT(*)
                    FROM course_enrollments ce
                    WHERE ce.course_offering_id = co.id
                    AND ce.enrollment_status IN ('enrolled', 'completed')
                ), 
                0
            ),
            updated_at = CURRENT_TIMESTAMP;
    """)
    
    updated_count = cur.rowcount
    print(f"  ✅ Updated {updated_count} course offerings")
    
    conn.commit()
    print("\n✅ All enrollment counts updated successfully!")
    
    # Verify the update
    print("\n4. Verifying updated counts...")
    cur.execute("""
        SELECT 
            COUNT(*) as total_offerings,
            SUM(current_enrollment) as total_enrollments,
            COUNT(*) FILTER (WHERE current_enrollment = 0) as zero_enrollment,
            COUNT(*) FILTER (WHERE current_enrollment > 0) as with_students,
            MAX(current_enrollment) as max_in_offering,
            ROUND(AVG(current_enrollment), 2) as avg_enrollment,
            COUNT(*) FILTER (
                WHERE current_enrollment > max_enrollment
            ) as still_overcapacity
        FROM course_offerings;
    """)
    
    final_state = cur.fetchone()
    print(f"\nFinal state:")
    print(f"  Total offerings: {final_state['total_offerings']}")
    print(f"  Total enrollments: {final_state['total_enrollments']}")
    print(f"  Offerings with 0 students: {final_state['zero_enrollment']}")
    print(f"  Offerings with students: {final_state['with_students']}")
    print(f"  Max enrollment in offering: {final_state['max_in_offering']}")
    print(f"  Average enrollment: {final_state['avg_enrollment']}")
    print(f"  Still overcapacity: {final_state['still_overcapacity']}")
    
    # Sample high-enrollment courses
    print("\n5. Top 10 courses by enrollment:")
    cur.execute("""
        SELECT 
            c.code as course_code,
            c.name->>'az' as course_name,
            co.section_code,
            co.current_enrollment,
            co.max_enrollment,
            ROUND(
                (co.current_enrollment::numeric / co.max_enrollment * 100),
                1
            ) as fill_pct
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.id
        WHERE co.current_enrollment > 0
        ORDER BY co.current_enrollment DESC
        LIMIT 10;
    """)
    
    top_courses = cur.fetchall()
    for course in top_courses:
        print(f"  {course['course_code']}: {course['course_name'][:40]}")
        print(f"    {course['current_enrollment']}/{course['max_enrollment']} "
              f"students ({course['fill_pct']}%)")
    
    # Check teacher's courses
    print("\n6. Teacher 5GK3GY7's courses:")
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
        for course in teacher_courses:
            print(f"  {course['course_code']}: {course['course_name']}")
            print(f"    Enrollment: {course['current_enrollment']}/"
                  f"{course['max_enrollment']}")
    else:
        print("  No courses found")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("ENROLLMENT FIX COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        fix_enrollment_counts()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
