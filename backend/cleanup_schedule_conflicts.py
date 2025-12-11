"""
Cleanup script to resolve teacher schedule conflicts
Strategy: Keep class with highest enrollment, remove others
"""
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        dbname="lms",
        user="postgres",
        password="1111",
        host="localhost",
        port="5432"
    )


def cleanup_schedule_conflicts(dry_run=True):
    """
    Remove duplicate schedules keeping the class with highest enrollment
    
    Args:
        dry_run: If True, only show what would be deleted without actually deleting
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 100)
    print(f"SCHEDULE CONFLICT CLEANUP - {'DRY RUN' if dry_run else 'LIVE RUN'}")
    print("=" * 100)
    
    # Get all conflicts
    cur.execute("""
        SELECT
            ci.instructor_id,
            cs.day_of_week,
            cs.start_time,
            cs.end_time,
            ARRAY_AGG(cs.id::text ORDER BY co.current_enrollment DESC NULLS LAST, cs.created_at) as schedule_ids,
            ARRAY_AGG(co.id::text ORDER BY co.current_enrollment DESC NULLS LAST, cs.created_at) as offering_ids,
            ARRAY_AGG(c.code ORDER BY co.current_enrollment DESC NULLS LAST, cs.created_at) as course_codes,
            ARRAY_AGG(co.section_code ORDER BY co.current_enrollment DESC NULLS LAST, cs.created_at) as sections,
            ARRAY_AGG(COALESCE(co.current_enrollment, 0) ORDER BY co.current_enrollment DESC NULLS LAST, cs.created_at) as enrollments,
            COUNT(*) as conflict_count
        FROM course_instructors ci
        JOIN course_offerings co ON ci.course_offering_id = co.id
        JOIN courses c ON co.course_id = c.id
        JOIN class_schedules cs ON cs.course_offering_id = co.id
        GROUP BY ci.instructor_id, cs.day_of_week, cs.start_time, cs.end_time
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
    """)
    
    conflicts = cur.fetchall()
    
    total_to_delete = 0
    schedules_to_delete = []
    offerings_to_check = []
    
    for conflict in conflicts:
        # Keep the first one (highest enrollment), delete the rest
        keep_schedule_id = conflict['schedule_ids'][0]
        keep_offering_id = conflict['offering_ids'][0]
        keep_course = conflict['course_codes'][0]
        keep_section = conflict['sections'][0]
        keep_enrollment = conflict['enrollments'][0]
        
        delete_count = conflict['conflict_count'] - 1
        total_to_delete += delete_count
        
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        day_name = days[conflict['day_of_week']]
        
        print(f"\n{day_name} {conflict['start_time']}-{conflict['end_time']}: {conflict['conflict_count']} conflicts")
        print(f"  ✓ KEEP: {keep_course} ({keep_section}) - Enrollment: {keep_enrollment}")
        
        for i in range(1, conflict['conflict_count']):
            schedule_id = conflict['schedule_ids'][i]
            offering_id = conflict['offering_ids'][i]
            course = conflict['course_codes'][i]
            section = conflict['sections'][i]
            enrollment = conflict['enrollments'][i]
            
            schedules_to_delete.append(schedule_id)
            offerings_to_check.append(offering_id)
            
            print(f"  ✗ DELETE: {course} ({section}) - Enrollment: {enrollment}")
    
    print("\n" + "=" * 100)
    print(f"SUMMARY: {len(conflicts)} conflict groups found")
    print(f"Total schedules to delete: {total_to_delete}")
    print("=" * 100)
    
    if not dry_run:
        print("\n⚠️  EXECUTING DELETION...")
        
        # Delete the conflicting schedules
        if schedules_to_delete:
            cur.execute("""
                DELETE FROM class_schedules
                WHERE id::text = ANY(%s)
            """, [schedules_to_delete])
            
            deleted_count = cur.rowcount
            print(f"✓ Deleted {deleted_count} class_schedules records")
            
            # Check if any course_offerings are now orphaned (no schedules)
            cur.execute("""
                SELECT co.id::text, c.code, co.section_code
                FROM course_offerings co
                JOIN courses c ON co.course_id = c.id
                WHERE co.id::text = ANY(%s)
                AND NOT EXISTS (
                    SELECT 1 FROM class_schedules cs 
                    WHERE cs.course_offering_id = co.id
                )
            """, [offerings_to_check])
            
            orphaned = cur.fetchall()
            
            if orphaned:
                print(f"\n⚠️  Found {len(orphaned)} orphaned course offerings (no schedules left):")
                for o in orphaned:
                    print(f"  - {o['code']} ({o['section_code']})")
                print("\nThese course offerings may need to be reviewed or removed.")
            
            conn.commit()
            print("\n✓ Changes committed to database")
        else:
            print("No schedules to delete")
    else:
        print("\n⚠️  DRY RUN - No changes made to database")
        print("Run with dry_run=False to apply changes")
    
    cur.close()
    conn.close()
    
    return total_to_delete


if __name__ == "__main__":
    import sys
    
    # Default to dry run unless explicitly told to execute
    execute = '--execute' in sys.argv or '--live' in sys.argv
    
    if execute:
        print("\n⚠️⚠️⚠️  WARNING  ⚠️⚠️⚠️")
        print("This will DELETE data from the database!")
        print("Make sure you have a backup!")
        response = input("\nType 'DELETE' to confirm: ")
        
        if response == 'DELETE':
            cleanup_schedule_conflicts(dry_run=False)
        else:
            print("Cancelled")
    else:
        print("\n💡 Running in DRY RUN mode (no changes will be made)")
        print("To execute changes, run: python3 cleanup_schedule_conflicts.py --execute\n")
        cleanup_schedule_conflicts(dry_run=True)
