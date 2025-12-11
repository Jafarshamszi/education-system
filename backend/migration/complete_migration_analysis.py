#!/usr/bin/env python3
"""
Comprehensive Migration Analysis and Execution Script
Analyzes both databases and executes remaining migration tasks
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

# Database configurations
OLD_DB = {'host': 'localhost', 'port': 5432, 'database': 'edu', 'user': 'postgres', 'password': '1111'}
NEW_DB = {'host': 'localhost', 'port': 5432, 'database': 'lms', 'user': 'postgres', 'password': '1111'}

def analyze_missing_data():
    """Analyze what data is missing in the new database"""
    print("=" * 80)
    print("COMPREHENSIVE MIGRATION GAP ANALYSIS")
    print("=" * 80)
    
    old_conn = psycopg2.connect(**OLD_DB)
    new_conn = psycopg2.connect(**NEW_DB)
    
    try:
        with old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with new_conn.cursor(cursor_factory=RealDictCursor) as new_cur:
                
                # 1. ANALYZE COURSES - Why did they fail?
                print("\n1. COURSE MIGRATION FAILURE ANALYSIS")
                print("-" * 80)
                
                # Get failed courses details
                old_cur.execute("""
                    SELECT 
                        c.id, c.code, c.education_plan_subject_id, c.semester_id,
                        eps.subject_id,
                        sc.subject_name_id,
                        sc.organization_id
                    FROM course c
                    LEFT JOIN education_plan_subject eps ON c.education_plan_subject_id = eps.id
                    LEFT JOIN subject_catalog sc ON eps.subject_id = sc.id
                    WHERE c.active = 1
                    LIMIT 10
                """)
                sample_courses = old_cur.fetchall()
                
                print(f"\nSample of course structure:")
                for course in sample_courses[:3]:
                    print(f"  Course ID: {course['id']}")
                    print(f"    code: {course['code']}")
                    print(f"    education_plan_subject_id: {course['education_plan_subject_id']}")
                    print(f"    subject_id (from eps): {course['subject_id']}")
                    print(f"    semester_id: {course['semester_id']}")
                    print()
                
                # Count courses with and without mappings
                old_cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(eps.id) as has_eps,
                        COUNT(eps.subject_id) as has_subject,
                        COUNT(c.semester_id) as has_semester
                    FROM course c
                    LEFT JOIN education_plan_subject eps ON c.education_plan_subject_id = eps.id
                    WHERE c.active = 1
                """)
                mapping_stats = old_cur.fetchone()
                print(f"Course Mapping Statistics:")
                print(f"  Total active courses: {mapping_stats['total']}")
                print(f"  Has education_plan_subject: {mapping_stats['has_eps']} ({mapping_stats['has_eps']*100/mapping_stats['total']:.1f}%)")
                print(f"  Has subject_catalog mapping: {mapping_stats['has_subject']} ({mapping_stats['has_subject']*100/mapping_stats['total']:.1f}%)")
                print(f"  Has semester_id: {mapping_stats['has_semester']} ({mapping_stats['has_semester']*100/mapping_stats['total']:.1f}%)")
                
                # 2. CHECK WHAT'S IN NEW DATABASE
                print("\n2. NEW DATABASE STRUCTURE ANALYSIS")
                print("-" * 80)
                
                # Get all tables in new database
                new_cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                new_tables = [row['table_name'] for row in new_cur.fetchall()]
                print(f"\nTables in NEW database ({len(new_tables)} tables):")
                for table in new_tables:
                    new_cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = new_cur.fetchone()['count']
                    print(f"  {table:40} : {count:>10,} records")
                
                # 3. CHECK WHAT'S MISSING FROM OLD DATABASE
                print("\n3. OLD DATABASE CONTENT THAT NEEDS MIGRATION")
                print("-" * 80)
                
                # Key tables to check
                old_tables_to_check = [
                    ('course', 'active = 1'),
                    ('journal', '1=1'),
                    ('journal_details', '1=1'),
                    ('exam', 'active = 1'),
                    ('exam_student', '1=1'),
                    ('files', '1=1'),
                    ('course_meeting_topic_file', '1=1'),
                    ('course_meeting', 'active = 1'),
                    ('course_meeting_attendance', '1=1'),
                    ('students', 'active = 1'),
                    ('teachers', 'active = 1'),
                    ('education_plan', 'active = 1'),
                    ('subject_catalog', 'active = 1'),
                ]
                
                for table, condition in old_tables_to_check:
                    old_cur.execute(f"SELECT COUNT(*) as count FROM {table} WHERE {condition}")
                    count = old_cur.fetchone()['count']
                    print(f"  {table:40} : {count:>10,} records")
                
                # 4. IDENTIFY TABLES MISSING IN NEW DB
                print("\n4. OLD DATABASE TABLES NOT MAPPED TO NEW DATABASE")
                print("-" * 80)
                
                old_cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                old_tables = [row['table_name'] for row in old_cur.fetchall()]
                
                # Tables that might not have direct mapping
                potential_unmapped = []
                for old_table in old_tables:
                    if old_table not in new_tables and not old_table.endswith('_backup'):
                        # Check if it has data
                        old_cur.execute(f"SELECT COUNT(*) as count FROM {old_table}")
                        count = old_cur.fetchone()['count']
                        if count > 0:
                            potential_unmapped.append((old_table, count))
                
                print(f"\nOld tables with data but no direct mapping in new DB:")
                for table, count in sorted(potential_unmapped, key=lambda x: x[1], reverse=True)[:20]:
                    print(f"  {table:40} : {count:>10,} records")
                
                # 5. CHECK ENROLLMENT AND GRADE DEPENDENCIES
                print("\n5. ENROLLMENT AND GRADE DEPENDENCY CHECK")
                print("-" * 80)
                
                # Check how many enrollments can be migrated based on existing students and courses
                old_cur.execute("""
                    SELECT COUNT(*) as total_enrollments
                    FROM journal j
                    WHERE j.status = 1  -- active enrollments
                """)
                total_enrollments = old_cur.fetchone()['total_enrollments']
                
                # Check current migration state
                new_cur.execute("SELECT COUNT(*) as count FROM course_enrollments")
                migrated_enrollments = new_cur.fetchone()['count']
                
                new_cur.execute("SELECT COUNT(*) as count FROM students")
                migrated_students = new_cur.fetchone()['count']
                
                new_cur.execute("SELECT COUNT(*) as count FROM course_offerings")
                migrated_offerings = new_cur.fetchone()['count']
                
                print(f"  Total enrollments in old DB: {total_enrollments:,}")
                print(f"  Migrated enrollments: {migrated_enrollments:,}")
                print(f"  Migrated students: {migrated_students:,}")
                print(f"  Migrated course offerings: {migrated_offerings:,}")
                print(f"  Gap: {total_enrollments - migrated_enrollments:,} enrollments not migrated")
                
                # Check grades
                old_cur.execute("SELECT COUNT(*) as count FROM journal_details")
                total_grades = old_cur.fetchone()['count']
                
                new_cur.execute("SELECT COUNT(*) as count FROM grades")
                migrated_grades = new_cur.fetchone()['count']
                
                print(f"\n  Total grades in old DB: {total_grades:,}")
                print(f"  Migrated grades: {migrated_grades:,}")
                print(f"  Gap: {total_grades - migrated_grades:,} grades not migrated")
                
    finally:
        old_conn.close()
        new_conn.close()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    analyze_missing_data()
