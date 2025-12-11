#!/usr/bin/env python3
"""
Data Migration Script: edu -> lms
Migrates all data from the old 'edu' database to the new 'lms' database with improved structure
"""

import psycopg2
import csv
import os
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'postgres',
    'password': '1111'
}

def connect_db(database):
    """Connect to a specific database"""
    config = DB_CONFIG.copy()
    config['database'] = database
    return psycopg2.connect(**config)

def export_table_data(old_conn, query, filename):
    """Export data from old database to CSV"""
    print(f"Exporting {filename}...")
    
    with old_conn.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        os.makedirs('C:/temp/lms_migration', exist_ok=True)
        filepath = f'C:/temp/lms_migration/{filename}'
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)
            writer.writerows(results)
        
        print(f"  Exported {len(results)} rows to {filename}")

def import_table_data(new_conn, table_name, filename, columns=None):
    """Import data from CSV to new database"""
    print(f"Importing {filename} to {table_name}...")
    
    filepath = f'C:/temp/lms_migration/{filename}'
    if not os.path.exists(filepath):
        print(f"  Warning: {filepath} not found, skipping...")
        return
    
    with new_conn.cursor() as cursor:
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # Skip header row
            
            if columns:
                placeholders = ','.join(['%s'] * len(columns))
                query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            else:
                placeholders = ','.join(['%s'] * len(headers))
                query = f"INSERT INTO {table_name} VALUES ({placeholders})"
            
            rows = list(reader)
            if rows:
                try:
                    cursor.executemany(query, rows)
                    new_conn.commit()
                    print(f"  Imported {len(rows)} rows to {table_name}")
                except Exception as e:
                    print(f"  Error importing to {table_name}: {e}")
                    new_conn.rollback()

