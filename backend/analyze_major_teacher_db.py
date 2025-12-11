#!/usr/bin/env python3
"""
Analyze major-kafedra-teacher relationships
"""
import sys
sys.path.append('/home/axel/Developer/Education-system/backend')

from app.core.database import sync_engine
from sqlalchemy import text

print("=" * 80)
print("MAJOR-KAFEDRA-TEACHER RELATIONSHIP ANALYSIS")
print("=" * 80)

with sync_engine.connect() as conn:
    
    # 1. Check teachers table structure
    print("\n1. TEACHERS TABLE - SAMPLE DATA:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT id, person_id, organization_id, active
        FROM teachers
        WHERE active = 1
        LIMIT 5
    """))
    for row in result:
        print(f"Teacher ID: {row[0]}, Person: {row[1]}, Org: {row[2]}, Active: {row[3]}")
    
    # 2. Check education_plan_subject for kafedra_id
    print("\n2. EDUCATION_PLAN_SUBJECT - CHECK KAFEDRA FIELD:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'education_plan_subject'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  {row[0]:30} {row[1]}")
    
    # 3. Sample education_plan_subject data
    print("\n3. EDUCATION_PLAN_SUBJECT - SAMPLE DATA:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT id, subject_id, subject_group_id
        FROM education_plan_subject
        WHERE active = 1
        LIMIT 5
    """))
    for row in result:
        print(f"EPS ID: {row[0]}, Subject: {row[1]}, Group: {row[2]}")
    
    # 4. Check subject_group table
    print("\n4. SUBJECT_GROUP TABLE:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'subject_group'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  {row[0]:30} {row[1]}")
    
    # 5. Sample subject_group data
    print("\n5. SUBJECT_GROUP - SAMPLE DATA:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT id, name_az, kafedra_id
        FROM subject_group
        WHERE active = 1 AND kafedra_id IS NOT NULL
        LIMIT 10
    """))
    for row in result:
        print(f"Group {row[0]}: {row[1]} - Kafedra: {row[2]}")
    
    # 6. Link subject_group kafedra to organization table
    print("\n6. KAFEDRA FROM SUBJECT_GROUP -> ORGANIZATION:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT sg.kafedra_id, o.name_az, o.type_id, 
               COUNT(DISTINCT sg.id) as subject_groups
        FROM subject_group sg
        INNER JOIN organization o ON o.id = sg.kafedra_id
        WHERE sg.kafedra_id IS NOT NULL AND o.active = 1 AND sg.active = 1
        GROUP BY sg.kafedra_id, o.name_az, o.type_id
        LIMIT 10
    """))
    for row in result:
        msg = f"Kafedra {row[0]}: {row[1]} (Type: {row[2]}, Groups: {row[3]})"
        print(msg)
    
    # 7. Teachers by kafedra/organization
    print("\n7. TEACHERS COUNT BY ORGANIZATION (potential kafedra):")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT o.id, o.name_az, o.type_id, COUNT(t.id) as teacher_count
        FROM organization o
        LEFT JOIN teachers t ON t.organization_id = o.id AND t.active = 1
        WHERE o.active = 1
        GROUP BY o.id, o.name_az, o.type_id
        HAVING COUNT(t.id) > 0
        ORDER BY teacher_count DESC
        LIMIT 15
    """))
    for row in result:
        msg = f"{row[1][:50]:50} Type:{row[2]:3} - {row[3]:3} teachers"
        print(msg)
    
    # 6. Organization types
    print("\n6. ORGANIZATION TYPES:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT id, name_az, name_en
        FROM organization_type_dic
        ORDER BY id
    """))
    for row in result:
        print(f"Type {row[0]}: {row[1]} ({row[2]})")
    
    # 9. Course to kafedra relationship through subject_group
    print("\n9. COURSE -> EDUCATION_PLAN_SUBJECT -> SUBJECT_GROUP -> KAFEDRA:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT c.id as course_id, c.code,
               eps.id as eps_id, sg.id as sg_id, sg.kafedra_id,
               o.name_az as kafedra_name
        FROM course c
        LEFT JOIN education_plan_subject eps 
            ON eps.id = c.education_plan_subject_id
        LEFT JOIN subject_group sg ON sg.id = eps.subject_group_id
        LEFT JOIN organization o ON o.id = sg.kafedra_id
        WHERE c.active = 1 AND sg.kafedra_id IS NOT NULL
        LIMIT 10
    """))
    for row in result:
        msg = f"Course {row[1]:10} -> EPS {row[2]:5} -> SG {row[3]:5} "
        msg += f"-> Kafedra {row[4]:5} ({row[5]})"
        print(msg)
    
    # 10. Check if we can link course -> kafedra -> teachers
    print("\n10. COMPLETE CHAIN: COURSE -> SUBJECT_GROUP -> KAFEDRA -> TEACHERS:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT c.code as course_code,
               sg.kafedra_id,
               o.name_az as kafedra_name,
               COUNT(DISTINCT t.id) as available_teachers
        FROM course c
        INNER JOIN education_plan_subject eps 
            ON eps.id = c.education_plan_subject_id
        INNER JOIN subject_group sg ON sg.id = eps.subject_group_id
        INNER JOIN organization o ON o.id = sg.kafedra_id
        LEFT JOIN teachers t 
            ON t.organization_id = sg.kafedra_id AND t.active = 1
        WHERE c.active = 1 AND sg.kafedra_id IS NOT NULL
        GROUP BY c.code, sg.kafedra_id, o.name_az
        HAVING COUNT(DISTINCT t.id) > 0
        LIMIT 10
    """))
    for row in result:
        msg = f"Course {row[0]:10} -> Kafedra: {row[2][:40]:40} "
        msg += f"-> {row[3]} teachers"
        print(msg)
    
    # 11. Check subject_dic for major/specialization info
    print("\n11. SUBJECT_DIC - POTENTIAL MAJOR/SPECIALIZATION INFO:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT id, name_az, code
        FROM subject_dic
        WHERE active = 1
        LIMIT 10
    """))
    for row in result:
        print(f"Subject {row[0]:5}: {row[1][:50]:50} Code: {row[2]}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
