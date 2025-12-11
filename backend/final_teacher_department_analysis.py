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
            p.first_name,
            p.last_name,
            p.middle_name,
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
        ORDER BY d.name_az, p.last_name
    """)
    
    teachers = cursor.fetchall()
    
    # Group teachers by department
    departments = {}
    unassigned_teachers = []
    
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
        name_parts = [teacher['first_name'], teacher['last_name']]
        if teacher['middle_name']:
            name_parts.append(teacher['middle_name'])
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
        for i, teacher in enumerate(dept_teachers[:10]):  # Show first 10 teachers
            print(f"      {i+1}. {teacher['name']}")
        
        if len(dept_teachers) > 10:
            print(f"      ... and {len(dept_teachers) - 10} more teachers")
        
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


def analyze_organizational_hierarchy():
    """Analyze the organizational hierarchy"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n\n🌳 ORGANIZATIONAL HIERARCHY ANALYSIS:")
    print("="*60)
    
    cursor.execute("""
        WITH RECURSIVE org_tree AS (
            -- Root organizations (no parent)
            SELECT 
                o.id,
                o.parent_id,
                d.name_az as org_name,
                d.short_name_az,
                0 as level,
                CAST(d.name_az AS TEXT) as path
            FROM organizations o
            LEFT JOIN dictionaries d ON o.dictionary_name_id = d.id AND d.active = 1
            WHERE o.parent_id IS NULL AND o.active = 1
            
            UNION ALL
            
            -- Child organizations
            SELECT 
                o.id,
                o.parent_id,
                d.name_az as org_name,
                d.short_name_az,
                ot.level + 1,
                ot.path || ' → ' || COALESCE(d.name_az, 'Unknown')
            FROM organizations o
            LEFT JOIN dictionaries d ON o.dictionary_name_id = d.id AND d.active = 1
            JOIN org_tree ot ON o.parent_id = ot.id
            WHERE o.active = 1 AND ot.level < 5  -- Prevent infinite recursion
        )
        SELECT 
            ot.*,
            COUNT(t.id) as teacher_count
        FROM org_tree ot
        LEFT JOIN teachers t ON t.organization_id = ot.id AND t.active = 1
        GROUP BY ot.id, ot.parent_id, ot.org_name, ot.short_name_az, ot.level, ot.path
        HAVING COUNT(t.id) > 0  -- Only show orgs with teachers
        ORDER BY ot.level, ot.org_name
    """)
    
    hierarchy = cursor.fetchall()
    
    current_level = -1
    for org in hierarchy:
        if org['level'] != current_level:
            current_level = org['level']
            print(f"\n📊 LEVEL {current_level}:")
            print("-" * 40)
        
        indent = "  " * org['level']
        org_name = org['org_name'] or f"Unknown Org (ID: {org['id']})"
        print(f"{indent}🏢 {org_name} ({org['teacher_count']} teachers)")
        if org['short_name_az']:
            print(f"{indent}   📝 Short: {org['short_name_az']}")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    try:
        departments = get_teacher_departments()
        analyze_organizational_hierarchy()
        
        print(f"\n✅ Analysis complete! Found teachers across {len(departments)} departments.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()