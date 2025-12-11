import psycopg2
from psycopg2.extras import RealDictCursor

def analyze_class_schedule():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='edu',
            user='postgres',
            password='1111'
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== CLASS SCHEDULE DATABASE ANALYSIS ===")
        print()
        
        # Get current active courses with proper joins
        print("1. ACTIVE COURSES FOR CURRENT SEMESTER:")
        print("-" * 50)
        cursor.execute("""
            SELECT 
                c.id,
                c.code,
                c.start_date,
                c.end_date,
                c.m_hours,
                c.s_hours,
                c.l_hours,
                c.fm_hours,
                c.student_count,
                sd.name_az as subject_name,
                sd.code as subject_code,
                COUNT(DISTINCT cs.student_id) as enrolled_students,
                COUNT(DISTINCT ct.teacher_id) as assigned_teachers
            FROM course c
            LEFT JOIN education_plan_subject eps ON eps.id = c.education_plan_subject_id
            LEFT JOIN subject_dic sd ON sd.id = eps.subject_id
            LEFT JOIN course_student cs ON cs.course_id = c.id AND cs.active = 1
            LEFT JOIN course_teacher ct ON ct.course_id = c.id AND ct.active = 1
            WHERE c.active = 1 
            AND c.start_date >= '2024-09-01'
            GROUP BY c.id, c.code, c.start_date, c.end_date, c.m_hours, 
                     c.s_hours, c.l_hours, c.fm_hours, c.student_count, 
                     sd.name_az, sd.code
            ORDER BY c.start_date DESC, c.code
            LIMIT 10
        """)
        
        courses = cursor.fetchall()
        print(f"Found {len(courses)} active courses:")
        for course in courses:
            print(f"• {course['code']}")
            if course['subject_name']:
                print(f"  Subject: {course['subject_name']} ({course['subject_code']})")
            print(f"  Dates: {course['start_date']} to {course['end_date']}")
            print(f"  Hours: M:{course['m_hours']} S:{course['s_hours']} L:{course['l_hours']}")
            print(f"  Students: {course['enrolled_students']}, Teachers: {course['assigned_teachers']}")
            print()
        
        # Get teacher details
        print("2. TEACHER ASSIGNMENTS:")
        print("-" * 50)
        cursor.execute("""
            SELECT 
                c.code as course_code,
                p.firstname || ' ' || p.lastname as teacher_name,
                orgn.name_az as organization_name,
                d.name_az as position_name,
                ct.lesson_type_id
            FROM course_teacher ct
            JOIN course c ON c.id = ct.course_id
            JOIN teachers t ON t.id = ct.teacher_id
            JOIN persons p ON p.id = t.person_id
            LEFT JOIN organisations org ON org.id = t.organization_id
            LEFT JOIN org_names orgn ON orgn.id = org.org_name_id
            LEFT JOIN dictionaries d ON d.id = t.position_id
            WHERE ct.active = 1 
            AND c.active = 1
            AND c.start_date >= '2024-09-01'
            ORDER BY c.code
            LIMIT 10
        """)
        
        teachers = cursor.fetchall()
        for teacher in teachers:
            print(f"• {teacher['course_code']}")
            print(f"  Teacher: {teacher['teacher_name']}")
            print(f"  Organization: {teacher['organization_name']}")
            print(f"  Position: {teacher['position_name']}")
            print()
            
        # Get lesson types and time info
        print("3. LESSON TYPES & SCHEDULE INFO:")
        print("-" * 50)
        cursor.execute("""
            SELECT DISTINCT 
                d.id,
                d.name_az as lesson_type_name
            FROM dictionaries d
            JOIN course_teacher ct ON ct.lesson_type_id = d.id
            JOIN course c ON c.id = ct.course_id
            WHERE c.active = 1 
            AND c.start_date >= '2024-09-01'
            ORDER BY d.id
        """)
        
        lesson_types = cursor.fetchall()
        print("Lesson Types found:")
        for lt in lesson_types:
            print(f"• ID: {lt['id']} - {lt['lesson_type_name']}")
        print()
        
        # Check academic schedule structure
        print("4. ACADEMIC SCHEDULE STRUCTURE:")
        print("-" * 50)
        cursor.execute("""
            SELECT 
                asd.id,
                asd.start_date,
                asd.end_date,
                asd.name_az,
                COUNT(c.id) as course_count
            FROM academic_schedule_details asd
            LEFT JOIN course c ON c.academic_schedule_details_id = asd.id
            WHERE asd.active = 1
            GROUP BY asd.id, asd.start_date, asd.end_date, asd.name_az
            ORDER BY asd.start_date DESC
            LIMIT 5
        """)
        
        schedules = cursor.fetchall()
        print("Academic Schedule Details:")
        for sched in schedules:
            print(f"• {sched['name_az']}")
            print(f"  Period: {sched['start_date']} to {sched['end_date']}")
            print(f"  Courses: {sched['course_count']}")
            print()
        
        # Get sample room/location data if exists
        print("5. LOCATIONS & ROOMS:")
        print("-" * 50)
        cursor.execute("""
            SELECT DISTINCT 
                room_id,
                COUNT(*) as usage_count
            FROM dynamic_timetable_details 
            WHERE room_id IS NOT NULL
            GROUP BY room_id
            LIMIT 10
        """)
        
        rooms = cursor.fetchall()
        if rooms:
            print("Rooms found in timetable:")
            for room in rooms:
                print(f"• Room ID: {room['room_id']} (used {room['usage_count']} times)")
        else:
            print("No room data found in dynamic_timetable_details")
        
        conn.close()
        
    except Exception as e:
        print(f'Database Error: {e}')

if __name__ == "__main__":
    analyze_class_schedule()