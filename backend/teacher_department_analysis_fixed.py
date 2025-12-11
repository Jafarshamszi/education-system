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
    
    # First, let's check what organization data we have
    print("Checking organization structure...")
    
    # Check organizations table
    cursor.execute("SELECT COUNT(*) as count FROM organizations WHERE active = 1")
    org_count = cursor.fetchone()['count']
    print(f"Active organizations: {org_count}")
    
    # Check dictionary entries for organizations
    cursor.execute("""
        SELECT d.id, d.name_az, d.name_en, d.name_ru 
        FROM dictionaries d 
        JOIN organizations o ON d.id = o.dictionary_name_id 
        WHERE o.active = 1 
        LIMIT 10
    """)
    org_names = cursor.fetchall()
    print(f"Organization names found: {len(org_names)}")
    for org in org_names:
        print(f"  - {org['name_az'] or org['name_en'] or org['name_ru']}")
    
    print("\n" + "="*60)
    
    # Query to get teachers with their department/organization information
    query = """
    SELECT 
        t.id as teacher_id,
        t.person_id,
        t.organization_id,
        t.position_id,
        t.staff_type_id,
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
    ORDER BY t.organization_id, p.lastname, p.firstname
    LIMIT 50
    """
    
    cursor.execute(query)
    teachers = cursor.fetchall()
    
    print(f"Found {len(teachers)} active teachers\n")
    
    # Let's also check what organization_ids we have in teachers
    cursor.execute("""
        SELECT DISTINCT t.organization_id, COUNT(*) as teacher_count
        FROM teachers t 
        WHERE t.active = 1 
        GROUP BY t.organization_id 
        ORDER BY teacher_count DESC
    """)
    org_distribution = cursor.fetchall()
    print("Organization ID distribution:")
    for org in org_distribution:
        org_id = org['organization_id']
        count = org['teacher_count']
        print(f"  Organization ID {org_id}: {count} teachers")
    
    print("\n" + "="*60)
    
    # Group teachers by organization
    departments = {}
    
    for teacher in teachers:
        # Try different ways to get organization name
        org_name = (teacher['organization_name_az'] or 
                   teacher['organization_name_en'] or 
                   teacher['organization_name_ru'])
        
        if not org_name:
            org_id = teacher['organization_id']
            if org_id:
                org_name = f"Organization ID: {org_id}"
            else:
                org_name = "No Organization Assigned"
        
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
            'teaching': teacher['teaching'],
            'org_id': teacher['organization_id']
        })
    
    # Display results
    print("TEACHERS BY DEPARTMENT/ORGANIZATION:")
    print("="*60)
    
    for dept_name, teachers_list in departments.items():
        print(f"\n📚 {dept_name.upper()}")
        print("-" * 50)
        print(f"Number of teachers: {len(teachers_list)}")
        
        # Show first few teachers as example
        display_count = min(10, len(teachers_list))
        for i, teacher in enumerate(teachers_list[:display_count]):
            position_info = f" ({teacher['position']})" if teacher['position'] else ""
            staff_info = f" - {teacher['staff_type']}" if teacher['staff_type'] else ""
            teaching_info = " [Teaching]" if teacher['teaching'] == 1 else ""
            org_info = f" [Org ID: {teacher['org_id']}]" if teacher['org_id'] else ""
            
            print(f"  • {teacher['name']}{position_info}{staff_info}{teaching_info}{org_info}")
        
        if len(teachers_list) > display_count:
            print(f"  ... and {len(teachers_list) - display_count} more teachers")
    
    # Get summary statistics
    print(f"\n\n📊 SUMMARY STATISTICS:")
    print("="*40)
    print(f"Total Departments/Organizations: {len(departments)}")
    
    total_teachers = sum(len(teachers_list) for teachers_list in departments.values())
    print(f"Total Active Teachers (displayed): {total_teachers}")
    
    # Find largest departments
    largest_depts = sorted(departments.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    print(f"\nTop 5 Largest Departments:")
    for dept_name, teachers_list in largest_depts:
        print(f"  • {dept_name}: {len(teachers_list)} teachers")
    
    # Check total count
    cursor.execute("SELECT COUNT(*) as total FROM teachers WHERE active = 1")
    total_active = cursor.fetchone()['total']
    
    if total_active > 50:
        print(f"\n⚠️  Note: Showing first 50 teachers out of {total_active} total active teachers")
    
    conn.close()


if __name__ == "__main__":
    analyze_teacher_departments()