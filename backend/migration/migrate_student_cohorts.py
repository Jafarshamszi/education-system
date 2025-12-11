#!/usr/bin/env python3
"""
Migration script: Migrate education_group data to student_cohorts
Date: 2025-10-14
Purpose: Transfer 419 education groups from edu database to lms.student_cohorts
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from datetime import datetime

# Database connections
EDU_DB = {
    'host': 'localhost',
    'database': 'edu',
    'user': 'postgres',
    'password': '1111'
}

LMS_DB = {
    'host': 'localhost',
    'database': 'lms',
    'user': 'postgres',
    'password': '1111'
}

def get_lookup_value(cursor, table, id_val, name_col='name'):
    """Get lookup value from dictionary table"""
    if not id_val:
        return None
    cursor.execute(f"SELECT {name_col} FROM {table} WHERE id = %s", (id_val,))
    result = cursor.fetchone()
    return result[name_col] if result else None

def get_uuid_from_metadata(cursor, table, old_id):
    """Get UUID from new lms table using old_id in metadata"""
    if not old_id:
        return None
    cursor.execute(
        f"SELECT id FROM {table} WHERE metadata->>'old_id' = %s",
        (str(old_id),)
    )
    result = cursor.fetchone()
    return result['id'] if result else None

def migrate_education_groups():
    """Migrate education_group from edu to student_cohorts in lms"""
    
    edu_conn = psycopg2.connect(**EDU_DB, cursor_factory=RealDictCursor)
    lms_conn = psycopg2.connect(**LMS_DB, cursor_factory=RealDictCursor)
    
    edu_cur = edu_conn.cursor()
    lms_cur = lms_conn.cursor()
    
    try:
        print("Starting education_group migration...")
        
        # Get all education groups from edu database
        edu_cur.execute("""
            SELECT 
                id,
                name,
                organization_id,
                education_level_id,
                education_type_id,
                education_lang_id,
                tyutor_id,
                education_year_id,
                create_date,
                active
            FROM education_group
            WHERE active = 1
            ORDER BY id
        """)
        
        groups = edu_cur.fetchall()
        print(f"Found {len(groups)} education groups to migrate")
        
        migrated = 0
        skipped = 0
        errors = 0
        
        for group in groups:
            try:
                # Get lookup values from edu database
                education_level = get_lookup_value(edu_cur, 'education_level_dic', group['education_level_id'])
                education_type = get_lookup_value(edu_cur, 'education_type_dic', group['education_type_id'])
                language = get_lookup_value(edu_cur, 'education_lang_dic', group['education_lang_id'])
                
                # Try to find matching organization unit in lms
                org_unit_id = get_uuid_from_metadata(lms_cur, 'organization_units', group['organization_id'])
                
                # Try to find matching tutor in lms staff_members
                tutor_id = get_uuid_from_metadata(lms_cur, 'staff_members', group['tyutor_id'])
                
                # Extract year from education_year_id or name
                # Assuming year is encoded in ID or can be extracted from name
                # For now, use create_date year as fallback
                start_year = group['create_date'].year if group['create_date'] else None
                
                # Insert into student_cohorts
                lms_cur.execute("""
                    INSERT INTO student_cohorts (
                        code,
                        name,
                        organization_unit_id,
                        education_level,
                        education_type,
                        language,
                        tutor_id,
                        start_year,
                        is_active,
                        created_at,
                        metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (code) DO NOTHING
                    RETURNING id
                """, (
                    group['name'],  # Use name as code
                    group['name'],  # Use name as display name
                    org_unit_id,
                    education_level,
                    education_type,
                    language,
                    tutor_id,
                    start_year,
                    True,  # is_active
                    group['create_date'] or datetime.now(),
                    {'old_id': str(group['id']), 'old_edu_year_id': str(group['education_year_id'])}
                ))
                
                result = lms_cur.fetchone()
                if result:
                    migrated += 1
                    if migrated % 50 == 0:
                        print(f"Migrated {migrated} cohorts...")
                        lms_conn.commit()
                else:
                    skipped += 1
                    
            except Exception as e:
                errors += 1
                print(f"Error migrating group {group['id']} ({group['name']}): {e}")
                continue
        
        lms_conn.commit()
        
        print(f"\n=== Migration Complete ===")
        print(f"Successfully migrated: {migrated}")
        print(f"Skipped (duplicates): {skipped}")
        print(f"Errors: {errors}")
        print(f"Total processed: {len(groups)}")
        
        # Verify migration
        lms_cur.execute("SELECT COUNT(*) as count FROM student_cohorts")
        final_count = lms_cur.fetchone()['count']
        print(f"\nFinal count in student_cohorts: {final_count}")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        lms_conn.rollback()
        sys.exit(1)
    finally:
        edu_cur.close()
        lms_cur.close()
        edu_conn.close()
        lms_conn.close()

def migrate_cohort_members():
    """Migrate education_group_student to student_cohort_members"""
    
    edu_conn = psycopg2.connect(**EDU_DB, cursor_factory=RealDictCursor)
    lms_conn = psycopg2.connect(**LMS_DB, cursor_factory=RealDictCursor)
    
    edu_cur = edu_conn.cursor()
    lms_cur = lms_conn.cursor()
    
    try:
        print("\nStarting cohort members migration...")
        
        # Get all group-student relationships
        edu_cur.execute("""
            SELECT 
                education_group_id,
                student_id,
                create_date
            FROM education_group_student
            WHERE active = 1
        """)
        
        members = edu_cur.fetchall()
        print(f"Found {len(members)} cohort members to migrate")
        
        migrated = 0
        skipped = 0
        errors = 0
        
        for member in members:
            try:
                # Find cohort UUID using old_id
                cohort_id = get_uuid_from_metadata(lms_cur, 'student_cohorts', member['education_group_id'])
                student_id = get_uuid_from_metadata(lms_cur, 'students', member['student_id'])
                
                if not cohort_id or not student_id:
                    skipped += 1
                    continue
                
                # Insert cohort membership
                lms_cur.execute("""
                    INSERT INTO student_cohort_members (
                        cohort_id,
                        student_id,
                        enrollment_date,
                        status,
                        is_active,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (cohort_id, student_id) DO NOTHING
                """, (
                    cohort_id,
                    student_id,
                    member['create_date'] or datetime.now(),
                    'active',
                    True,
                    member['create_date'] or datetime.now()
                ))
                
                migrated += 1
                if migrated % 500 == 0:
                    print(f"Migrated {migrated} memberships...")
                    lms_conn.commit()
                    
            except Exception as e:
                errors += 1
                if errors < 10:  # Only print first 10 errors
                    print(f"Error migrating membership: {e}")
                continue
        
        lms_conn.commit()
        
        print(f"\n=== Cohort Members Migration Complete ===")
        print(f"Successfully migrated: {migrated}")
        print(f"Skipped (no match): {skipped}")
        print(f"Errors: {errors}")
        print(f"Total processed: {len(members)}")
        
        # Verify migration
        lms_cur.execute("SELECT COUNT(*) as count FROM student_cohort_members")
        final_count = lms_cur.fetchone()['count']
        print(f"\nFinal count in student_cohort_members: {final_count}")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        lms_conn.rollback()
        sys.exit(1)
    finally:
        edu_cur.close()
        lms_cur.close()
        edu_conn.close()
        lms_conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Education Group to Student Cohorts Migration")
    print("=" * 60)
    
    migrate_education_groups()
    migrate_cohort_members()
    
    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)
