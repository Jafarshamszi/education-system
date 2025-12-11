#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor
import json

def analyze_relationships():
    """Analyze potential relationships and create improved schema documentation"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='edu',
            user='postgres',
            password='1111',
            port=5432
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== RELATIONSHIP ANALYSIS FOR IMPROVED SCHEMA ===\n")
        
        # 1. Core Entity Analysis
        core_entities = {
            'users': 'System users and authentication',
            'persons': 'Person information (names, personal data)',
            'students': 'Student-specific information',
            'teachers': 'Teacher-specific information',
            'course': 'Course instances',
            'education_group': 'Class groups/sections',
            'dictionaries': 'Reference/lookup data',
            'organizations': 'Organizational units'
        }
        
        print("1. CORE ENTITIES ANALYSIS:")
        for table, description in core_entities.items():
            try:
                # Get table structure
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position
                """, (table,))
                columns = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                
                print(f"\n{table.upper()} ({count:,} records): {description}")
                
                # Show key columns
                key_columns = []
                fk_columns = []
                
                for col in columns:
                    col_name = col['column_name']
                    if col_name == 'id':
                        key_columns.append(f"id (PK)")
                    elif col_name.endswith('_id') and col_name != 'id':
                        fk_columns.append(col_name)
                    elif col_name in ['name', 'firstname', 'lastname', 'code', 'title']:
                        key_columns.append(col_name)
                
                if key_columns:
                    print(f"  Key columns: {', '.join(key_columns)}")
                if fk_columns:
                    print(f"  Foreign keys: {', '.join(fk_columns)}")
                
            except Exception as e:
                print(f"\n{table.upper()}: ERROR - {e}")
        
        # 2. Relationship Mapping
        print("\n\n2. DETECTED RELATIONSHIP PATTERNS:")
        
        relationships = [
            {
                'name': 'User Authentication Chain',
                'tables': ['users', 'accounts', 'persons'],
                'description': 'users -> accounts -> persons (authentication to personal data)',
                'query': '''
                    SELECT 
                        COUNT(DISTINCT u.id) as users,
                        COUNT(DISTINCT a.id) as accounts, 
                        COUNT(DISTINCT p.id) as persons
                    FROM users u
                    LEFT JOIN accounts a ON u.account_id = a.id
                    LEFT JOIN persons p ON a.person_id = p.id
                '''
            },
            {
                'name': 'Student Management',
                'tables': ['students', 'education_group', 'education_group_student'],
                'description': 'students <-> education_group_student <-> education_group',
                'query': '''
                    SELECT 
                        COUNT(DISTINCT s.id) as students,
                        COUNT(DISTINCT eg.id) as education_groups,
                        COUNT(DISTINCT egs.id) as student_group_links
                    FROM students s
                    LEFT JOIN education_group_student egs ON s.id = egs.student_id
                    LEFT JOIN education_group eg ON egs.education_group_id = eg.id
                '''
            },
            {
                'name': 'Course Management',
                'tables': ['course', 'course_teacher', 'course_student'],
                'description': 'course <-> course_teacher/course_student <-> teachers/students',
                'query': '''
                    SELECT 
                        COUNT(DISTINCT c.id) as courses,
                        COUNT(DISTINCT ct.teacher_id) as course_teachers,
                        COUNT(DISTINCT cs.student_id) as course_students
                    FROM course c
                    LEFT JOIN course_teacher ct ON c.id = ct.course_id
                    LEFT JOIN course_student cs ON c.id = cs.course_id
                '''
            },
            {
                'name': 'Dictionary/Reference Data',
                'tables': ['dictionaries', 'dictionary_types'],
                'description': 'dictionaries -> dictionary_types (lookup system)',
                'query': '''
                    SELECT 
                        COUNT(DISTINCT d.id) as dictionary_entries,
                        COUNT(DISTINCT dt.id) as dictionary_types
                    FROM dictionaries d
                    LEFT JOIN dictionary_types dt ON d.type_id = dt.id
                '''
            }
        ]
        
        for rel in relationships:
            print(f"\n{rel['name']}:")
            print(f"  Pattern: {rel['description']}")
            try:
                cursor.execute(rel['query'])
                result = cursor.fetchone()
                for key, value in result.items():
                    print(f"  {key}: {value:,}")
            except Exception as e:
                print(f"  Error analyzing: {e}")
        
        # 3. Generate improved schema suggestions
        print(f"\n\n3. SCHEMA IMPROVEMENT RECOMMENDATIONS:")
        
        improvements = [
            "Add proper foreign key constraints to enforce referential integrity",
            "Consolidate duplicate/backup tables (found 41 backup tables)", 
            "Standardize naming convention (currently mixed snake_case/camelCase)",
            "Add proper indexes on frequently queried foreign key columns",
            "Implement cascade delete/update rules where appropriate",
            "Add check constraints for data validation",
            "Create views for complex joins to improve query performance",
            "Implement proper audit trail with created_at/updated_at timestamps",
            "Add database-level permissions and row-level security",
            "Create proper documentation and ER diagrams"
        ]
        
        for i, improvement in enumerate(improvements, 1):
            print(f"  {i}. {improvement}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_relationships()