#!/usr/bin/env python3
"""
Simplified migration: Just migrate education_group names to student_cohorts
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
import sys
from datetime import datetime

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

def migrate_simple():
    """Simple migration: Just copy education_group names"""
    
    edu_conn = psycopg2.connect(**EDU_DB, cursor_factory=RealDictCursor)
    lms_conn = psycopg2.connect(**LMS_DB, cursor_factory=RealDictCursor)
    
    edu_cur = edu_conn.cursor()
    lms_cur = lms_conn.cursor()
    
    try:
        print("Starting simple education_group migration...")
        
        # Get education groups with lookup data
        edu_cur.execute("""
            SELECT 
                eg.id,
                eg.name,
                el.name_az as education_level,
                et.name_az as education_type,
                lang.name_az as language,
                eg.create_date,
                eg.active
            FROM education_group eg
            LEFT JOIN dictionaries el ON eg.education_level_id = el.id
            LEFT JOIN dictionaries et ON eg.education_type_id = et.id
            LEFT JOIN dictionaries lang ON eg.education_lang_id = lang.id
            WHERE eg.active = 1
            ORDER BY eg.id
        """)
        
        groups = edu_cur.fetchall()
        print(f"Found {len(groups)} education groups")
        
        migrated = 0
        
        for group in groups:
            try:
                # Extract year from name (e.g., "923-s" -> 2023, "ML-61-17" -> 2017)
                name = group['name'] or f"Group-{group['id']}"
                start_year = None
                
                # Try to extract year from name
                parts = name.split('-')
                for part in parts:
                    if part.isdigit() and len(part) == 2:
                        year = int(part)
                        # Assume 00-50 is 2000s, 51-99 is 1900s
                        start_year = 2000 + year if year < 50 else 1900 + year
                        break
                
                #If no year found, use create date
                if not start_year and group['create_date']:
                    start_year = group['create_date'].year
                
                lms_cur.execute("""
                    INSERT INTO student_cohorts (
                        code,
                        name,
                        education_level,
                        education_type,
                        language,
                        start_year,
                        is_active,
                        created_at,
                        metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb
                    )
                    ON CONFLICT (code) DO NOTHING
                    RETURNING id
                """, (
                    name,
                    name,
                    group['education_level'],
                    group['education_type'],
                    group['language'],
                    start_year,
                    True,
                    group['create_date'] or datetime.now(),
                    Json({'old_id': str(group['id'])})
                ))
                
                result = lms_cur.fetchone()
                if result:
                    migrated += 1
                    if migrated % 50 == 0:
                        print(f"Migrated {migrated} cohorts...")
                        lms_conn.commit()
                    
            except Exception as e:
                print(f"Error migrating {group['name']}: {e}")
                continue
        
        lms_conn.commit()
        
        print(f"\n=== Complete ===")
        print(f"Migrated: {migrated}")
        
        lms_cur.execute("SELECT COUNT(*) as count FROM student_cohorts")
        final = lms_cur.fetchone()['count']
        print(f"Final count: {final}")
        
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
    migrate_simple()
