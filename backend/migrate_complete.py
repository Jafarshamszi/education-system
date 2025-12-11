#!/usr/bin/env python3
"""
Complete Data Migration Script: edu -> lms
Migrates data in the correct order to handle foreign key constraints
"""

import psycopg2
import os

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'postgres',
    'password': '1111'
}

def connect_db(database):
    config = DB_CONFIG.copy()
    config['database'] = database
    return psycopg2.connect(**config)

def main():
    print("Starting complete data migration from edu to lms database...")
    
    old_conn = connect_db('edu')
    new_conn = connect_db('lms')
    
    try:
        # Phase 1: Migrate reference data first
        print("\n=== Phase 1: Migrating reference data ===")
        
        # Migrate gender references
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            print("Migrating gender references...")
            old_cursor.execute("""
                SELECT DISTINCT gender_id 
                FROM persons 
                WHERE gender_id IS NOT NULL
                ORDER BY gender_id
            """)
            
            gender_ids = old_cursor.fetchall()
            for (gender_id,) in gender_ids:
                if gender_id not in [1, 2]:  # Skip existing genders
                    new_cursor.execute("""
                        INSERT INTO genders (id, name_az, name_en, code)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (gender_id, f'Gender {gender_id}', f'Gender {gender_id}', f'G{gender_id}'))
            
            new_conn.commit()
            print(f"Added {len(gender_ids)} gender references")
        
        # Migrate country references
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            print("Migrating country references...")
            old_cursor.execute("""
                SELECT DISTINCT citizenship_id 
                FROM persons 
                WHERE citizenship_id IS NOT NULL
                ORDER BY citizenship_id
            """)
            
            country_ids = old_cursor.fetchall()
            for (country_id,) in country_ids:
                new_cursor.execute("""
                    INSERT INTO countries (id, name_az, name_en, is_active)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (country_id, f'Country {country_id}', f'Country {country_id}', True))
            
            new_conn.commit()
            print(f"Added {len(country_ids)} country references")
        
        # Migrate organization references
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            print("Migrating organizations...")
            old_cursor.execute("""
                SELECT DISTINCT
                    o.type_id
                FROM organizations o
                WHERE o.type_id IS NOT NULL
                ORDER BY o.type_id
            """)
            
            org_types = old_cursor.fetchall()
            for (type_id,) in org_types:
                new_cursor.execute("""
                    INSERT INTO organization_types (id, name_az, name_en, code)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (type_id, f'Org Type {type_id}', f'Org Type {type_id}', f'ORG{type_id}'))
            
            # Now migrate organizations
            old_cursor.execute("""
                SELECT 
                    o.id, 
                    COALESCE(d.name_az, 'Organization ' || o.id) as name_az,
                    COALESCE(d.name_en, 'Organization ' || o.id) as name_en,
                    o.parent_id, 
                    o.type_id,
                    CASE WHEN o.active = 1 THEN TRUE ELSE FALSE END as is_active
                FROM organizations o
                LEFT JOIN dictionaries d ON o.dictionary_name_id = d.id 
                WHERE o.id IS NOT NULL
            """)
            
            organizations = old_cursor.fetchall()
            for org in organizations:
                new_cursor.execute("""
                    INSERT INTO organizations (id, name_az, name_en, parent_id, type_id, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, org)
            
            new_conn.commit()
            print(f"Added {len(organizations)} organizations")
        
        # Migrate position references
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            print("Migrating positions...")
            old_cursor.execute("""
                SELECT DISTINCT position_id 
                FROM teachers 
                WHERE position_id IS NOT NULL
                ORDER BY position_id
            """)
            
            position_ids = old_cursor.fetchall()
            for (position_id,) in position_ids:
                new_cursor.execute("""
                    INSERT INTO positions (id, name_az, name_en, code, category)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (position_id, f'Position {position_id}', f'Position {position_id}', f'POS{position_id}', 'academic'))
            
            new_conn.commit()
            print(f"Added {len(position_ids)} positions")
        
        # Migrate language references  
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            print("Migrating languages...")
            old_cursor.execute("""
                SELECT DISTINCT lang_id 
                FROM (
                    SELECT education_lang_id as lang_id FROM education_group WHERE education_lang_id IS NOT NULL
                    UNION
                    SELECT education_lang_id as lang_id FROM course WHERE education_lang_id IS NOT NULL
                ) langs
                ORDER BY lang_id
            """)
            
            lang_ids = old_cursor.fetchall()
            for (lang_id,) in lang_ids:
                new_cursor.execute("""
                    INSERT INTO languages (id, name_az, name_en, is_active)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (lang_id, f'Language {lang_id}', f'Language {lang_id}', True))
            
            new_conn.commit()
            print(f"Added {len(lang_ids)} languages")
        
        # Phase 2: Core person data
        print("\n=== Phase 2: Migrating core person data ===")
        
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            # Migrate persons (deduplicated)
            old_cursor.execute("""
                SELECT DISTINCT ON (COALESCE(pincode, firstname||lastname||birthdate::text))
                    id, firstname, lastname, patronymic, 
                    CASE 
                        WHEN gender_id IS NOT NULL AND gender_id IN (1, 2) THEN gender_id
                        WHEN gender_id IS NOT NULL THEN gender_id
                        ELSE NULL
                    END as gender_id,
                    CASE WHEN birthdate ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' THEN birthdate::date ELSE NULL END as birthdate,
                    pincode, citizenship_id
                FROM persons 
                WHERE firstname IS NOT NULL 
                  AND lastname IS NOT NULL
                  AND LENGTH(trim(firstname)) > 0
                  AND LENGTH(trim(lastname)) > 0
                ORDER BY COALESCE(pincode, firstname||lastname||birthdate::text), id
            """)
            
            persons = old_cursor.fetchall()
            print(f"Migrating {len(persons)} persons...")
            
            for person in persons:
                try:
                    new_cursor.execute("""
                        INSERT INTO persons (id, firstname, lastname, patronymic, gender_id, birthdate, pincode, citizenship_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, person)
                except Exception as e:
                    print(f"  Error with person {person[0]}: {e}")
                    continue
            
            new_conn.commit()
            print(f"Migrated persons")
        
        # Phase 3: Migrate accounts
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            old_cursor.execute("""
                SELECT DISTINCT ON (username)
                    a.id, a.person_id, a.username, a.email, 
                    COALESCE(a.password, '') as password_hash,
                    CASE WHEN a.activity_status = 1 THEN TRUE ELSE FALSE END as is_active
                FROM accounts a
                WHERE a.username IS NOT NULL
                  AND EXISTS (SELECT 1 FROM persons p WHERE p.id = a.person_id)
                ORDER BY username, a.id
            """)
            
            accounts = old_cursor.fetchall()
            print(f"Migrating {len(accounts)} accounts...")
            
            for account in accounts:
                try:
                    new_cursor.execute("""
                        INSERT INTO accounts (id, person_id, username, email, password_hash, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, account)
                except Exception as e:
                    print(f"  Error with account {account[0]}: {e}")
                    continue
            
            new_conn.commit()
            print(f"Migrated accounts")
        
        # Phase 4: Migrate users
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            old_cursor.execute("""
                SELECT 
                    u.id, u.account_id, u.organization_id,
                    CASE 
                        WHEN u.user_type = 1 THEN 'student'
                        WHEN u.user_type = 2 THEN 'teacher'  
                        WHEN u.user_type = 3 THEN 'admin'
                        ELSE 'staff'
                    END as user_type,
                    CASE WHEN u.is_blocked = 1 THEN TRUE ELSE FALSE END as is_blocked
                FROM users u
                WHERE u.account_id IS NOT NULL
            """)
            
            users = old_cursor.fetchall()
            print(f"Migrating {len(users)} users...")
            
            for user in users:
                try:
                    new_cursor.execute("""
                        INSERT INTO users (id, account_id, organization_id, user_type, is_blocked)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, user)
                except Exception as e:
                    print(f"  Error with user {user[0]}: {e}")
                    continue
            
            new_conn.commit()
            print(f"Migrated users")
        
        # Phase 5: Migrate students and teachers
        print("\n=== Phase 5: Migrating students and teachers ===")
        
        # Migrate students
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            old_cursor.execute("""
                SELECT 
                    s.id, s.person_id, s.user_id,
                    COALESCE(s.card_number, 'STU' || s.id::text) as student_id_number,
                    s.org_id as organization_id,
                    COALESCE(EXTRACT(YEAR FROM s.in_order_date::date), 2020) as admission_year,
                    CASE 
                        WHEN s.active = 1 THEN 'active'
                        WHEN s.out_order_date IS NOT NULL THEN 'graduated'
                        ELSE 'active'
                    END as status
                FROM students s
                WHERE s.person_id IS NOT NULL
            """)
            
            students = old_cursor.fetchall()
            print(f"Migrating {len(students)} students...")
            
            for student in students:
                try:
                    new_cursor.execute("""
                        INSERT INTO students (id, person_id, user_id, student_id_number, organization_id, admission_year, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, student)
                except Exception as e:
                    print(f"  Error with student {student[0]}: {e}")
                    continue
            
            new_conn.commit()
            print(f"Migrated students")
        
        # Migrate teachers
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            old_cursor.execute("""
                SELECT 
                    t.id, t.person_id, t.user_id, t.card_number as employee_id,
                    t.organization_id, t.position_id,
                    CASE 
                        WHEN t.active = 1 THEN 'active'
                        ELSE 'active'
                    END as status
                FROM teachers t
                WHERE t.person_id IS NOT NULL
            """)
            
            teachers = old_cursor.fetchall()
            print(f"Migrating {len(teachers)} teachers...")
            
            for teacher in teachers:
                try:
                    new_cursor.execute("""
                        INSERT INTO teachers (id, person_id, user_id, employee_id, organization_id, position_id, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, teacher)
                except Exception as e:
                    print(f"  Error with teacher {teacher[0]}: {e}")
                    continue
            
            new_conn.commit()
            print(f"Migrated teachers")
        
        # Phase 6: Migrate academic data
        print("\n=== Phase 6: Migrating academic data ===")
        
        # Migrate subjects first
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            old_cursor.execute("""
                SELECT DISTINCT
                    eps.subject_id as id,
                    COALESCE(eps.code, 'SUBJ' || eps.subject_id::text) as code,
                    eps.name_az, 
                    COALESCE(eps.name_en, eps.name_az) as name_en,
                    eps.name_ru,
                    COALESCE(eps.credits, 0) as credits
                FROM education_plan_subject eps
                WHERE eps.subject_id IS NOT NULL 
                  AND eps.name_az IS NOT NULL
                  AND LENGTH(trim(eps.name_az)) > 0
            """)
            
            subjects = old_cursor.fetchall()
            print(f"Migrating {len(subjects)} subjects...")
            
            for subject in subjects:
                try:
                    new_cursor.execute("""
                        INSERT INTO subjects (id, code, name_az, name_en, name_ru, credits)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, subject)
                except Exception as e:
                    print(f"  Error with subject {subject[0]}: {e}")
                    continue
            
            new_conn.commit()
            print(f"Migrated subjects")
        
        # Migrate courses
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            old_cursor.execute("""
                SELECT 
                    c.id, c.education_plan_subject_id as subject_id,
                    c.code, c.semester_id,
                    COALESCE(c.education_year_id, 1) as academic_year_id,
                    c.education_lang_id as language_id,
                    COALESCE(c.m_hours, 0) as lecture_hours,
                    COALESCE(c.s_hours, 0) as seminar_hours,
                    COALESCE(c.l_hours, 0) as lab_hours,
                    CASE 
                        WHEN c.active = 1 THEN 'active'
                        ELSE 'planned'
                    END as status
                FROM course c
                WHERE c.code IS NOT NULL
                  AND c.education_plan_subject_id IS NOT NULL
            """)
            
            courses = old_cursor.fetchall()
            print(f"Migrating {len(courses)} courses...")
            
            success_count = 0
            for course in courses:
                try:
                    new_cursor.execute("""
                        INSERT INTO courses (id, subject_id, code, semester_id, academic_year_id, language_id, 
                                           lecture_hours, seminar_hours, lab_hours, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, course)
                    success_count += 1
                except Exception as e:
                    print(f"  Error with course {course[0]}: {e}")
                    continue
            
            new_conn.commit()
            print(f"Migrated {success_count} courses successfully")
        
        # Update sequences
        print("\n=== Phase 7: Updating sequences ===")
        
        tables = ['persons', 'accounts', 'users', 'students', 'teachers', 'subjects', 'courses']
        
        with new_conn.cursor() as cursor:
            for table in tables:
                try:
                    cursor.execute(f"SELECT setval('{table}_id_seq', (SELECT COALESCE(MAX(id), 1) FROM {table}));")
                    result = cursor.fetchone()
                    print(f"Updated {table}_id_seq to {result[0]}")
                except Exception as e:
                    print(f"Error updating sequence for {table}: {e}")
            
            new_conn.commit()
        
        # Final statistics
        print("\n=== Migration Summary ===")
        with new_conn.cursor() as cursor:
            tables_to_check = ['persons', 'accounts', 'users', 'students', 'teachers', 'subjects', 'courses']
            
            for table in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} records")
        
        print("\n=== Data migration completed successfully! ===")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        old_conn.close()
        new_conn.close()

if __name__ == "__main__":
    main()