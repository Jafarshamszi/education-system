#!/usr/bin/env python3
"""
Complete teacher-department analysis with correct database schema.
"""

import psycopg2
from psycopg2.extras import RealDictCursor


def connect_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(
        host="localhost",
        database="edu",
        user="postgres",
        password="1111",
        cursor_factory=RealDictCursor
    )


def get_teacher_departments():
    """Get comprehensive teacher-department mapping"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=== COMPLETE TEACHER-DEPARTMENT ANALYSIS ===\n")
    
    # Get teachers with their department names resolved
    print("🔍 Analyzing teacher-department relationships...\n")
    
    cursor.execute("""
        SELECT 
            t.id as teacher_id,
            p.firstname,
            p.lastname,
            p.patronymic,
            t.organization_id,
            o.parent_id,
            d.name_az as department_name_az,
            d.name_en as department_name_en,
            d.name_ru as department_name_ru,
            d.short_name_az,
            d.code as department_code,
            parent_d.name_az as parent_dept_name_az,
            parent_d.name_en as parent_dept_name_en
        FROM teachers t
        JOIN persons p ON t.person_id = p.id
        LEFT JOIN organizations o ON t.organization_id = o.id AND o.active = 1
        LEFT JOIN dictionaries d ON o.dictionary_name_id = d.id AND d.active = 1
        LEFT JOIN organizations parent_o ON o.parent_id = parent_o.id AND parent_o.active = 1
        LEFT JOIN dictionaries parent_d ON parent_o.dictionary_name_id = parent_d.id AND parent_d.active = 1
        WHERE t.active = 1
        ORDER BY d.name_az, p.lastname
    """)
    
    teachers = cursor.fetchall()
    
    # Group teachers by department
    departments = {}
    
    for teacher in teachers:
        # Use Azerbaijani name as primary, fall back to English, then Russian
        dept_name = (teacher['department_name_az'] or 
                    teacher['department_name_en'] or 
                    teacher['department_name_ru'] or 
                    f"Unknown Department (Org ID: {teacher['organization_id']})")
        
        parent_dept = (teacher['parent_dept_name_az'] or 
                      teacher['parent_dept_name_en'] or 
                      "No Parent")
        
        # Build teacher name
        name_parts = [teacher['firstname'], teacher['lastname']]
        if teacher['patronymic']:
            name_parts.append(teacher['patronymic'])
        teacher_name = ' '.join(filter(None, name_parts))
        
        teacher_info = {
            'name': teacher_name,
            'teacher_id': teacher['teacher_id'],
            'organization_id': teacher['organization_id'],
            'department_code': teacher['department_code'],
            'parent_department': parent_dept
        }
        
        if dept_name not in departments:
            departments[dept_name] = []
        departments[dept_name].append(teacher_info)
    
    # Display results
    print(f"📊 Found {len(teachers)} active teachers in {len(departments)} departments\n")
    
    # Sort departments by teacher count
    sorted_depts = sorted(departments.items(), key=lambda x: len(x[1]), reverse=True)
    
    for dept_name, dept_teachers in sorted_depts[:15]:  # Show top 15 departments
        print(f"🏢 {dept_name}")
        print(f"   👥 Teachers: {len(dept_teachers)}")
        
        if dept_teachers[0]['department_code']:
            print(f"   📋 Code: {dept_teachers[0]['department_code']}")
        
        if dept_teachers[0]['parent_department'] != "No Parent":
            print(f"   🔗 Parent: {dept_teachers[0]['parent_department']}")
        
        print("   📝 Teachers:")
        for i, teacher in enumerate(dept_teachers[:8]):  # Show first 8 teachers
            print(f"      {i+1}. {teacher['name']}")
        
        if len(dept_teachers) > 8:
            print(f"      ... and {len(dept_teachers) - 8} more teachers")
        
        print()
    
    # Summary statistics
    print("\n📈 SUMMARY STATISTICS:")
    print("="*50)
    
    # Department size distribution
    dept_sizes = [len(teachers) for teachers in departments.values()]
    print(f"📊 Department Statistics:")
    print(f"   • Total Departments: {len(departments)}")
    print(f"   • Total Teachers: {sum(dept_sizes)}")
    print(f"   • Largest Department: {max(dept_sizes)} teachers")
    print(f"   • Smallest Department: {min(dept_sizes)} teachers")
    print(f"   • Average Department Size: {sum(dept_sizes) / len(dept_sizes):.1f} teachers")
    
    # Top 5 largest departments summary
    print(f"\n🏆 TOP 5 LARGEST DEPARTMENTS:")
    for i, (dept_name, dept_teachers) in enumerate(sorted_depts[:5], 1):
        short_name = dept_name[:60] + "..." if len(dept_name) > 60 else dept_name
        print(f"   {i}. {short_name}: {len(dept_teachers)} teachers")
    
    # Organizations without names
    unknown_count = sum(1 for dept_name in departments.keys() if "Unknown Department" in dept_name)
    if unknown_count > 0:
        print(f"\n⚠️  Warning: {unknown_count} organization(s) without resolved names")
    
    cursor.close()
    conn.close()
    
    return departments


def export_department_data():
    """Export department data to a simple format for further analysis"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n📄 EXPORT DATA FOR ANALYSIS:")
    print("="*50)
    
    cursor.execute("""
        SELECT 
            t.id as teacher_id,
            COALESCE(p.firstname, '') || ' ' || COALESCE(p.lastname, '') as teacher_name,
            t.organization_id,
            COALESCE(d.name_az, d.name_en, d.name_ru, 'Unknown') as department_name,
            d.code as department_code,
            COALESCE(parent_d.name_az, parent_d.name_en, 'No Parent') as parent_department
        FROM teachers t
        JOIN persons p ON t.person_id = p.id
        LEFT JOIN organizations o ON t.organization_id = o.id AND o.active = 1
        LEFT JOIN dictionaries d ON o.dictionary_name_id = d.id AND d.active = 1
        LEFT JOIN organizations parent_o ON o.parent_id = parent_o.id AND parent_o.active = 1
        LEFT JOIN dictionaries parent_d ON parent_o.dictionary_name_id = parent_d.id AND parent_d.active = 1
        WHERE t.active = 1
        ORDER BY department_name, teacher_name
    """)
    
    teachers = cursor.fetchall()
    
    # Create CSV-like output
    print("Teacher Name | Department | Org ID | Dept Code | Parent Department")
    print("-" * 80)
    
    for teacher in teachers[:50]:  # Show first 50 for readability
        teacher_name = teacher['teacher_name'].strip()
        dept_name = teacher['department_name'][:30]
        org_id = str(teacher['organization_id'])
        dept_code = teacher['department_code'] or 'N/A'
        parent_dept = teacher['parent_department'][:25]
        
        print(f"{teacher_name:<25} | {dept_name:<20} | {org_id:<10} | {dept_code:<8} | {parent_dept}")
    
    if len(teachers) > 50:
        print(f"\n... and {len(teachers) - 50} more teachers")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    try:
        departments = get_teacher_departments()
        export_department_data()
        
        print(f"\n✅ Analysis complete! Found teachers across {len(departments)} departments.")
        print("📁 The data above shows which teachers belong to which departments.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()