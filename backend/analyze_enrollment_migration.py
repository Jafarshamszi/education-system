#!/usr/bin/env python3
"""
Analyze enrollment data in OLD (edu) and NEW (lms) databases
and prepare for migration if needed.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json

def analyze_old_database():
    """Analyze OLD database (edu) for enrollment data"""
    print("=" * 80)
    print("ANALYZING OLD DATABASE (edu)")
    print("=" * 80)
    
    conn = psycopg2.connect(
        dbname="edu",
        user="postgres",
        password="1111",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Find tables related to enrollment
    print("\n1. Finding enrollment-related tables...")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND (
            table_name LIKE '%enroll%' OR 
            table_name LIKE '%student%' OR 
            table_name LIKE '%course%' OR
            table_name LIKE '%class%'
        )
        ORDER BY table_name;
    """)
    
    tables = cur.fetchall()
    print(f"\nFound {len(tables)} relevant tables:")
    for table in tables:
        print(f"  - {table['table_name']}")
    
    # Analyze each table structure
    print("\n2. Analyzing table structures...")
    
    for table in tables:
        table_name = table['table_name']
        print(f"\n--- Table: {table_name} ---")
        
        # Get column information
        cur.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, [table_name])
        
        columns = cur.fetchall()
        print(f"Columns ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) as count FROM {table_name};")
        count = cur.fetchone()['count']
        print(f"Row count: {count}")
        
        # Show sample data if table has rows
        if count > 0 and count <= 10:
            cur.execute(f"SELECT * FROM {table_name} LIMIT 5;")
            samples = cur.fetchall()
            print(f"Sample data:")
            for sample in samples:
                print(f"  {dict(sample)}")
    
    # Look for specific enrollment relationships
    print("\n" + "=" * 80)
    print("3. Searching for enrollment relationships...")
    print("=" * 80)
    
    # Check for student-course relationships
    enrollment_queries = [
        ("Journal entries", "SELECT COUNT(*) FROM journal;"),
        ("Students with courses", """
            SELECT s.student_id, s.first_name, s.last_name, COUNT(j.id) as course_count
            FROM students s
            LEFT JOIN journal j ON s.id = j.student_id
            GROUP BY s.student_id, s.first_name, s.last_name
            HAVING COUNT(j.id) > 0
            LIMIT 10;
        """),
    ]
    
    for query_name, query in enrollment_queries:
        try:
            print(f"\n{query_name}:")
            cur.execute(query)
            results = cur.fetchall()
            for result in results:
                print(f"  {dict(result)}")
        except Exception as e:
            print(f"  Error: {e}")
    
    cur.close()
    conn.close()


