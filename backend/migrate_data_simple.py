#!/usr/bin/env python3
"""
Simplified Data Migration Script: edu -> lms
"""

import psycopg2
import csv
import os

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

def main():
    print("Starting simplified data migration from edu to lms database...")
    
    old_conn = connect_db('edu')
    new_conn = connect_db('lms')
    
    try:
        os.makedirs('C:/temp/lms_migration', exist_ok=True)
        
        # Phase 1: Core data migration
        print("\n=== Phase 1: Migrating persons ===")
        
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            # Migrate persons (deduplicated by pincode)
            old_cursor.execute("""
                SELECT DISTINCT ON (COALESCE(pincode, firstname||lastname||birthdate::text))
                    id, firstname, lastname, patronymic, gender_id, 
                    CASE WHEN birthdate ~ '^\d{4}-\d{2}-\d{2}' THEN birthdate::date ELSE NULL END as birthdate,
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
                new_cursor.execute("""
                    INSERT INTO persons (id, firstname, lastname, patronymic, gender_id, birthdate, pincode, citizenship_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, person)
            
            new_conn.commit()
            print(f"Migrated {len(persons)} persons")
        
        # Phase 2: Migrate accounts
        print("\n=== Phase 2: Migrating accounts ===")
        
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
                new_cursor.execute("""
                    INSERT INTO accounts (id, person_id, username, email, password_hash, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, account)
            
            new_conn.commit()
            print(f"Migrated {len(accounts)} accounts")
        
        # Phase 3: Migrate users
        print("\n=== Phase 3: Migrating users ===")
        
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
                  AND EXISTS (SELECT 1 FROM accounts a WHERE a.id = u.account_id)
            """)
            
            users = old_cursor.fetchall()
            print(f"Migrating {len(users)} users...")
            
            for user in users:
                new_cursor.execute("""
                    INSERT INTO users (id, account_id, organization_id, user_type, is_blocked)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, user)
            
            new_conn.commit()
            print(f"Migrated {len(users)} users")
        
        # Phase 4: Migrate students
        print("\n=== Phase 4: Migrating students ===")
        
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
                  AND EXISTS (SELECT 1 FROM persons p WHERE p.id = s.person_id)
            """)
            
            students = old_cursor.fetchall()
            print(f"Migrating {len(students)} students...")
            
            for student in students:
                new_cursor.execute("""
                    INSERT INTO students (id, person_id, user_id, student_id_number, organization_id, admission_year, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, student)
            
            new_conn.commit()
            print(f"Migrated {len(students)} students")
        
        # Phase 5: Migrate teachers
        print("\n=== Phase 5: Migrating teachers ===")
        
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
                  AND EXISTS (SELECT 1 FROM persons p WHERE p.id = t.person_id)
            """)
            
            teachers = old_cursor.fetchall()
            print(f"Migrating {len(teachers)} teachers...")
            
            for teacher in teachers:
                new_cursor.execute("""
                    INSERT INTO teachers (id, person_id, user_id, employee_id, organization_id, position_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, teacher)
            
            new_conn.commit()
            print(f"Migrated {len(teachers)} teachers")
        
        # Phase 6: Migrate subjects and courses
        print("\n=== Phase 6: Migrating subjects and courses ===")
        
        # First migrate subjects
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
                new_cursor.execute("""
                    INSERT INTO subjects (id, code, name_az, name_en, name_ru, credits)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, subject)
            
            new_conn.commit()
            print(f"Migrated {len(subjects)} subjects")
        
        # Then migrate courses
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
                  AND EXISTS (
                      SELECT 1 FROM education_plan_subject eps 
                      WHERE eps.subject_id = c.education_plan_subject_id
                  )
            """)
            
            courses = old_cursor.fetchall()
            print(f"Migrating {len(courses)} courses...")
            
            for course in courses:
                try:
                    new_cursor.execute("""
                        INSERT INTO courses (id, subject_id, code, semester_id, academic_year_id, language_id, 
                                           lecture_hours, seminar_hours, lab_hours, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, course)
                except Exception as e:
                    print(f"  Error with course {course[0]}: {e}")
                    continue
            
            new_conn.commit()
            print(f"Migrated courses")
        
        # Update sequences
        print("\n=== Phase 7: Updating sequences ===")
        
        tables_with_sequences = ['persons', 'accounts', 'users', 'students', 'teachers', 'subjects', 'courses']
        
        with new_conn.cursor() as cursor:
            for table in tables_with_sequences:
                try:
                    cursor.execute(f"SELECT setval('{table}_id_seq', (SELECT COALESCE(MAX(id), 1) FROM {table}));")
                    result = cursor.fetchone()
                    print(f"Updated {table}_id_seq to {result[0]}")
                except Exception as e:
                    print(f"Error updating sequence for {table}: {e}")
            
            new_conn.commit()
        
        # Print final statistics
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