#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor

def analyze_critical_issues():
    """Analyze critical database issues in detail"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='edu',
            user='postgres',
            password='1111',
            port=5432
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== CRITICAL DATABASE ISSUES ANALYSIS ===\n")
        
        # 1. Check for duplicate/backup tables
        print("1. BACKUP AND DUPLICATE TABLES:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name ILIKE '%bak%' 
               OR table_name ILIKE '%backup%'
               OR table_name ILIKE '%archive%'
               OR table_name ILIKE '%_old%'
               OR table_name ILIKE '%2022%'
               OR table_name ILIKE '%2023%'
               OR table_name ILIKE '%_2%'
               OR table_name ILIKE 'a_%'
            ORDER BY table_name
        """)
        backup_tables = cursor.fetchall()
        print(f"Found {len(backup_tables)} potential backup/duplicate tables:")
        for table in backup_tables:
            print(f"  - {table['table_name']}")
        
        # 2. Check tables with inconsistent naming
        print(f"\n2. NAMING CONVENTION ISSUES:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE schemaname = 'public'
            ORDER BY table_name
        """)
        all_tables = cursor.fetchall()
        
        # Find tables with different naming patterns
        snake_case = []
        camel_case = []
        mixed_case = []
        
        for table in all_tables:
            name = table['table_name']
            if '_' in name and name.islower():
                snake_case.append(name)
            elif any(c.isupper() for c in name[1:]) and '_' not in name:
                camel_case.append(name)
            elif '_' in name and any(c.isupper() for c in name):
                mixed_case.append(name)
        
        print(f"  Snake_case tables: {len(snake_case)}")
        print(f"  CamelCase tables: {len(camel_case)}")  
        print(f"  Mixed naming: {len(mixed_case)}")
        
        # 3. Analyze potential foreign key relationships
        print(f"\n3. MISSING FOREIGN KEY ANALYSIS:")
        
        # Find all columns ending with _id
        cursor.execute("""
            SELECT 
                table_name,
                column_name,
                data_type
            FROM information_schema.columns 
            WHERE column_name LIKE '%_id' 
              AND column_name != 'id'
              AND table_schema = 'public'
            ORDER BY table_name, column_name
        """)
        
        potential_fks = cursor.fetchall()
        print(f"Found {len(potential_fks)} potential foreign key columns:")
        
        # Group by referenced table
        fk_groups = {}
        for fk in potential_fks:
            # Extract potential referenced table name
            col_name = fk['column_name']
            if col_name.endswith('_id'):
                ref_table = col_name[:-3]  # Remove '_id'
                if ref_table not in fk_groups:
                    fk_groups[ref_table] = []
                fk_groups[ref_table].append((fk['table_name'], fk['column_name']))
        
        # Show most common potential references
        print("\nMost common potential foreign key relationships:")
        for ref_table, references in sorted(fk_groups.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
            print(f"  {ref_table} ({len(references)} references):")
            for table_name, col_name in references[:5]:  # Show first 5
                print(f"    - {table_name}.{col_name}")
            if len(references) > 5:
                print(f"    ... and {len(references) - 5} more")
        
        # 4. Check for data consistency issues
        print(f"\n4. DATA CONSISTENCY CHECKS:")
        
        # Check if core tables have data
        core_tables = ['users', 'students', 'teachers', 'course', 'education_group']
        
        for table in core_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"  {table}: {count:,} records")
            except Exception as e:
                print(f"  {table}: ERROR - {e}")
        
        # 5. Check for orphaned data (sample)
        print(f"\n5. SAMPLE ORPHANED DATA CHECKS:")
        
        # Check if students reference education_group
        cursor.execute("""
            SELECT COUNT(*) as orphaned_students
            FROM education_group_student egs
            WHERE NOT EXISTS (SELECT 1 FROM students s WHERE s.id = egs.student_id)
               OR NOT EXISTS (SELECT 1 FROM education_group eg WHERE eg.id = egs.education_group_id)
        """)
        orphaned = cursor.fetchone()['orphaned_students']
        print(f"  Orphaned education_group_student records: {orphaned}")
        
        # Check course assignments
        cursor.execute("""
            SELECT COUNT(*) as orphaned_course_teachers
            FROM course_teacher ct
            WHERE NOT EXISTS (SELECT 1 FROM teachers t WHERE t.id = ct.teacher_id)
               OR NOT EXISTS (SELECT 1 FROM course c WHERE c.id = ct.course_id)
        """)
        orphaned_ct = cursor.fetchone()['orphaned_course_teachers']
        print(f"  Orphaned course_teacher records: {orphaned_ct}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_critical_issues()