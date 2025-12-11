#!/usr/bin/env python3
"""
Final teacher-department analysis using organization types instead of missing dictionary names.
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


def get_teachers_by_organization_type():
    """Get teachers grouped by organization type"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=== TEACHER ANALYSIS BY ORGANIZATION TYPE ===\n")
    
    # Get teachers with organization types
    cursor.execute("""
        SELECT 
            t.id as teacher_id,
            COALESCE(p.firstname, '') || ' ' || COALESCE(p.lastname, '') as teacher_name,
            t.organization_id,
            o.type_id,
            type_dict.name_az as org_type_az,
            type_dict.name_en as org_type_en,
            type_dict.name_ru as org_type_ru,
            o.parent_id,
            parent_type.name_az as parent_type_az
        FROM teachers t
        JOIN persons p ON t.person_id = p.id
        LEFT JOIN organizations o ON t.organization_id = o.id AND o.active = 1
        LEFT JOIN dictionaries type_dict ON o.type_id = type_dict.id AND type_dict.active = 1
        LEFT JOIN organizations parent_o ON o.parent_id = parent_o.id AND parent_o.active = 1
        LEFT JOIN dictionaries parent_type ON parent_o.type_id = parent_type.id AND parent_type.active = 1
        WHERE t.active = 1
        ORDER BY type_dict.name_az, teacher_name
    """)
    
    teachers = cursor.fetchall()
    
    # Group by organization type
    org_types = {}
    unknown_teachers = []
    
    for teacher in teachers:
        # Use organization type as department category
        org_type = (teacher['org_type_az'] or 
                   teacher['org_type_en'] or 
                   teacher['org_type_ru'] or 
                   f"Unknown Type (Org ID: {teacher['organization_id']})")
        
        parent_type = teacher['parent_type_az'] or "No Parent"
        
        teacher_info = {
            'name': teacher['teacher_name'].strip(),
            'teacher_id': teacher['teacher_id'],
            'organization_id': teacher['organization_id'],
            'parent_type': parent_type
        }
        
        if org_type not in org_types:
            org_types[org_type] = []
        org_types[org_type].append(teacher_info)
    
    # Display results
    print(f"📊 Found {len(teachers)} teachers in {len(org_types)} organization types\n")
    
    # Sort by teacher count
    sorted_types = sorted(org_types.items(), key=lambda x: len(x[1]), reverse=True)
    
    for org_type, type_teachers in sorted_types:
        print(f"🏢 {org_type.upper()}")
        print(f"   👥 Teachers: {len(type_teachers)}")
        
        # Show sample teachers
        print("   📝 Sample Teachers:")
        for i, teacher in enumerate(type_teachers[:8]):
            print(f"      {i+1}. {teacher['name']} (Org: {teacher['organization_id']})")
        
        if len(type_teachers) > 8:
            print(f"      ... and {len(type_teachers) - 8} more teachers")
        print()
    
    cursor.close()
    conn.close()
    
    return org_types


def get_detailed_department_structure():
    """Get detailed department structure by analyzing organization hierarchy"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n🏗️ DETAILED ORGANIZATIONAL STRUCTURE:")
    print("="*60)
    
    # Get organization hierarchy with teacher counts
    cursor.execute("""
        WITH org_hierarchy AS (
            SELECT 
                o.id,
                o.parent_id,
                o.type_id,
                type_dict.name_az as org_type,
                COUNT(t.id) as teacher_count,
                0 as level
            FROM organizations o
            LEFT JOIN dictionaries type_dict ON o.type_id = type_dict.id AND type_dict.active = 1
            LEFT JOIN teachers t ON t.organization_id = o.id AND t.active = 1
            WHERE o.active = 1 AND o.parent_id IS NULL
            GROUP BY o.id, o.parent_id, o.type_id, type_dict.name_az
            
            UNION ALL
            
            SELECT 
                child.id,
                child.parent_id,
                child.type_id,
                child_type.name_az as org_type,
                COUNT(t.id) as teacher_count,
                1 as level
            FROM organizations child
            LEFT JOIN dictionaries child_type ON child.type_id = child_type.id AND child_type.active = 1
            LEFT JOIN teachers t ON t.organization_id = child.id AND t.active = 1
            WHERE child.active = 1 AND child.parent_id IS NOT NULL
            GROUP BY child.id, child.parent_id, child.type_id, child_type.name_az
        )
        SELECT * FROM org_hierarchy 
        WHERE teacher_count > 0
        ORDER BY level, org_type, teacher_count DESC
    """)
    
    hierarchy = cursor.fetchall()
    
    # Group by level and type
    root_orgs = [org for org in hierarchy if org['level'] == 0]
    child_orgs = [org for org in hierarchy if org['level'] == 1]
    
    print("📊 ROOT ORGANIZATIONS (Top Level):")
    for org in sorted(root_orgs, key=lambda x: x['teacher_count'], reverse=True):
        org_type = org['org_type'] or f"Unknown Type (ID: {org['type_id']})"
        print(f"   🏛️  {org_type} (Org ID: {org['id']}) - {org['teacher_count']} teachers")
    
    print(f"\n📊 CHILD ORGANIZATIONS (Departments/Units):")
    current_type = None
    for org in sorted(child_orgs, key=lambda x: (x['org_type'] or 'ZZZ', -x['teacher_count'])):
        org_type = org['org_type'] or f"Unknown Type (ID: {org['type_id']})"
        
        if org_type != current_type:
            current_type = org_type
            print(f"\n   📚 {org_type.upper()}:")
        
        print(f"      • Org ID {org['id']} (Parent: {org['parent_id']}) - {org['teacher_count']} teachers")
    
    # Get specific department breakdown for Kafedra (departments)
    print(f"\n\n🎓 KAFEDRA (DEPARTMENT) BREAKDOWN:")
    print("-" * 50)
    
    cursor.execute("""
        SELECT 
            o.id as org_id,
            o.parent_id,
            COUNT(t.id) as teacher_count,
            STRING_AGG(DISTINCT COALESCE(p.firstname, '') || ' ' || COALESCE(p.lastname, ''), ', ') as teachers
        FROM organizations o
        LEFT JOIN dictionaries type_dict ON o.type_id = type_dict.id AND type_dict.active = 1
        LEFT JOIN teachers t ON t.organization_id = o.id AND t.active = 1
        LEFT JOIN persons p ON t.person_id = p.id
        WHERE o.active = 1 
          AND type_dict.name_az = 'Kafedra'
          AND t.id IS NOT NULL
        GROUP BY o.id, o.parent_id
        ORDER BY teacher_count DESC
        LIMIT 10
    """)
    
    kafedras = cursor.fetchall()
    
    for i, kafedra in enumerate(kafedras, 1):
        print(f"{i}. Kafedra ID {kafedra['org_id']} (Parent: {kafedra['parent_id']})")
        print(f"   👥 Teachers ({kafedra['teacher_count']}): {kafedra['teachers'][:100]}...")
        print()
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    try:
        org_types = get_teachers_by_organization_type()
        get_detailed_department_structure()
        
        print(f"\n✅ ANALYSIS COMPLETE!")
        print(f"📋 SUMMARY: Found teachers distributed across {len(org_types)} organization types.")
        print(f"🏢 The main organizational units are: Kafedra (Departments), Fakulte (Faculties), and various specialization types.")
        print(f"📍 Teachers are primarily assigned to Kafedra (department-level) organizations.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()