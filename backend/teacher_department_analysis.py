import psycopg2
from psycopg2.extras import RealDictCursor

def analyze_teacher_departments():
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        database='edu',
        user='postgres',
        password='1111',
        cursor_factory=RealDictCursor
    )
    
    cursor = conn.cursor()
    
    print('=== TEACHER-DEPARTMENT ANALYSIS ===\n')
    
    # Query to get teachers with their department/organization information
    query = """
    SELECT 
        t.id as teacher_id,
        t.person_id,
        t.organization_id,
        p.firstname,
        p.lastname,
        p.patronymic,
        org_dict.name_az as organization_name_az,
        org_dict.name_en as organization_name_en,
        org_dict.name_ru as organization_name_ru,
        pos_dict.name_az as position_name_az,
        pos_dict.name_en as position_name_en,
        staff_dict.name_az as staff_type_az,
        staff_dict.name_en as staff_type_en,
        t.teaching,
        t.active
    FROM teachers t
    LEFT JOIN persons p ON t.person_id = p.id
    LEFT JOIN organizations org ON t.organization_id = org.id
    LEFT JOIN dictionaries org_dict ON org.dictionary_name_id = org_dict.id
    LEFT JOIN dictionaries pos_dict ON t.position_id = pos_dict.id
    LEFT JOIN dictionaries staff_dict ON t.staff_type_id = staff_dict.id
    WHERE t.active = 1
    ORDER BY org_dict.name_az, p.lastname, p.firstname
    LIMIT 50
    """
    
    cursor.execute(query)
    teachers = cursor.fetchall()
    
    print(f"Found {len(teachers)} active teachers\n")
    
    # Group teachers by organization
    departments = {}
    
    for teacher in teachers:
        org_name = teacher['organization_name_az'] or teacher['organization_name_en'] or "Unknown Organization"
        
        if org_name not in departments:
            departments[org_name] = []
        
        teacher_name = f"{teacher['firstname'] or ''} {teacher['lastname'] or ''}".strip()
        if teacher['patronymic']:
            teacher_name += f" {teacher['patronymic']}"
        
        departments[org_name].append({
            'id': teacher['teacher_id'],
            'name': teacher_name,
            'position': teacher['position_name_az'] or teacher['position_name_en'],
            'staff_type': teacher['staff_type_az'] or teacher['staff_type_en'],
            'teaching': teacher['teaching']
        })
    
    # Display results
    print("TEACHERS BY DEPARTMENT/ORGANIZATION:")
    print("="*60)
    
    for dept_name, teachers_list in departments.items():
        print(f"\n📚 {dept_name.upper()}")
        print("-" * 50)
        print(f"Number of teachers: {len(teachers_list)}")
        
        for teacher in teachers_list:
            position_info = f" ({teacher['position']})" if teacher['position'] else ""
            staff_info = f" - {teacher['staff_type']}" if teacher['staff_type'] else ""
            teaching_info = " [Teaching]" if teacher['teaching'] == 1 else ""
            
            print(f"  • {teacher['name']}{position_info}{staff_info}{teaching_info}")
    
    # Get summary statistics
    print(f"\n\n📊 SUMMARY STATISTICS:")
    print("="*40)
    print(f"Total Departments/Organizations: {len(departments)}")
    
    total_teachers = sum(len(teachers_list) for teachers_list in departments.values())
    print(f"Total Active Teachers: {total_teachers}")
    
    # Find largest departments
    largest_depts = sorted(departments.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    print(f"\nTop 5 Largest Departments:")
    for dept_name, teachers_list in largest_depts:
        print(f"  • {dept_name}: {len(teachers_list)} teachers")
    
    # Check if there are more teachers than displayed
    cursor.execute("SELECT COUNT(*) FROM teachers WHERE active = 1")
    total_active = cursor.fetchone()[0]
    
    if total_active > 50:
        print(f"\n⚠️  Note: Showing first 50 teachers out of {total_active} total active teachers")
    
    conn.close()

if __name__ == "__main__":
    analyze_teacher_departments()