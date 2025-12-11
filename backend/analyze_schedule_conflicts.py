"""
Analyze and report all teacher schedule conflicts
where a teacher is assigned to multiple classes at the same time
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import defaultdict

def get_db_connection():
    return psycopg2.connect(
        dbname="lms",
        user="postgres",
        password="1111",
        host="localhost",
        port="5432"
    )

def analyze_all_conflicts():
    """Find all teachers with scheduling conflicts"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all teachers with schedule conflicts
    cur.execute("""
        SELECT 
            u.username,
            CONCAT(p.first_name, ' ', COALESCE(p.middle_name, ''), ' ', p.last_name) as teacher_name,
            COUNT(*) as total_schedules,
            COUNT(DISTINCT CONCAT(cs.day_of_week, '-', cs.start_time, '-', cs.end_time)) as unique_timeslots
        FROM course_instructors ci
        JOIN users u ON ci.instructor_id = u.id
        LEFT JOIN persons p ON u.id = p.user_id
        JOIN course_offerings co ON ci.course_offering_id = co.id
        JOIN class_schedules cs ON cs.course_offering_id = co.id
        GROUP BY u.id, u.username, p.first_name, p.middle_name, p.last_name
        HAVING COUNT(*) > COUNT(DISTINCT CONCAT(cs.day_of_week, '-', cs.start_time, '-', cs.end_time))
        ORDER BY COUNT(*) - COUNT(DISTINCT CONCAT(cs.day_of_week, '-', cs.start_time, '-', cs.end_time)) DESC
        LIMIT 10
    """)
    
    teachers_with_conflicts = cur.fetchall()
    
    print("=" * 100)
    print("TEACHER SCHEDULE CONFLICT ANALYSIS")
    print("=" * 100)
    print(f"\nFound {len(teachers_with_conflicts)} teachers with scheduling conflicts\n")
    
    all_conflicts = []
    
    for teacher in teachers_with_conflicts:
        print(f"\nTeacher: {teacher['username']} - {teacher['teacher_name']}")
        print(f"Total Schedules: {teacher['total_schedules']}, Unique Time Slots: {teacher['unique_timeslots']}")
        print(f"Conflicts: {teacher['total_schedules'] - teacher['unique_timeslots']} overlapping classes")
        
        # Get detailed conflicts for this teacher
        cur.execute("""
            SELECT
                u.id as instructor_id,
                cs.day_of_week,
                cs.start_time,
                cs.end_time,
                COUNT(*) as conflict_count,
                ARRAY_AGG(cs.id::text) as schedule_ids,
                ARRAY_AGG(c.code) as course_codes,
                ARRAY_AGG(c.name->>'en') as course_names,
                ARRAY_AGG(co.section_code) as section_codes,
                ARRAY_AGG(co.id::text) as offering_ids,
                ARRAY_AGG(co.current_enrollment) as enrollments
            FROM course_instructors ci
            JOIN users u ON ci.instructor_id = u.id
            JOIN course_offerings co ON ci.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            JOIN class_schedules cs ON cs.course_offering_id = co.id
            WHERE u.username = %s
            GROUP BY u.id, cs.day_of_week, cs.start_time, cs.end_time
            HAVING COUNT(*) > 1
            ORDER BY cs.day_of_week, cs.start_time
        """, [teacher['username']])
        
        conflicts = cur.fetchall()
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for i, conflict in enumerate(conflicts, 1):
            print(f"\n  Conflict #{i}: {days[conflict['day_of_week']]} {conflict['start_time']}-{conflict['end_time']}")
            print(f"  {conflict['conflict_count']} classes scheduled at same time:")
            
            for j in range(conflict['conflict_count']):
                print(f"\n    Class {j+1}:")
                print(f"      Schedule ID: {conflict['schedule_ids'][j]}")
                print(f"      Course: {conflict['course_codes'][j]} - {conflict['course_names'][j]}")
                print(f"      Section: {conflict['section_codes'][j]}")
                print(f"      Offering ID: {conflict['offering_ids'][j]}")
                print(f"      Enrollment: {conflict['enrollments'][j]}")
            
            all_conflicts.append({
                'teacher_username': teacher['username'],
                'teacher_name': teacher['teacher_name'],
                'instructor_id': conflict['instructor_id'],
                'day': days[conflict['day_of_week']],
                'day_of_week': conflict['day_of_week'],
                'start_time': str(conflict['start_time']),
                'end_time': str(conflict['end_time']),
                'conflict_count': conflict['conflict_count'],
                'schedule_ids': conflict['schedule_ids'],
                'course_codes': conflict['course_codes'],
                'course_names': conflict['course_names'],
                'section_codes': conflict['section_codes'],
                'offering_ids': conflict['offering_ids'],
                'enrollments': conflict['enrollments']
            })
        
        print("\n" + "-" * 100)
    
    cur.close()
    conn.close()
    
    return all_conflicts

def generate_cleanup_options(conflicts):
    """Generate options for resolving conflicts"""
    print("\n" + "=" * 100)
    print("CONFLICT RESOLUTION OPTIONS")
    print("=" * 100)
    
    print("\nTo resolve these conflicts, we can:")
    print("\n1. KEEP HIGHEST ENROLLMENT: Keep the class with most students, remove others")
    print("2. KEEP FIRST SCHEDULED: Keep the first schedule_id (oldest), remove others")
    print("3. MANUAL SELECTION: Review each conflict and manually choose which to keep")
    print("4. MERGE SECTIONS: Combine all sections into one class (what we did for calendar)")
    
    print("\n" + "=" * 100)
    print(f"Total conflicts to resolve: {len(conflicts)}")
    print("=" * 100)

if __name__ == "__main__":
    conflicts = analyze_all_conflicts()
    generate_cleanup_options(conflicts)
    
    print("\n\n⚠️  WARNING: Do not delete any schedules yet!")
    print("Review the conflicts above and decide on resolution strategy.")
    print("A cleanup script will be provided based on your choice.")
