#!/usr/bin/env python3
"""
FINAL Analysis: Major-Kafedra-Teacher Relationship
"""
import sys
sys.path.append('/home/axel/Developer/Education-system/backend')

from app.core.database import sync_engine
from sqlalchemy import text

print("=" * 80)
print("FINAL MAJOR-KAFEDRA-TEACHER RELATIONSHIP ANALYSIS")
print("=" * 80)

with sync_engine.connect() as conn:
    
    # 1. Check education_plan_subject_group structure
    print("\n1. EDUCATION_PLAN_SUBJECT_GROUP TABLE STRUCTURE:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'education_plan_subject_group'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  {row[0]:30} {row[1]}")
    
    # 2. Sample data from education_plan_subject_group
    print("\n2. SAMPLE EDUCATION_PLAN_SUBJECT_GROUP DATA:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT *
        FROM education_plan_subject_group
        WHERE active = 1
        LIMIT 5
    """))
    for row in result:
        print(f"  ID: {row.id if hasattr(row, 'id') else 'N/A'}")
        for key in row._mapping.keys():
            if row._mapping[key] is not None:
                print(f"    {key}: {row._mapping[key]}")
        print()
    
    # 3. Check if kafedra_id exists
    print("\n3. CHECKING FOR KAFEDRA RELATIONSHIP:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name IN ('education_plan_subject_group', 'education_plan_subject', 'subject_dic')
        AND column_name LIKE '%kafed%'
    """))
    kafedra_columns = list(result)
    if kafedra_columns:
        for row in kafedra_columns:
            print(f"  Found: {row[0]}")
    else:
        print("  No kafedra_id column found in these tables")
    
    # 4. Check organization table for departments/kafedra
    print("\n4. ORGANIZATION TYPES (looking for kafedra/departments):")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT DISTINCT o.type_id, otd.name_az as type_name, 
               COUNT(o.id) as org_count
        FROM organization o
        LEFT JOIN organization_type_dic otd ON otd.id = o.type_id
        WHERE o.active = 1
        GROUP BY o.type_id, otd.name_az
        ORDER BY o.type_id
    """))
    for row in result:
        print(f"  Type {row[0]}: {row[1]:40} - {row[2]} organizations")
    
    # 5. Check how teachers are linked to organizations
    print("\n5. TEACHER-ORGANIZATION DISTRIBUTION:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT o.type_id, otd.name_az as type_name,
               COUNT(DISTINCT t.id) as teacher_count
        FROM teachers t
        INNER JOIN organization o ON o.id = t.organization_id
        LEFT JOIN organization_type_dic otd ON otd.id = o.type_id
        WHERE t.active = 1 AND o.active = 1
        GROUP BY o.type_id, otd.name_az
        ORDER BY teacher_count DESC
    """))
    for row in result:
        print(f"  Type {row[0]} ({row[1]:30}): {row[2]} teachers")
    
    # 6. Sample organizations with teachers (kafedra candidates)
    print("\n6. TOP ORGANIZATIONS WITH TEACHERS (potential kafedra):")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT o.id, o.name_az, o.type_id, 
               COUNT(DISTINCT t.id) as teacher_count
        FROM organization o
        INNER JOIN teachers t ON t.organization_id = o.id AND t.active = 1
        WHERE o.active = 1
        GROUP BY o.id, o.name_az, o.type_id
        ORDER BY teacher_count DESC
        LIMIT 20
    """))
    for row in result:
        print(f"  [{row[2]}] {row[1][:50]:50} - {row[3]:3} teachers")
    
    # 7. Check education_plan_subject to see full chain
    print("\n7. EDUCATION_PLAN_SUBJECT RELATIONSHIPS:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT eps.id, eps.subject_id, eps.subject_group_id,
               sd.name_az as subject_name
        FROM education_plan_subject eps
        LEFT JOIN subject_dic sd ON sd.id = eps.subject_id
        WHERE eps.active = 1
        LIMIT 5
    """))
    for row in result:
        print(f"  EPS {row[0]}: Subject={row[1]}, Group={row[2]}")
        print(f"    Subject Name: {row[3]}")
    
    # 8. Try to find the complete chain: course -> subject -> organization/kafedra
    print("\n8. COURSE -> SUBJECT -> ORGANIZATION CHAIN:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT c.id, c.code,
               eps.subject_id,
               sd.name_az as subject_name,
               sd.kafedra_id,
               o.name_az as org_name
        FROM course c
        INNER JOIN education_plan_subject eps ON eps.id = c.education_plan_subject_id
        INNER JOIN subject_dic sd ON sd.id = eps.subject_id
        LEFT JOIN organization o ON o.id = sd.kafedra_id
        WHERE c.active = 1 AND sd.kafedra_id IS NOT NULL
        LIMIT 10
    """))
    found_chain = False
    for row in result:
        found_chain = True
        print(f"  Course {row[1]}: {row[3][:40]:40}")
        print(f"    -> Kafedra: {row[5]}")
    
    if not found_chain:
        print("  No courses found with kafedra_id in subject_dic")
        print("  Checking subject_dic for kafedra_id column...")
        
        result2 = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'subject_dic'
            AND column_name LIKE '%kafed%'
        """))
        has_kafedra = list(result2)
        if has_kafedra:
            print(f"  ✓ Found column: {has_kafedra[0][0]}")
        else:
            print("  ✗ No kafedra column in subject_dic")
    
    # 9. Check alternative: organization hierarchy
    print("\n9. ORGANIZATION HIERARCHY (parent-child):")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT parent.id as parent_id, parent.name_az as parent_name,
               parent.type_id as parent_type,
               COUNT(DISTINCT child.id) as child_count
        FROM organization parent
        INNER JOIN organization child ON child.parent_id = parent.id
        WHERE parent.active = 1 AND child.active = 1
        GROUP BY parent.id, parent.name_az, parent.type_id
        HAVING COUNT(DISTINCT child.id) > 0
        ORDER BY child_count DESC
        LIMIT 10
    """))
    for row in result:
        print(f"  {row[1][:50]:50} (Type {row[2]}) - {row[3]} children")

print("\n" + "=" * 80)
print("KEY FINDINGS:")
print("=" * 80)
print("1. Teachers are linked to organizations via teachers.organization_id")
print("2. Need to find how to link courses/subjects to organizations/kafedra")
print("3. Check if subject_dic has kafedra_id for the linking")
print("=" * 80)