def main():
    print("Starting data migration from edu to lms database...")
    
    # Connect to databases
    old_conn = connect_db('edu')
    new_conn = connect_db('lms')
    
    try:
        # Phase 1: Export reference data
        print("\n=== Phase 1: Exporting reference data ===")
        
        # Export dictionary types
        export_table_data(old_conn, """
            SELECT DISTINCT 
                type_id as id,
                'TYPE_' || type_id::text as code,
                'Legacy Type ' || type_id as name_az,
                'Legacy Type ' || type_id as name_en,
                'Dictionary type from legacy system' as description,
                TRUE as is_active,
                NOW() as created_at,
                NOW() as updated_at
            FROM dictionaries 
            WHERE type_id IS NOT NULL
            ORDER BY type_id
        """, 'dictionary_types.csv')
        
        # Export dictionaries
        export_table_data(old_conn, """
            SELECT 
                id, type_id, code, name_az, name_en, name_ru, parent_id, 
                0 as sort_order, TRUE as is_active, NOW() as created_at, NOW() as updated_at
            FROM dictionaries 
            WHERE type_id IS NOT NULL
        """, 'dictionaries.csv')
        
        # Export organization types
        export_table_data(old_conn, """
            SELECT DISTINCT
                type_id as id,
                'Organization Type ' || type_id as name_az,
                'Organization Type ' || type_id as name_en,
                'ORG_' || type_id::text as code
            FROM organizations
            WHERE type_id IS NOT NULL
            ORDER BY type_id
        """, 'organization_types.csv')
        
        # Export organizations
        export_table_data(old_conn, """
            SELECT 
                o.id, 
                COALESCE(d.name_az, 'Organization ' || o.id) as name_az,
                COALESCE(d.name_en, 'Organization ' || o.id) as name_en,
                NULL as code, 
                o.parent_id, 
                o.type_id,
                CASE WHEN o.active = 1 THEN TRUE ELSE FALSE END as is_active,
                COALESCE(o.create_date, NOW()) as created_at,
                COALESCE(o.update_date, NOW()) as updated_at
            FROM organizations o
            LEFT JOIN dictionaries d ON o.dictionary_name_id = d.id 
            WHERE o.id IS NOT NULL
        """, 'organizations.csv')
        
        # Export education levels
        export_table_data(old_conn, """
            SELECT DISTINCT
                education_level_id as id,
                'Education Level ' || education_level_id as name_az,
                'Education Level ' || education_level_id as name_en,
                'EDU_' || education_level_id::text as code,
                0 as sort_order
            FROM education_group
            WHERE education_level_id IS NOT NULL
            ORDER BY education_level_id
        """, 'education_levels.csv')
        
        # Export education types
        export_table_data(old_conn, """
            SELECT DISTINCT
                education_type_id as id,
                'Education Type ' || education_type_id as name_az,
                'Education Type ' || education_type_id as name_en,
                'TYPE_' || education_type_id::text as code
            FROM education_group
            WHERE education_type_id IS NOT NULL
            ORDER BY education_type_id
        """, 'education_types.csv')
        
        # Export positions
        export_table_data(old_conn, """
            SELECT DISTINCT
                position_id as id,
                'Position ' || position_id as name_az,
                'Position ' || position_id as name_en,
                'POS_' || position_id::text as code,
                'academic' as category
            FROM teachers
            WHERE position_id IS NOT NULL
            ORDER BY position_id
        """, 'positions.csv')
        
        # Export countries
        export_table_data(old_conn, """
            SELECT DISTINCT
                citizenship_id as id,
                'Country ' || citizenship_id as name_az,
                'Country ' || citizenship_id as name_en,
                NULL as iso_code,
                TRUE as is_active
            FROM persons
            WHERE citizenship_id IS NOT NULL
            ORDER BY citizenship_id
        """, 'countries.csv')
        
        # Export languages
        export_table_data(old_conn, """
            SELECT DISTINCT
                lang_id as id,
                'Language ' || lang_id as name_az,
                'Language ' || lang_id as name_en,
                NULL as iso_code,
                TRUE as is_active
            FROM (
                SELECT education_lang_id as lang_id FROM education_group WHERE education_lang_id IS NOT NULL
                UNION
                SELECT education_lang_id as lang_id FROM course WHERE education_lang_id IS NOT NULL
            ) langs
            ORDER BY lang_id
        """, 'languages.csv')
        
        # Phase 2: Export core person data
        print("\n=== Phase 2: Exporting person data ===")
        
        # Export persons (deduplicated)
        export_table_data(old_conn, """
            SELECT DISTINCT ON (COALESCE(pincode, firstname||lastname||birthdate::text))
                id, firstname, lastname, patronymic, gender_id, birthdate, pincode, citizenship_id,
                COALESCE(create_date, NOW()) as created_at, 
                COALESCE(update_date, NOW()) as updated_at,
                created_by, updated_by
            FROM persons 
            WHERE firstname IS NOT NULL 
              AND lastname IS NOT NULL
              AND LENGTH(trim(firstname)) > 0
              AND LENGTH(trim(lastname)) > 0
            ORDER BY COALESCE(pincode, firstname||lastname||birthdate::text), id
        """, 'persons_clean.csv')
        
        # Export accounts
        export_table_data(old_conn, """
            SELECT DISTINCT ON (username)
                a.id, a.person_id, a.username, a.email, 
                COALESCE(a.password, '') as password_hash,
                CASE WHEN a.activity_status = 1 THEN TRUE ELSE FALSE END as is_active,
                FALSE as email_verified,
                a.last_login,
                COALESCE(a.create_date, NOW()) as created_at, 
                COALESCE(a.update_date, NOW()) as updated_at
            FROM accounts a
            WHERE a.username IS NOT NULL
              AND EXISTS (
                  SELECT 1 FROM persons p 
                  WHERE p.id = a.person_id 
                    AND p.firstname IS NOT NULL 
                    AND p.lastname IS NOT NULL
              )
            ORDER BY username, a.id
        """, 'accounts_clean.csv')
        
        # Export users
        export_table_data(old_conn, """
            SELECT 
                u.id, u.account_id, u.organization_id,
                CASE 
                    WHEN u.user_type = 1 THEN 'student'
                    WHEN u.user_type = 2 THEN 'teacher'  
                    WHEN u.user_type = 3 THEN 'admin'
                    ELSE 'staff'
                END as user_type,
                CASE WHEN u.is_blocked = 1 THEN TRUE ELSE FALSE END as is_blocked,
                COALESCE(u.create_date, NOW()) as created_at, 
                COALESCE(u.update_date, NOW()) as updated_at
            FROM users u
            WHERE u.account_id IS NOT NULL
              AND EXISTS (SELECT 1 FROM accounts a WHERE a.id = u.account_id)
        """, 'users_clean.csv')
        
        # Phase 3: Export academic entities
        print("\n=== Phase 3: Exporting academic data ===")
        
        # Export students
        export_table_data(old_conn, """
            SELECT 
                s.id, s.person_id, s.user_id,
                COALESCE(s.card_number, 'STU' || s.id::text) as student_id_number,
                s.org_id as organization_id,
                COALESCE(EXTRACT(YEAR FROM s.in_order_date::date), 2020) as admission_year,
                CASE 
                    WHEN s.out_order_date IS NOT NULL THEN EXTRACT(YEAR FROM s.out_order_date::date)
                    ELSE NULL
                END as graduation_year,
                s.education_line_id,
                CASE 
                    WHEN s.active = 1 THEN 'active'
                    WHEN s.out_order_date IS NOT NULL THEN 'graduated'
                    ELSE 'active'
                END as status,
                COALESCE(s.create_date, NOW()) as created_at, 
                COALESCE(s.update_date, NOW()) as updated_at
            FROM students s
            WHERE s.person_id IS NOT NULL
              AND EXISTS (SELECT 1 FROM persons p WHERE p.id = s.person_id)
        """, 'students_clean.csv')
        
        # Export teachers
        export_table_data(old_conn, """
            SELECT 
                t.id, t.person_id, t.user_id, t.card_number as employee_id,
                t.organization_id, t.position_id,
                t.in_action_date::date as hire_date,
                t.out_action_date::date as termination_date,
                CASE 
                    WHEN t.active = 1 THEN 'active'
                    WHEN t.out_action_date IS NOT NULL THEN 'terminated'
                    ELSE 'active'
                END as status,
                COALESCE(t.create_date, NOW()) as created_at, 
                COALESCE(t.update_date, NOW()) as updated_at
            FROM teachers t
            WHERE t.person_id IS NOT NULL
              AND EXISTS (SELECT 1 FROM persons p WHERE p.id = t.person_id)
        """, 'teachers_clean.csv')
        
        # Export education groups
        export_table_data(old_conn, """
            SELECT 
                eg.id, eg.name, eg.code, eg.organization_id,
                COALESCE(eg.education_year_id, 1) as academic_year_id,
                eg.education_level_id, eg.education_type_id, eg.education_lang_id as language_id,
                eg.tyutor_id as tutor_id,
                30 as capacity,
                CASE WHEN eg.active = 1 THEN TRUE ELSE FALSE END as is_active,
                COALESCE(eg.create_date, NOW()) as created_at, 
                COALESCE(eg.update_date, NOW()) as updated_at
            FROM education_group eg
            WHERE eg.name IS NOT NULL
        """, 'education_groups.csv')
        
        # Export group-student relationships
        export_table_data(old_conn, """
            SELECT 
                egs.id, egs.education_group_id, egs.student_id,
                COALESCE(egs.create_date, NOW()) as joined_at,
                NULL as left_at,
                CASE WHEN egs.active = 1 THEN 'active' ELSE 'transferred' END as status
            FROM education_group_student egs
            WHERE EXISTS (SELECT 1 FROM education_group eg WHERE eg.id = egs.education_group_id)
              AND EXISTS (SELECT 1 FROM students s WHERE s.id = egs.student_id)
        """, 'group_students.csv')
        
        # Phase 4: Export course data
        print("\n=== Phase 4: Exporting course data ===")
        
        # Export subjects
        export_table_data(old_conn, """
            SELECT DISTINCT
                eps.subject_id as id,
                COALESCE(eps.code, 'SUBJ' || eps.subject_id::text) as code,
                eps.name_az, eps.name_en, eps.name_ru,
                COALESCE(eps.credits, 0) as credits,
                eps.description,
                TRUE as is_active,
                NOW() as created_at, NOW() as updated_at
            FROM education_plan_subject eps
            WHERE eps.subject_id IS NOT NULL 
              AND eps.name_az IS NOT NULL
              AND LENGTH(trim(eps.name_az)) > 0
        """, 'subjects.csv')
        
        # Export courses
        export_table_data(old_conn, """
            SELECT 
                c.id, c.education_plan_subject_id as subject_id,
                c.code, c.semester_id,
                COALESCE(c.education_year_id, 1) as academic_year_id,
                c.education_lang_id as language_id,
                COALESCE(c.m_hours, 0) as lecture_hours,
                COALESCE(c.s_hours, 0) as seminar_hours,
                COALESCE(c.l_hours, 0) as lab_hours,
                COALESCE(c.fm_hours, 0) as practice_hours,
                c.start_date::date,
                c.end_date::date,
                c.student_count as max_students,
                CASE 
                    WHEN c.active = 1 THEN 'active'
                    WHEN c.end_date < CURRENT_DATE THEN 'completed'
                    ELSE 'planned'
                END as status,
                COALESCE(c.create_date, NOW()) as created_at, 
                COALESCE(c.update_date, NOW()) as updated_at
            FROM course c
            WHERE c.code IS NOT NULL
              AND c.education_plan_subject_id IS NOT NULL
              AND EXISTS (
                  SELECT 1 FROM education_plan_subject eps 
                  WHERE eps.subject_id = c.education_plan_subject_id
              )
        """, 'courses.csv')
        
        # Export course-teacher relationships
        export_table_data(old_conn, """
            SELECT 
                ct.id, ct.course_id, ct.teacher_id,
                'instructor' as role,
                COALESCE(ct.create_date, NOW()) as assigned_at,
                NULL as removed_at
            FROM course_teacher ct
            WHERE EXISTS (SELECT 1 FROM course c WHERE c.id = ct.course_id)
              AND EXISTS (SELECT 1 FROM teachers t WHERE t.id = ct.teacher_id)
        """, 'course_teachers.csv')
        
        # Export course-student relationships
        export_table_data(old_conn, """
            SELECT 
                cs.id, cs.course_id, cs.student_id,
                COALESCE(cs.create_date, NOW()) as enrolled_at,
                NULL as dropped_at,
                CASE WHEN cs.active = 1 THEN 'enrolled' ELSE 'completed' END as status,
                NULL as final_grade
            FROM course_student cs
            WHERE EXISTS (SELECT 1 FROM course c WHERE c.id = cs.course_id)
              AND EXISTS (SELECT 1 FROM students s WHERE s.id = cs.student_id)
        """, 'course_students.csv')
        
        # Phase 5: Import to LMS database
        print("\n=== Phase 5: Importing data to LMS database ===")
        
        # Import reference data
        print("Importing reference data...")
        import_table_data(new_conn, 'dictionary_types', 'dictionary_types.csv')
        import_table_data(new_conn, 'dictionaries', 'dictionaries.csv')
        import_table_data(new_conn, 'organization_types', 'organization_types.csv')
        import_table_data(new_conn, 'organizations', 'organizations.csv')
        import_table_data(new_conn, 'education_levels', 'education_levels.csv')
        import_table_data(new_conn, 'education_types', 'education_types.csv')
        import_table_data(new_conn, 'positions', 'positions.csv')
        import_table_data(new_conn, 'countries', 'countries.csv')
        import_table_data(new_conn, 'languages', 'languages.csv')
        
        # Import person data
        print("Importing person data...")
        import_table_data(new_conn, 'persons', 'persons_clean.csv')
        import_table_data(new_conn, 'accounts', 'accounts_clean.csv')
        import_table_data(new_conn, 'users', 'users_clean.csv')
        
        # Import academic data
        print("Importing academic data...")
        import_table_data(new_conn, 'students', 'students_clean.csv')
        import_table_data(new_conn, 'teachers', 'teachers_clean.csv')
        import_table_data(new_conn, 'education_groups', 'education_groups.csv')
        import_table_data(new_conn, 'education_group_students', 'group_students.csv')
        
        # Import course data
        print("Importing course data...")
        import_table_data(new_conn, 'subjects', 'subjects.csv')
        import_table_data(new_conn, 'courses', 'courses.csv')
        import_table_data(new_conn, 'course_teachers', 'course_teachers.csv')
        import_table_data(new_conn, 'course_students', 'course_students.csv')
        
        # Update sequences
        print("\n=== Phase 6: Updating sequences ===")
        tables_with_sequences = [
            'dictionary_types', 'dictionaries', 'organization_types', 'organizations',
            'education_levels', 'education_types', 'positions', 'countries', 'languages',
            'persons', 'accounts', 'users', 'students', 'teachers', 
            'education_groups', 'education_group_students', 'subjects', 'courses',
            'course_teachers', 'course_students'
        ]
        
        with new_conn.cursor() as cursor:
            for table in tables_with_sequences:
                try:
                    cursor.execute(f"SELECT setval('{table}_id_seq', (SELECT COALESCE(MAX(id), 1) FROM {table}));")
                    result = cursor.fetchone()
                    print(f"Updated {table}_id_seq to {result[0]}")
                except Exception as e:
                    print(f"Error updating sequence for {table}: {e}")
            
            new_conn.commit()
        
        # Analyze tables
        print("\nAnalyzing tables for query optimization...")
        with new_conn.cursor() as cursor:
            cursor.execute("ANALYZE;")
            new_conn.commit()
        
        print("\n=== Data migration completed successfully! ===")
        
        # Print summary statistics
        print("\n=== Migration Summary ===")
        with new_conn.cursor() as cursor:
            tables_to_check = ['persons', 'accounts', 'users', 'students', 'teachers', 
                             'education_groups', 'courses', 'subjects']
            
            for table in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} records")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        old_conn.close()
        new_conn.close()

if __name__ == "__main__":
    main()