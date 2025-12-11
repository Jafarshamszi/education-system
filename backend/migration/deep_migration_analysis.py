#!/usr/bin/env python3
"""
Deep Migration Analysis Script
Analyzes migration completeness, data integrity, and performance optimization opportunities
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

def analyze_migration():
    print("=" * 80)
    print("DEEP MIGRATION ANALYSIS - COMPREHENSIVE DATABASE AUDIT")
    print("=" * 80)

    old_conn = psycopg2.connect(dbname='edu', user='postgres', password='1111', host='localhost', cursor_factory=RealDictCursor)
    new_conn = psycopg2.connect(dbname='lms', user='postgres', password='1111', host='localhost', cursor_factory=RealDictCursor)

    old_cur = old_conn.cursor()
    new_cur = new_conn.cursor()

    # 1. TABLE MIGRATION COMPLETENESS
    print("\n📊 1. TABLE MIGRATION STATUS")
    print("-" * 80)

    tables_check = [
        ('users', 'users', 'id', 'metadata->>\'old_user_id\''),
        ('persons', 'students', 'id', 'metadata->>\'old_person_id\''),
        ('students', 'students', 'id', 'metadata->>\'old_student_id\''),
        ('teachers', 'staff_members', 'id', 'metadata->>\'old_teacher_id\''),
        ('organizations', 'organizations', 'id', 'metadata->>\'old_org_id\''),
        ('courses', 'courses', 'id', 'metadata->>\'old_course_id\''),
        ('subjects', 'courses', 'id', 'metadata->>\'old_subject_id\''),
        ('exam', 'assessments', 'id', 'metadata->>\'old_exam_id\''),
        ('exam_student', 'assessment_submissions', None, None),
        ('education_plan', 'courses', 'id', 'metadata->>\'old_education_plan_id\''),
        ('course_material', 'course_materials', 'id', 'metadata->>\'old_material_id\''),
    ]

    migration_results = []
    for old_table, new_table, old_id_col, metadata_path in tables_check:
        try:
            old_cur.execute(f"SELECT COUNT(*) FROM {old_table} WHERE active = 1")
            old_count = old_cur.fetchone()['count']
        except:
            try:
                old_cur.execute(f"SELECT COUNT(*) FROM {old_table}")
                old_count = old_cur.fetchone()['count']
            except:
                old_count = 0
        
        try:
            if metadata_path:
                new_cur.execute(f"SELECT COUNT(*) FROM {new_table} WHERE {metadata_path} IS NOT NULL")
            else:
                new_cur.execute(f"SELECT COUNT(*) FROM {new_table}")
            new_count = new_cur.fetchone()['count']
        except:
            new_count = 0
        
        coverage = (new_count / old_count * 100) if old_count > 0 else 0
        status = "✅" if coverage >= 95 else "⚠️" if coverage >= 80 else "❌"
        migration_results.append({
            'old_table': old_table,
            'new_table': new_table,
            'old_count': old_count,
            'new_count': new_count,
            'coverage': coverage,
            'status': status
        })
        print(f"{status} {old_table:20} -> {new_table:20} | {old_count:6} -> {new_count:6} ({coverage:5.1f}%)")

    # 2. FOREIGN KEY INTEGRITY
    print("\n🔗 2. FOREIGN KEY INTEGRITY CHECK")
    print("-" * 80)

    fk_checks = [
        ('students', 'user_id', 'users', 'id'),
        ('staff_members', 'user_id', 'users', 'id'),
        ('courses', 'organization_id', 'organizations', 'id'),
        ('courses', 'subject_id', 'subjects', 'id'),
        ('enrollments', 'student_id', 'students', 'id'),
        ('enrollments', 'course_id', 'courses', 'id'),
        ('assessment_submissions', 'student_id', 'students', 'id'),
        ('assessment_submissions', 'assessment_id', 'assessments', 'id'),
        ('course_materials', 'course_id', 'courses', 'id'),
        ('grades', 'enrollment_id', 'enrollments', 'id'),
    ]

    fk_issues = []
    for table, fk_col, ref_table, ref_col in fk_checks:
        try:
            new_cur.execute(f"""
                SELECT COUNT(*) as orphans
                FROM {table} t
                LEFT JOIN {ref_table} r ON t.{fk_col} = r.{ref_col}
                WHERE r.{ref_col} IS NULL AND t.{fk_col} IS NOT NULL
            """)
            orphans = new_cur.fetchone()['orphans']
            status = "✅" if orphans == 0 else "❌"
            if orphans > 0:
                fk_issues.append(f"{table}.{fk_col} -> {ref_table}.{ref_col}: {orphans} orphaned records")
            print(f"{status} {table}.{fk_col} -> {ref_table}.{ref_col}: {orphans} orphaned records")
        except Exception as e:
            print(f"⚠️ {table}.{fk_col} -> {ref_table}.{ref_col}: Error - {str(e)[:50]}")

    # 3. DATA QUALITY ISSUES
    print("\n🔍 3. DATA QUALITY ANALYSIS")
    print("-" * 80)

    critical_fields = [
        ('users', 'email'),
        ('users', 'username'),
        ('students', 'user_id'),
        ('students', 'student_number'),
        ('staff_members', 'user_id'),
        ('courses', 'course_code'),
        ('courses', 'name'),
        ('enrollments', 'student_id'),
        ('enrollments', 'course_id'),
    ]

    null_issues = []
    for table, field in critical_fields:
        try:
            new_cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {field} IS NULL")
            null_count = new_cur.fetchone()['count']
            
            new_cur.execute(f"SELECT COUNT(*) FROM {table}")
            total_count = new_cur.fetchone()['count']
            
            status = "✅" if null_count == 0 else "⚠️"
            if null_count > 0:
                null_issues.append(f"{table}.{field}: {null_count}/{total_count} NULL values")
            print(f"{status} {table}.{field}: {null_count}/{total_count} NULL values")
        except:
            pass

    # 4. DUPLICATE DETECTION
    print("\n🔄 4. DUPLICATE DETECTION")
    print("-" * 80)

    duplicate_checks = [
        ('users', 'email'),
        ('users', 'username'),
        ('students', 'student_number'),
        ('staff_members', 'staff_number'),
        ('courses', 'course_code'),
        ('organizations', 'code'),
    ]

    duplicate_issues = []
    for table, field in duplicate_checks:
        try:
            new_cur.execute(f"""
                SELECT COUNT(*) as dup_count
                FROM (
                    SELECT {field}, COUNT(*) as cnt
                    FROM {table}
                    WHERE {field} IS NOT NULL
                    GROUP BY {field}
                    HAVING COUNT(*) > 1
                ) dupes
            """)
            dup_count = new_cur.fetchone()['dup_count']
            status = "✅" if dup_count == 0 else "❌"
            if dup_count > 0:
                duplicate_issues.append(f"{table}.{field}: {dup_count} duplicate values")
            print(f"{status} {table}.{field}: {dup_count} duplicate values")
        except:
            pass

    # 5. MISSING CRITICAL DATA
    print("\n⚠️ 5. MISSING CRITICAL RELATIONSHIPS")
    print("-" * 80)

    # Students without enrollments
    new_cur.execute("""
        SELECT COUNT(*) 
        FROM students s
        LEFT JOIN enrollments e ON s.id = e.student_id
        WHERE e.id IS NULL
    """)
    students_no_enrollments = new_cur.fetchone()['count']
    print(f"⚠️ Students without enrollments: {students_no_enrollments}")

    # Courses without enrollments
    new_cur.execute("""
        SELECT COUNT(*) 
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        WHERE e.id IS NULL
    """)
    courses_no_enrollments = new_cur.fetchone()['count']
    print(f"⚠️ Courses without enrollments: {courses_no_enrollments}")

    # Teachers without courses
    try:
        new_cur.execute("""
            SELECT COUNT(*) 
            FROM staff_members s
            LEFT JOIN courses c ON s.id = c.instructor_id
            WHERE c.id IS NULL AND s.metadata->>'old_teacher_id' IS NOT NULL
        """)
        teachers_no_courses = new_cur.fetchone()['count']
        print(f"⚠️ Teachers without courses: {teachers_no_courses}")
    except:
        print(f"⚠️ Teachers without courses: Could not check")

    # 6. INDEX ANALYSIS
    print("\n📈 6. INDEX ANALYSIS")
    print("-" * 80)

    new_cur.execute("""
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname
    """)

    indexes = new_cur.fetchall()
    index_count_by_table = {}
    for idx in indexes:
        table = idx['tablename']
        index_count_by_table[table] = index_count_by_table.get(table, 0) + 1

    print(f"Total indexes: {len(indexes)}")
    print("\nIndexes per table:")
    for table, count in sorted(index_count_by_table.items()):
        try:
            new_cur.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = new_cur.fetchone()['count']
            status = "✅" if count >= 2 else "⚠️" if count >= 1 else "❌"
            print(f"{status} {table:25} {count} indexes, {row_count:,} rows")
        except:
            pass

    # 7. MISSING INDEXES RECOMMENDATION
    print("\n💡 7. RECOMMENDED INDEXES")
    print("-" * 80)

    new_cur.execute("""
        SELECT DISTINCT
            tc.table_name,
            kcu.column_name,
            CASE WHEN i.indexname IS NULL THEN 'Missing' ELSE 'Exists' END as index_status
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        LEFT JOIN pg_indexes i 
            ON i.tablename = tc.table_name 
            AND i.indexdef LIKE '%' || kcu.column_name || '%'
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.column_name
    """)

    missing_fk_indexes = []
    for row in new_cur.fetchall():
        if row['index_status'] == 'Missing':
            missing_fk_indexes.append(row)
            print(f"❌ Missing index on {row['table_name']}.{row['column_name']}")

    if not missing_fk_indexes:
        print("✅ All foreign key columns are indexed")

    # 8. STATISTICS SUMMARY
    print("\n📊 8. DATABASE STATISTICS SUMMARY")
    print("-" * 80)

    new_cur.execute("""
        SELECT 
            schemaname,
            tablename,
            n_live_tup as row_count,
            n_dead_tup as dead_rows,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY n_live_tup DESC
    """)

    print(f"{'Table':<25} {'Rows':>10} {'Dead Rows':>12} {'Last Analyze':<20}")
    print("-" * 70)
    for row in new_cur.fetchall():
        analyze_time = row['last_autoanalyze'] or row['last_analyze'] or 'Never'
        if analyze_time != 'Never':
            analyze_time = str(analyze_time)[:19]
        print(f"{row['tablename']:<25} {row['row_count']:>10,} {row['dead_rows']:>12,} {analyze_time:<20}")

    # 9. GENERATE SUMMARY REPORT
    print("\n" + "=" * 80)
    print("MIGRATION ANALYSIS SUMMARY")
    print("=" * 80)
    
    avg_coverage = sum(r['coverage'] for r in migration_results) / len(migration_results)
    below_95 = [r for r in migration_results if r['coverage'] < 95]
    
    print(f"\n✅ Average Migration Coverage: {avg_coverage:.1f}%")
    print(f"✅ Tables with >95% coverage: {len([r for r in migration_results if r['coverage'] >= 95])}/{len(migration_results)}")
    
    if below_95:
        print(f"\n⚠️ Tables below 95% coverage:")
        for r in below_95:
            print(f"   - {r['old_table']} -> {r['new_table']}: {r['coverage']:.1f}%")
    
    if fk_issues:
        print(f"\n❌ Foreign Key Issues: {len(fk_issues)}")
        for issue in fk_issues[:5]:
            print(f"   - {issue}")
    else:
        print(f"\n✅ No Foreign Key Issues")
    
    if duplicate_issues:
        print(f"\n❌ Duplicate Value Issues: {len(duplicate_issues)}")
        for issue in duplicate_issues[:5]:
            print(f"   - {issue}")
    else:
        print(f"\n✅ No Duplicate Value Issues")
    
    if null_issues:
        print(f"\n⚠️ NULL Value Issues: {len(null_issues)}")
        for issue in null_issues[:5]:
            print(f"   - {issue}")
    
    if missing_fk_indexes:
        print(f"\n⚠️ Missing Indexes on FK Columns: {len(missing_fk_indexes)}")
        print(f"   Performance may be impacted for joins")
    else:
        print(f"\n✅ All FK columns are properly indexed")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    old_conn.close()
    new_conn.close()

    # Return summary for further processing
    return {
        'migration_results': migration_results,
        'fk_issues': fk_issues,
        'duplicate_issues': duplicate_issues,
        'null_issues': null_issues,
        'missing_indexes': missing_fk_indexes,
        'avg_coverage': avg_coverage
    }

if __name__ == '__main__':
    analyze_migration()
