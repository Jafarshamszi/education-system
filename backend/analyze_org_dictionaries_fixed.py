#!/usr/bin/env python3
"""
Detailed analysis of organization-dictionary relationships to understand
the department structure for teachers.
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


def analyze_organization_dictionary_structure():
    """Analyze the relationship between organizations and dictionaries"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=== ORGANIZATION-DICTIONARY ANALYSIS ===\n")
    
    # Get sample organizations with correct column names
    print("1. Sample Organizations:")
    cursor.execute("""
        SELECT id, type_id, dictionary_name_id, active, parent_id
        FROM organizations 
        WHERE active = 1 
        ORDER BY id 
        LIMIT 10
    """)
    orgs = cursor.fetchall()
    
    for org in orgs:
        print(f"  • Org ID: {org['id']}")
        print(f"    Type ID: {org['type_id']}")
        print(f"    Dictionary Name ID: {org['dictionary_name_id']}")
        print(f"    Parent ID: {org['parent_id']}")
        print(f"    Active: {org['active']}")
        print()
    
    # Get sample dictionaries
    print("2. Sample Dictionaries:")
    cursor.execute("""
        SELECT id, name, description, dictionary_type, is_active 
        FROM dictionaries 
        WHERE is_active = true 
        ORDER BY id 
        LIMIT 10
    """)
    dicts = cursor.fetchall()
    
    for d in dicts:
        print(f"  • Dict ID: {d['id']}")
        print(f"    Name: {d['name']}")
        print(f"    Description: {d['description']}")
        print(f"    Type: {d['dictionary_type']}")
        print()
    
    # Try to resolve organization names through dictionaries
    print("3. Resolving Organization Names:")
    for org in orgs[:5]:  # Check first 5 organizations
        if org['dictionary_name_id']:
            cursor.execute("""
                SELECT id, name, description, dictionary_type 
                FROM dictionaries 
                WHERE id = %s AND is_active = true
            """, (org['dictionary_name_id'],))
            dict_match = cursor.fetchone()
            
            print(f"  • Organization {org['id']} (dict_id: {org['dictionary_name_id']})")
            if dict_match:
                print(f"    → Name: {dict_match['name']}")
                print(f"    → Description: {dict_match['description']}")
                print(f"    → Type: {dict_match['dictionary_type']}")
            else:
                print(f"    → NO DICTIONARY FOUND")
            print()
    
    # Get teachers with resolved organization names
    print("4. Teachers with Resolved Department Names:")
    cursor.execute("""
        SELECT 
            t.id as teacher_id,
            p.first_name,
            p.last_name,
            p.middle_name,
            t.organization_id,
            d.name as department_name,
            d.description as department_description
        FROM teachers t
        JOIN persons p ON t.person_id = p.id
        LEFT JOIN organizations o ON t.organization_id = o.id AND o.active = 1
        LEFT JOIN dictionaries d ON o.dictionary_name_id = d.id AND d.is_active = true
        WHERE t.active = 1
        ORDER BY d.name, p.last_name
        LIMIT 20
    """)
    teachers_with_depts = cursor.fetchall()
    
    current_dept = None
    for teacher in teachers_with_depts:
        dept_name = teacher['department_name'] or f"Unknown Dept (Org ID: {teacher['organization_id']})"
        
        if dept_name != current_dept:
            print(f"\n📚 DEPARTMENT: {dept_name}")
            if teacher['department_description']:
                print(f"   Description: {teacher['department_description']}")
            print("   " + "="*50)
            current_dept = dept_name
        
        name = f"{teacher['first_name']} {teacher['last_name']}"
        if teacher['middle_name']:
            name += f" {teacher['middle_name']}"
        
        print(f"   • {name}")
    
    # Count teachers by department
    print("\n\n5. Teacher Count by Department:")
    cursor.execute("""
        SELECT 
            d.name as department_name,
            COUNT(t.id) as teacher_count,
            o.id as org_id
        FROM teachers t
        LEFT JOIN organizations o ON t.organization_id = o.id AND o.active = 1
        LEFT JOIN dictionaries d ON o.dictionary_name_id = d.id AND d.is_active = true
        WHERE t.active = 1
        GROUP BY d.name, o.id
        ORDER BY teacher_count DESC
    """)
    dept_counts = cursor.fetchall()
    
    for dept in dept_counts:
        dept_name = dept['department_name'] or f"Unknown Department (Org ID: {dept['org_id']})"
        print(f"  • {dept_name}: {dept['teacher_count']} teachers")
    
    # Check organization hierarchy
    print("\n\n6. Organization Hierarchy (Parent-Child relationships):")
    cursor.execute("""
        WITH org_hierarchy AS (
            SELECT 
                o.id,
                o.parent_id,
                d.name as org_name,
                o.dictionary_name_id,
                COUNT(t.id) as teacher_count
            FROM organizations o
            LEFT JOIN dictionaries d ON o.dictionary_name_id = d.id AND d.is_active = true
            LEFT JOIN teachers t ON t.organization_id = o.id AND t.active = 1
            WHERE o.active = 1
            GROUP BY o.id, o.parent_id, d.name, o.dictionary_name_id
        )
        SELECT 
            parent.org_name as parent_name,
            child.org_name as child_name,
            child.teacher_count
        FROM org_hierarchy child
        LEFT JOIN org_hierarchy parent ON child.parent_id = parent.id
        WHERE child.teacher_count > 0
        ORDER BY parent.org_name, child.org_name
        LIMIT 20
    """)
    hierarchy = cursor.fetchall()
    
    for h in hierarchy:
        parent = h['parent_name'] or "ROOT"
        child = h['child_name'] or f"Unknown (has {h['teacher_count']} teachers)"
        print(f"  • {parent} → {child} ({h['teacher_count']} teachers)")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    try:
        analyze_organization_dictionary_structure()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()