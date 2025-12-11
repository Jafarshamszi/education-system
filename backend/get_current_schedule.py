import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def get_current_schedule_info():
    try:
        conn = psycopg2.connect(host='localhost', database='edu', user='postgres', password='1111')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("CURRENT SEMESTER CLASS SCHEDULE ANALYSIS")
        print("="*60)
        
        # Get current academic year and active courses
        cursor.execute("""
            SELECT 
                c.id,
                c.code,
                c.start_date,
                sd.name_az as subject_name,
                sd.code as subject_code,
                c.m_hours,
                c.s_hours, 
                c.l_hours,
                c.fm_hours,
                c.student_count,
                c.active,
                c.close_status,
                COUNT(cs.student_id) as enrolled_students,
                COUNT(ct.teacher_id) as assigned_teachers
            FROM course c
            LEFT JOIN education_plan_subject eps ON eps.id = c.education_plan_subject_id
            LEFT JOIN subject_dic sd ON sd.id = eps.subject_id  
            LEFT JOIN course_student cs ON cs.course_id = c.id AND cs.active = 1
            LEFT JOIN course_teacher ct ON ct.course_id = c.id AND ct.active = 1
            WHERE c.active = 1 
            AND c.education_year_id = (
                SELECT MAX(education_year_id) FROM course WHERE active = 1
            )
            GROUP BY c.id, c.code, c.start_date, sd.name_az, sd.code, 
                     c.m_hours, c.s_hours, c.l_hours, c.fm_hours, c.student_count, c.active, c.close_status
            ORDER BY c.start_date DESC, c.code
            LIMIT 20;
        """)
        
        courses = cursor.fetchall()
        print(f"\nACTIVE COURSES ({len(courses)} found):")
        print("-" * 60)
        for course in courses:
            print(f"Course: {course['code']}")
            print(f"  Subject: {course['subject_name']} ({course['subject_code']})")
            print(f"  Hours: M:{course['m_hours']} S:{course['s_hours']} L:{course['l_hours']} FM:{course['fm_hours']}")
            print(f"  Students: {course['enrolled_students']}, Teachers: {course['assigned_teachers']}")
            print(f"  Start Date: {course['start_date']}, Status: {'Active' if course['active'] == 1 else 'Inactive'}")
            print()
        
        # Get teacher assignments for current courses
        cursor.execute("""
            SELECT 
                c.code as course_code,
                p.firstname || ' ' || p.lastname as teacher_name,
                org.name_az as organization_name,
                pos.name_az as position_name,
                ct.lesson_type_id
            FROM course_teacher ct
            JOIN course c ON c.id = ct.course_id
            JOIN teachers t ON t.id = ct.teacher_id
            JOIN persons p ON p.id = t.person_id
            LEFT JOIN organisations org ON org.id = t.organization_id
            LEFT JOIN org_names orgn ON orgn.id = org.org_name_id
            LEFT JOIN dictionaries pos ON pos.id = t.position_id
            WHERE ct.active = 1 
            AND c.active = 1
            AND c.education_year_id = (
                SELECT MAX(education_year_id) FROM course WHERE active = 1
            )
            ORDER BY c.code
            LIMIT 20;
        """)
        
        teachers = cursor.fetchall()
        print(f"\nTEACHER ASSIGNMENTS ({len(teachers)} found):")
        print("-" * 60)
        for teacher in teachers:
            print(f"Course: {teacher['course_code']}")
            print(f"  Teacher: {teacher['teacher_name']}")
            print(f"  Organization: {teacher['organization_name']}")
            print(f"  Position: {teacher['position_name']}")
            print(f"  Lesson Type: {teacher['lesson_type_id']}")
            print()
            
        # Check for any timetable data
        cursor.execute("""
            SELECT COUNT(*) as count FROM dynamic_timetable_details WHERE active = 1;
        """)
        timetable_count = cursor.fetchone()['count']
        print(f"\nTIMETABLE ENTRIES: {timetable_count}")
        
        # Get dictionary values for lesson types, days, etc.
        cursor.execute("""
            SELECT id, name_az, name_en, type_id 
            FROM dictionaries 
            WHERE type_id IN (110000111, 110000112, 110000113, 110000114)
            ORDER BY type_id, id;
        """)
        dict_values = cursor.fetchall()
        print(f"\nDICTIONARY VALUES ({len(dict_values)} found):")
        print("-" * 60)
        for val in dict_values:
            print(f"ID: {val['id']}, Name: {val['name_az']}, Type: {val['type_id']}")
        
        conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    get_current_schedule_info()