def analyze_new_database():
    """Analyze NEW database (lms) for enrollment data"""
    print("\n\n" + "=" * 80)
    print("ANALYZING NEW DATABASE (lms)")
    print("=" * 80)
    
    conn = psycopg2.connect(
        dbname="lms",
        user="postgres",
        password="1111",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Find enrollment-related tables
    print("\n1. Finding enrollment-related tables...")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND (
            table_name LIKE '%enroll%' OR 
            table_name LIKE '%student%' OR 
            table_name LIKE '%course%'
        )
        ORDER BY table_name;
    """)
    
    tables = cur.fetchall()
    print(f"\nFound {len(tables)} relevant tables:")
    for table in tables:
        print(f"  - {table['table_name']}")
    
    # Analyze course_enrollments table if it exists
    print("\n2. Analyzing course_enrollments table...")
    
    try:
        cur.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'course_enrollments'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        if columns:
            print(f"\nCourse_enrollments columns ({len(columns)}):")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")
            
            # Check for foreign keys
            cur.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = 'course_enrollments';
            """)
            
            fkeys = cur.fetchall()
            if fkeys:
                print("\nForeign keys:")
                for fkey in fkeys:
                    print(f"  {fkey['column_name']} -> {fkey['foreign_table_name']}.{fkey['foreign_column_name']}")
            
            # Check row count
            cur.execute("SELECT COUNT(*) as count FROM course_enrollments;")
            count = cur.fetchone()['count']
            print(f"\nRow count: {count}")
            
            if count > 0:
                cur.execute("SELECT * FROM course_enrollments LIMIT 5;")
                samples = cur.fetchall()
                print(f"\nSample data:")
                for sample in samples:
                    print(f"  {dict(sample)}")
            else:
                print("\n⚠️  WARNING: course_enrollments table is EMPTY!")
        else:
            print("\n⚠️  WARNING: course_enrollments table does NOT exist!")
    except Exception as e:
        print(f"\n⚠️  ERROR: {e}")
    
    # Check for students table
    print("\n3. Analyzing students table...")
    try:
        cur.execute("""
            SELECT 
                column_name, 
                data_type 
            FROM information_schema.columns
            WHERE table_name = 'students'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        if columns:
            print(f"\nStudents table columns ({len(columns)}):")
            for col in columns:
                print(f"  {col['column_name']}: {col['data_type']}")
            
            cur.execute("SELECT COUNT(*) as count FROM students;")
            count = cur.fetchone()['count']
            print(f"Row count: {count}")
            
            if count > 0:
                cur.execute("SELECT * FROM students LIMIT 3;")
                samples = cur.fetchall()
                print(f"\nSample students:")
                for sample in samples:
                    print(f"  {dict(sample)}")
        else:
            print("\n⚠️  WARNING: students table does NOT exist!")
    except Exception as e:
        print(f"\n⚠️  ERROR: {e}")
    
    # Check for course_offerings
    print("\n4. Checking course_offerings...")
    try:
        cur.execute("SELECT COUNT(*) as count FROM course_offerings;")
        count = cur.fetchone()['count']
        print(f"Course offerings count: {count}")
        
        if count > 0:
            cur.execute("""
                SELECT 
                    id, 
                    course_id, 
                    section_code,
                    max_enrollment,
                    current_enrollment
                FROM course_offerings 
                LIMIT 5;
            """)
            samples = cur.fetchall()
            print(f"\nSample course offerings:")
            for sample in samples:
                print(f"  {dict(sample)}")
    except Exception as e:
        print(f"\n⚠️  ERROR: {e}")
    
    cur.close()
    conn.close()


def compare_and_recommend():
    """Compare both databases and provide migration recommendations"""
    print("\n\n" + "=" * 80)
    print("MIGRATION ANALYSIS AND RECOMMENDATIONS")
    print("=" * 80)
    
    # Connect to both databases
    old_conn = psycopg2.connect(
        dbname="edu",
        user="postgres",
        password="1111",
        host="localhost",
        port="5432"
    )
    old_cur = old_conn.cursor(cursor_factory=RealDictCursor)
    
    new_conn = psycopg2.connect(
        dbname="lms",
        user="postgres",
        password="1111",
        host="localhost",
        port="5432"
    )
    new_cur = new_conn.cursor(cursor_factory=RealDictCursor)
    
    # Count enrollments in old database
    print("\n1. Enrollment counts in OLD database (edu):")
    try:
        old_cur.execute("SELECT COUNT(*) as count FROM journal;")
        old_journal_count = old_cur.fetchone()['count']
        print(f"   Journal entries: {old_journal_count}")
        
        old_cur.execute("""
            SELECT COUNT(DISTINCT student_id) as count 
            FROM journal;
        """)
        old_students = old_cur.fetchone()['count']
        print(f"   Unique students: {old_students}")
        
        old_cur.execute("""
            SELECT COUNT(DISTINCT class_id) as count 
            FROM journal;
        """)
        old_classes = old_cur.fetchone()['count']
        print(f"   Unique classes: {old_classes}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Count enrollments in new database
    print("\n2. Enrollment counts in NEW database (lms):")
    try:
        new_cur.execute("""
            SELECT COUNT(*) as count 
            FROM course_enrollments;
        """)
        new_enrollments = new_cur.fetchone()['count']
        print(f"   Course enrollments: {new_enrollments}")
        
        if new_enrollments == 0:
            print("\n   ⚠️  CRITICAL: No enrollment data in NEW database!")
            print("   📋 RECOMMENDATION: Migration is REQUIRED")
    except Exception as e:
        print(f"   Error: {e}")
        print("\n   ⚠️  CRITICAL: course_enrollments table may not exist!")
        print("   📋 RECOMMENDATION: Create table and migrate data")
    
    # Check for matching students
    print("\n3. Checking student data correspondence...")
    try:
        old_cur.execute("""
            SELECT student_id, first_name, last_name 
            FROM students 
            LIMIT 5;
        """)
        old_students = old_cur.fetchall()
        print(f"\n   OLD database students sample:")
        for student in old_students:
            print(f"     {student['student_id']}: {student['first_name']} {student['last_name']}")
        
        new_cur.execute("""
            SELECT id, user_id 
            FROM students 
            LIMIT 5;
        """)
        new_students = new_cur.fetchall()
        print(f"\n   NEW database students sample:")
        for student in new_students:
            print(f"     {dict(student)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("""
1. Review the analysis above
2. Identify the mapping between OLD and NEW schemas
3. Create a migration script to:
   - Map students from OLD to NEW (student_id -> student UUID)
   - Map courses from OLD to NEW (class_id -> course_offering_id)
   - Insert enrollment records into course_enrollments
4. Validate the migration
5. Update current_enrollment counts in course_offerings
""")
    
    old_cur.close()
    old_conn.close()
    new_cur.close()
    new_conn.close()


if __name__ == "__main__":
    try:
        analyze_old_database()
        analyze_new_database()
        compare_and_recommend()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
