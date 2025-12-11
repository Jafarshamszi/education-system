i#!/usr/bin/env python3
"""
FINAL REPORT: Teacher-Department Analysis for Education System
"""

import psycopg2
from psycopg2.extras import RealDictCursor


def connect_db():
    return psycopg2.connect(
        host="localhost",
        database="edu", 
        user="postgres",
        password="1111",
        cursor_factory=RealDictCursor
    )


def generate_final_report():
    """Generate comprehensive teacher-department report"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("🎓 EDUCATION SYSTEM - TEACHER DEPARTMENT ANALYSIS REPORT")
    print("=" * 80)
    
    # Get complete teacher-department mapping
    cursor.execute("""
        SELECT 
            t.id as teacher_id,
            TRIM(COALESCE(p.firstname, '') || ' ' || COALESCE(p.lastname, '')) as teacher_name,
            t.organization_id,
            o.parent_id,
            org_type.name_az as department_type,
            parent_type.name_az as faculty_type,
            -- Hierarchy: University -> Faculty -> Department
            CASE 
                WHEN org_type.name_az = 'Kafedra' THEN t.organization_id
                WHEN org_type.name_az = 'Fakulte' THEN t.organization_id  
                ELSE NULL
            END as department_id,
            CASE 
                WHEN org_type.name_az = 'Kafedra' THEN o.parent_id
                WHEN org_type.name_az = 'Fakulte' THEN NULL
                ELSE NULL  
            END as faculty_id
        FROM teachers t
        JOIN persons p ON t.person_id = p.id
        LEFT JOIN organizations o ON t.organization_id = o.id AND o.active = 1
        LEFT JOIN dictionaries org_type ON o.type_id = org_type.id AND org_type.active = 1
        LEFT JOIN organizations parent_o ON o.parent_id = parent_o.id AND parent_o.active = 1
        LEFT JOIN dictionaries parent_type ON parent_o.type_id = parent_type.id AND parent_type.active = 1
        WHERE t.active = 1
        ORDER BY 
            org_type.name_az,
            CASE WHEN org_type.name_az = 'Kafedra' THEN o.parent_id ELSE t.organization_id END,
            t.organization_id,
            teacher_name
    """)
    
    teachers = cursor.fetchall()
    
    print(f"\n📊 EXECUTIVE SUMMARY:")
    print(f"   • Total Active Teachers: {len(teachers)}")
    
    # Count by organization type
    type_counts = {}
    for teacher in teachers:
        dept_type = teacher['department_type'] or 'Unknown'
        type_counts[dept_type] = type_counts.get(dept_type, 0) + 1
    
    for dept_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {dept_type}: {count} teachers")
    
    print(f"\n🏛️ ORGANIZATIONAL STRUCTURE:")
    print(f"   University (Universitet) → Faculty (Fakulte) → Department (Kafedra)")
    print(f"   Most teachers are assigned directly to Kafedra (departments)")
    
    # Group teachers by faculty and department
    faculty_structure = {}
    
    for teacher in teachers:
        if teacher['department_type'] == 'Kafedra':
            # Teacher is in a department
            faculty_id = teacher['faculty_id']
            dept_id = teacher['department_id']
            
            if faculty_id not in faculty_structure:
                faculty_structure[faculty_id] = {}
            
            if dept_id not in faculty_structure[faculty_id]:
                faculty_structure[faculty_id][dept_id] = []
            
            faculty_structure[faculty_id][dept_id].append({
                'name': teacher['teacher_name'],
                'id': teacher['teacher_id']
            })
    
    print(f"\n🏢 DEPARTMENT BREAKDOWN:")
    print("=" * 60)
    
    # Get faculty names for better reporting
    faculty_names = {}
    for faculty_id in faculty_structure.keys():
        if faculty_id:
            cursor.execute("""
                SELECT d.name_az, d.name_en 
                FROM organizations o 
                JOIN dictionaries d ON o.type_id = d.id 
                WHERE o.id = %s AND o.active = 1 AND d.active = 1
            """, (faculty_id,))
            result = cursor.fetchone()
            if result:
                faculty_names[faculty_id] = result['name_az'] or result['name_en'] or f"Faculty {faculty_id}"
            else:
                faculty_names[faculty_id] = f"Faculty {faculty_id}"
    
    # Sort faculties by teacher count
    faculty_sizes = [(fid, sum(len(dept_teachers) for dept_teachers in faculty_structure[fid].values())) 
                     for fid in faculty_structure.keys()]
    faculty_sizes.sort(key=lambda x: x[1], reverse=True)
    
    for faculty_id, total_teachers in faculty_sizes:
        faculty_name = faculty_names.get(faculty_id, f"Faculty {faculty_id}")
        print(f"\n🏛️ {faculty_name.upper()} (ID: {faculty_id})")
        print(f"   Total Teachers: {total_teachers}")
        print("   " + "-" * 50)
        
        # Sort departments by teacher count
        dept_sizes = [(dept_id, len(teachers_list)) 
                      for dept_id, teachers_list in faculty_structure[faculty_id].items()]
        dept_sizes.sort(key=lambda x: x[1], reverse=True)
        
        for dept_id, teacher_count in dept_sizes:
            print(f"\n   📚 Kafedra (Department) {dept_id}")
            print(f"      Teachers: {teacher_count}")
            print(f"      Staff:")
            
            dept_teachers = faculty_structure[faculty_id][dept_id]
            for i, teacher in enumerate(dept_teachers[:10], 1):  # Show first 10
                print(f"         {i:2d}. {teacher['name']}")
            
            if len(dept_teachers) > 10:
                print(f"         ... and {len(dept_teachers) - 10} more teachers")
    
    # Handle teachers not in kafedras
    other_teachers = [t for t in teachers if t['department_type'] != 'Kafedra']
    if other_teachers:
        print(f"\n🏢 OTHER ORGANIZATIONAL ASSIGNMENTS:")
        print("=" * 60)
        
        other_by_type = {}
        for teacher in other_teachers:
            org_type = teacher['department_type'] or 'Unknown'
            if org_type not in other_by_type:
                other_by_type[org_type] = []
            other_by_type[org_type].append(teacher)
        
        for org_type, type_teachers in other_by_type.items():
            print(f"\n📋 {org_type.upper()} ({len(type_teachers)} teachers)")
            for teacher in type_teachers[:15]:  # Show first 15
                print(f"   • {teacher['teacher_name']} (Org: {teacher['organization_id']})")
            if len(type_teachers) > 15:
                print(f"   ... and {len(type_teachers) - 15} more teachers")
    
    print(f"\n" + "=" * 80)
    print(f"📋 CONCLUSION:")
    print(f"   • The education system has a 3-level hierarchy: University → Faculty → Department")
    print(f"   • Most teachers ({type_counts.get('Kafedra', 0)}) are assigned to Kafedra (departments)")
    print(f"   • There are {len(faculty_structure)} faculties with multiple departments each")
    print(f"   • {type_counts.get('Universitet', 0)} teachers are assigned at university level")
    print(f"   • {type_counts.get('Fakulte', 0)} teachers are assigned directly to faculty level")
    print(f"=" * 80)
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    try:
        generate_final_report()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()