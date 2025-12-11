import psycopg2
from psycopg2.extras import RealDictCursor

def get_schedule_data():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='edu', 
            user='postgres',
            password='1111'
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== CURRENT SEMESTER CLASS SCHEDULE ===")
        print()
        
        # Get current active courses 
        cursor.execute("""
            SELECT 
                c.id,
                c.code,
                c.start_date,
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
            GROUP BY c.id, c.code, c.start_date, c.m_hours, c.s_hours, 
                     c.l_hours, c.fm_hours, c.student_count, sd.name_az, sd.code
            ORDER BY c.start_date DESC, c.code
            LIMIT 15
        """)
        
        courses = cursor.fetchall()
        print(f"ACTIVE COURSES ({len(courses)} found):")
        print("-" * 60)
        
        for course in courses:
            print(f"📚 {course['code']}")
            if course['subject_name']:
                print(f"   Subject: {course['subject_name']} ({course['subject_code']})")
            print(f"   Start: {course['start_date']}")
            print(f"   Hours: Lecture:{course['m_hours']} Seminar:{course['s_hours']} Lab:{course['l_hours']} Final:{course['fm_hours']}")
            print(f"   👥 Students: {course['enrolled_students']} | 👨‍🏫 Teachers: {course['assigned_teachers']}")
            print()
        
        # Get detailed teacher info
        print("\nTEACHER ASSIGNMENTS:")
        print("-" * 60)
        cursor.execute("""
            SELECT 
                c.code as course_code,
                p.firstname || ' ' || p.lastname as teacher_name,
                orgn.name_az as organization_name,
                d.name_az as position_name,
                lt.name_az as lesson_type_name
            FROM course_teacher ct
            JOIN course c ON c.id = ct.course_id
            JOIN teachers t ON t.id = ct.teacher_id
            JOIN persons p ON p.id = t.person_id
            LEFT JOIN organisations org ON org.id = t.organization_id
            LEFT JOIN org_names orgn ON orgn.id = org.org_name_id  
            LEFT JOIN dictionaries d ON d.id = t.position_id
            LEFT JOIN dictionaries lt ON lt.id = ct.lesson_type_id
            WHERE ct.active = 1 
            AND c.active = 1
            AND c.start_date >= '2024-09-01'
            ORDER BY c.code
            LIMIT 10
        """)
        
        teachers = cursor.fetchall()
        for teacher in teachers:
            print(f"👨‍🏫 {teacher['teacher_name']}")
            print(f"    Course: {teacher['course_code']}")
            print(f"    Organization: {teacher['organization_name']}")
            print(f"    Position: {teacher['position_name']}")
            print(f"    Lesson Type: {teacher['lesson_type_name']}")
            print()
            
        # Get student enrollment details
        print("\nSTUDENT ENROLLMENTS:")
        print("-" * 60)
        cursor.execute("""
            SELECT 
                c.code as course_code,
                p.firstname || ' ' || p.lastname as student_name,
                s.student_id_number,
                sp.name_az as specialty_name
            FROM course_student cs
            JOIN course c ON c.id = cs.course_id
            JOIN students s ON s.id = cs.student_id
            JOIN persons p ON p.id = s.person_id
            LEFT JOIN specialities sp ON sp.id = s.speciality_id
            WHERE cs.active = 1 
            AND c.active = 1
            AND c.start_date >= '2024-09-01'
            ORDER BY c.code, p.lastname
            LIMIT 20
        """)
        
        students = cursor.fetchall()
        current_course = None
        for student in students:
            if student['course_code'] != current_course:
                current_course = student['course_code']
                print(f"📚 {current_course}:")
            print(f"   👨‍🎓 {student['student_name']} ({student['student_id_number']})")
            if student['specialty_name']:
                print(f"       Specialty: {student['specialty_name']}")
        
        # Get time slots and schedule structure
        print(f"\n\nACTIVE ACADEMIC PERIODS:")
        print("-" * 60)
        cursor.execute("""
            SELECT DISTINCT
                asd.name_az as period_name,
                asd.start_date,
                TO_CHAR(asd.start_date, 'DD/MM/YYYY') as formatted_start,
                COUNT(c.id) as course_count
            FROM academic_schedule_details asd
            LEFT JOIN course c ON c.academic_schedule_details_id = asd.id 
                AND c.active = 1 AND c.start_date >= '2024-09-01'
            WHERE asd.active = 1
            GROUP BY asd.name_az, asd.start_date
            ORDER BY asd.start_date DESC
            LIMIT 5
        """)
        
        periods = cursor.fetchall()
        for period in periods:
            print(f"📅 {period['period_name']}")
            print(f"    Start: {period['formatted_start']}")
            print(f"    Active Courses: {period['course_count']}")
            print()
        
        conn.close()
        print("✅ Analysis completed successfully!")
        
    except Exception as e:
        print(f'❌ Database Error: {e}')

if __name__ == "__main__":
    get_schedule_data()