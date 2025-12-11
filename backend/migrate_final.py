#!/usr/bin/env python3
"""
Final Migration Script: edu -> lms
Handles hierarchical data and foreign key constraints properly
"""

import psycopg2

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
    print("Starting final data migration from edu to lms database...")
    
    old_conn = connect_db('edu')
    new_conn = connect_db('lms')
    
    try:
        print("\n=== Phase 1: Migrating reference data ===")
        
        # Step 1: Migrate all unique reference IDs first
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            # Gender references
            print("Adding gender references...")
            old_cursor.execute("SELECT DISTINCT gender_id FROM persons WHERE gender_id IS NOT NULL ORDER BY gender_id")
            for (gender_id,) in old_cursor.fetchall():
                if gender_id not in [1, 2]:
                    new_cursor.execute("""
                        INSERT INTO genders (id, name_az, name_en, code) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, (gender_id, f'Gender {gender_id}', f'Gender {gender_id}', f'G{gender_id}'))
            
            # Country references  
            print("Adding country references...")
            old_cursor.execute("SELECT DISTINCT citizenship_id FROM persons WHERE citizenship_id IS NOT NULL ORDER BY citizenship_id")
            for (country_id,) in old_cursor.fetchall():
                new_cursor.execute("""
                    INSERT INTO countries (id, name_az, name_en, is_active) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                """, (country_id, f'Country {country_id}', f'Country {country_id}', True))
            
            # Organization type references
            print("Adding organization type references...")
            old_cursor.execute("SELECT DISTINCT type_id FROM organizations WHERE type_id IS NOT NULL ORDER BY type_id")
            for (type_id,) in old_cursor.fetchall():
                new_cursor.execute("""
                    INSERT INTO organization_types (id, name_az, name_en, code) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                """, (type_id, f'Org Type {type_id}', f'Org Type {type_id}', f'ORG{type_id}'))
            
            # Position references
            print("Adding position references...")
            old_cursor.execute("SELECT DISTINCT position_id FROM teachers WHERE position_id IS NOT NULL ORDER BY position_id")
            for (position_id,) in old_cursor.fetchall():
                new_cursor.execute("""
                    INSERT INTO positions (id, name_az, name_en, code, category) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                """, (position_id, f'Position {position_id}', f'Position {position_id}', f'POS{position_id}', 'academic'))
            
            # Language references
            print("Adding language references...")
            old_cursor.execute("""
                SELECT DISTINCT lang_id FROM (
                    SELECT education_lang_id as lang_id FROM education_group WHERE education_lang_id IS NOT NULL
                    UNION
                    SELECT education_lang_id as lang_id FROM course WHERE education_lang_id IS NOT NULL
                ) langs ORDER BY lang_id
            """)
            for (lang_id,) in old_cursor.fetchall():
                new_cursor.execute("""
                    INSERT INTO languages (id, name_az, name_en, is_active) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                """, (lang_id, f'Language {lang_id}', f'Language {lang_id}', True))
            
            new_conn.commit()
            print("Reference data migration completed")
        
        # Step 2: Migrate organizations (without parent_id first)
        print("Adding organizations...")
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            old_cursor.execute("""
                SELECT 
                    o.id, 
                    COALESCE(d.name_az, 'Organization ' || o.id) as name_az,
                    COALESCE(d.name_en, 'Organization ' || o.id) as name_en,
                    o.type_id,
                    CASE WHEN o.active = 1 THEN TRUE ELSE FALSE END as is_active
                FROM organizations o
                LEFT JOIN dictionaries d ON o.dictionary_name_id = d.id 
                WHERE o.id IS NOT NULL
            """)
            
            organizations = old_cursor.fetchall()
            for org in organizations:
                try:
                    new_cursor.execute("""
                        INSERT INTO organizations (id, name_az, name_en, type_id, is_active) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, org)
                except Exception as e:
                    print(f"  Error with organization {org[0]}: {e}")
                    continue
            
            new_conn.commit()
            print(f"Added {len(organizations)} organizations")
        
        print("\n=== Phase 2: Migrating core person data ===")
        
        # Migrate persons
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            old_cursor.execute("""
                SELECT DISTINCT ON (COALESCE(pincode, firstname||lastname||COALESCE(birthdate,'')))
                    id, firstname, lastname, patronymic, gender_id,
                    CASE WHEN birthdate ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' THEN birthdate::date ELSE NULL END as birthdate,
                    pincode, citizenship_id
                FROM persons 
                WHERE firstname IS NOT NULL AND lastname IS NOT NULL
                  AND LENGTH(trim(firstname)) > 0 AND LENGTH(trim(lastname)) > 0
                ORDER BY COALESCE(pincode, firstname||lastname||COALESCE(birthdate,'')), id
            """)
            
            persons = old_cursor.fetchall()
            print(f"Migrating {len(persons)} persons...")
            
            success_count = 0
            for person in persons:
                try:
                    new_cursor.execute("""
                        INSERT INTO persons (id, firstname, lastname, patronymic, gender_id, birthdate, pincode, citizenship_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, person)
                    success_count += 1
                except Exception as e:
                    print(f"  Error with person {person[0]}: {e}")
                    continue
            
            new_conn.commit()
            print(f"Successfully migrated {success_count} persons")
        
        # Migrate accounts
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            old_cursor.execute("""
                SELECT DISTINCT ON (username)
                    a.id, a.person_id, a.username, a.email, 
                    COALESCE(a.password, '') as password_hash,
                    CASE WHEN a.activity_status = 1 THEN TRUE ELSE FALSE END as is_active
                FROM accounts a
                WHERE a.username IS NOT NULL
                ORDER BY username, a.id
            """)
            
            accounts = old_cursor.fetchall()
            print(f"Migrating {len(accounts)} accounts...")
            
            success_count = 0
            for account in accounts:
                try:
                    new_cursor.execute("""
                        INSERT INTO accounts (id, person_id, username, email, password_hash, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, account)
                    success_count += 1
                except:
                    continue
            
            new_conn.commit()
            print(f"Successfully migrated {success_count} accounts")
        
        # Migrate users
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
            
            success_count = 0
            for user in users:
                try:
                    new_cursor.execute("""
                        INSERT INTO users (id, account_id, organization_id, user_type, is_blocked)
                        VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, user)
                    success_count += 1
                except:
                    continue
            
            new_conn.commit()
            print(f"Successfully migrated {success_count} users")
        
        print("\n=== Phase 3: Migrating students and teachers ===")
        
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
            
            success_count = 0
            for student in students:
                try:
                    new_cursor.execute("""
                        INSERT INTO students (id, person_id, user_id, student_id_number, organization_id, admission_year, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, student)
                    success_count += 1
                except:
                    continue
            
            new_conn.commit()
            print(f"Successfully migrated {success_count} students")
        
        # Migrate teachers
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            old_cursor.execute("""
                SELECT 
                    t.id, t.person_id, t.user_id, t.card_number as employee_id,
                    t.organization_id, t.position_id, 'active' as status
                FROM teachers t
                WHERE t.person_id IS NOT NULL
            """)
            
            teachers = old_cursor.fetchall()
            print(f"Migrating {len(teachers)} teachers...")
            
            success_count = 0
            for teacher in teachers:
                try:
                    new_cursor.execute("""
                        INSERT INTO teachers (id, person_id, user_id, employee_id, organization_id, position_id, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, teacher)
                    success_count += 1
                except:
                    continue
            
            new_conn.commit()
            print(f"Successfully migrated {success_count} teachers")
        
        print("\n=== Phase 4: Migrating academic data ===")
        
        # Migrate subjects
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
            
            success_count = 0
            for subject in subjects:
                try:
                    new_cursor.execute("""
                        INSERT INTO subjects (id, code, name_az, name_en, name_ru, credits)
                        VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, subject)
                    success_count += 1
                except:
                    continue
            
            new_conn.commit()
            print(f"Successfully migrated {success_count} subjects")
        
        # Migrate courses (only with valid subject references)
        with old_conn.cursor() as old_cursor, new_conn.cursor() as new_cursor:
            old_cursor.execute("""
                SELECT 
                    c.id, c.education_plan_subject_id as subject_id,
                    c.code, c.semester_id, 1 as academic_year_id,
                    c.education_lang_id as language_id,
                    COALESCE(c.m_hours, 0) as lecture_hours,
                    COALESCE(c.s_hours, 0) as seminar_hours,
                    COALESCE(c.l_hours, 0) as lab_hours,
                    CASE WHEN c.active = 1 THEN 'active' ELSE 'planned' END as status
                FROM course c
                WHERE c.code IS NOT NULL 
                  AND c.education_plan_subject_id IS NOT NULL
            """)
            
            courses = old_cursor.fetchall()
            print(f"Migrating {len(courses)} courses...")
            
            success_count = 0
            for course in courses:
                try:
                    # Ensure total hours > 0 constraint
                    if course[6] + course[7] + course[8] == 0:  # All hours are 0
                        course = course[:6] + (1, 0, 0) + course[9:]  # Set lecture_hours to 1
                    
                    new_cursor.execute("""
                        INSERT INTO courses (id, subject_id, code, semester_id, academic_year_id, language_id, 
                                           lecture_hours, seminar_hours, lab_hours, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                    """, course)
                    success_count += 1
                except:
                    continue
            
            new_conn.commit()
            print(f"Successfully migrated {success_count} courses")
        
        # Update sequences
        print("\n=== Phase 5: Updating sequences ===")
        
        tables = ['persons', 'accounts', 'users', 'students', 'teachers', 'subjects', 'courses', 
                 'organizations', 'genders', 'countries', 'languages', 'positions', 'organization_types']
        
        with new_conn.cursor() as cursor:
            for table in tables:
                try:
                    cursor.execute(f"SELECT setval('{table}_id_seq', (SELECT COALESCE(MAX(id), 1) FROM {table}));")
                    result = cursor.fetchone()
                    print(f"Updated {table}_id_seq to {result[0]}")
                except:
                    continue
            
            new_conn.commit()
        
        # Final statistics
        print("\n=== Migration Summary ===")
        with new_conn.cursor() as cursor:
            tables = ['persons', 'accounts', 'users', 'students', 'teachers', 'subjects', 'courses']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} records")
        
        print("\n🎉 Data migration completed successfully! 🎉")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        old_conn.close()
        new_conn.close()

if __name__ == "__main__":
    main()