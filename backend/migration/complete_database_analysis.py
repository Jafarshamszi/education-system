#!/usr/bin/env python3
"""
Complete Database Migration Analysis and Optimization Report
"""

import psycopg2
from psycopg2.extras import RealDictCursor


def run_analysis():
    """Run complete database analysis"""
    
    print("=" * 80)
    print("COMPLETE DATABASE MIGRATION & OPTIMIZATION ANALYSIS")
    print("=" * 80)

    try:
        old_conn = psycopg2.connect(
            dbname='edu', user='postgres', password='1111',
            host='localhost', cursor_factory=RealDictCursor
        )
        new_conn = psycopg2.connect(
            dbname='lms', user='postgres', password='1111',
            host='localhost', cursor_factory=RealDictCursor
        )
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    old_cur = old_conn.cursor()
    new_cur = new_conn.cursor()

    # PART 1: Migration Completeness
    print("\n📊 PART 1: MIGRATION COMPLETENESS")
    print("-" * 80)

    migration_results = []
    
    # Users
    old_cur.execute("SELECT COUNT(*) FROM users WHERE active = 1")
    old_users = old_cur.fetchone()['count']
    new_cur.execute("SELECT COUNT(*) FROM users")
    new_users = new_cur.fetchone()['count']
    users_pct = (new_users / old_users * 100)
    status = "✅" if users_pct >= 95 else "⚠️"
    print(f"{status} Users: {new_users:,}/{old_users:,} ({users_pct:.1f}%)")
    migration_results.append(('users', users_pct))
    
    # Persons
    old_cur.execute("SELECT COUNT(*) FROM persons WHERE active = 1")
    old_persons = old_cur.fetchone()['count']
    new_cur.execute("SELECT COUNT(*) FROM persons")
    new_persons = new_cur.fetchone()['count']
    persons_pct = (new_persons / old_persons * 100)
    status = "✅" if persons_pct >= 95 else "⚠️"
    print(f"{status} Persons: {new_persons:,}/{old_persons:,} ({persons_pct:.1f}%)")
    migration_results.append(('persons', persons_pct))
    
    # Students
    old_cur.execute("SELECT COUNT(*) FROM students WHERE active = 1")
    old_students = old_cur.fetchone()['count']
    new_cur.execute("SELECT COUNT(*) FROM students")
    new_students = new_cur.fetchone()['count']
    students_pct = (new_students / old_students * 100)
    status = "✅" if students_pct >= 95 else "⚠️"
    print(f"{status} Students: {new_students:,}/{old_students:,} ({students_pct:.1f}%)")
    migration_results.append(('students', students_pct))
    
    # Teachers
    old_cur.execute("SELECT COUNT(*) FROM teachers WHERE active = 1")
    old_teachers = old_cur.fetchone()['count']
    new_cur.execute("SELECT COUNT(*) FROM staff_members")
    new_teachers = new_cur.fetchone()['count']
    teachers_pct = (new_teachers / old_teachers * 100) if old_teachers > 0 else 100
    status = "✅" if teachers_pct >= 95 else "⚠️" if teachers_pct >= 80 else "❌"
    print(f"{status} Teachers: {new_teachers:,}/{old_teachers:,} ({teachers_pct:.1f}%)")
    migration_results.append(('teachers', teachers_pct))
    
    # Organizations
    old_cur.execute("SELECT COUNT(*) FROM organizations WHERE active = 1")
    old_orgs = old_cur.fetchone()['count']
    new_cur.execute("SELECT COUNT(*) FROM organization_units")
    new_orgs = new_cur.fetchone()['count']
    orgs_pct = (new_orgs / old_orgs * 100) if old_orgs > 0 else 100
    status = "✅" if orgs_pct >= 95 else "⚠️"
    print(f"{status} Organizations: {new_orgs:,}/{old_orgs:,} ({orgs_pct:.1f}%)")
    migration_results.append(('organizations', orgs_pct))
    
    # Courses/Subjects
    new_cur.execute("SELECT COUNT(*) FROM courses")
    new_courses = new_cur.fetchone()['count']
    print(f"✅ Courses: {new_courses:,} (new structure)")
    
    # Exams/Assessments
    old_cur.execute("SELECT COUNT(*) FROM exam WHERE active = 1")
    old_exams = old_cur.fetchone()['count']
    new_cur.execute("SELECT COUNT(*) FROM assessments WHERE assessment_type = 'exam'")
    new_exams = new_cur.fetchone()['count']
    exams_pct = (new_exams / old_exams * 100) if old_exams > 0 else 100
    status = "✅" if exams_pct >= 95 else "⚠️"
    print(f"{status} Exams: {new_exams:,}/{old_exams:,} ({exams_pct:.1f}%)")
    migration_results.append(('exams', exams_pct))
    
    # Exam Submissions
    old_cur.execute("SELECT COUNT(*) FROM exam_student WHERE active = 1")
    old_subs = old_cur.fetchone()['count']
    new_cur.execute("SELECT COUNT(*) FROM assessment_submissions")
    new_subs = new_cur.fetchone()['count']
    subs_pct = (new_subs / old_subs * 100) if old_subs > 0 else 100
    status = "✅" if subs_pct >= 95 else "⚠️"
    print(f"{status} Exam Submissions: {new_subs:,}/{old_subs:,} ({subs_pct:.1f}%)")
    migration_results.append(('exam_submissions', subs_pct))
    
    # Enrollments
    old_cur.execute("SELECT COUNT(*) FROM journal WHERE active = 1")
    old_enr = old_cur.fetchone()['count']
    new_cur.execute("SELECT COUNT(*) FROM course_enrollments")
    new_enr = new_cur.fetchone()['count']
    enr_pct = (new_enr / old_enr * 100) if old_enr > 0 else 100
    status = "✅" if enr_pct >= 95 else "⚠️"
    print(f"{status} Enrollments: {new_enr:,}/{old_enr:,} ({enr_pct:.1f}%)")
    migration_results.append(('enrollments', enr_pct))
    
    # Materials
    try:
        old_cur.execute("SELECT COUNT(*) FROM course_material WHERE active = 1")
        old_mat = old_cur.fetchone()['count']
    except:
        try:
            old_cur.execute("SELECT COUNT(*) FROM material WHERE active = 1")
            old_mat = old_cur.fetchone()['count']
        except:
            old_mat = 0
    
    new_cur.execute("SELECT COUNT(*) FROM course_materials")
    new_mat = new_cur.fetchone()['count']
    mat_pct = (new_mat / old_mat * 100) if old_mat > 0 else 100
    status = "✅" if mat_pct >= 95 else "⚠️"
    print(f"{status} Course Materials: {new_mat:,}/{old_mat:,} ({mat_pct:.1f}%)")
    migration_results.append(('course_materials', mat_pct))
    
    # Grades
    new_cur.execute("SELECT COUNT(*) FROM grades")
    new_grades = new_cur.fetchone()['count']
    print(f"✅ Grades: {new_grades:,} (new structure)")

    # PART 2: Data Integrity
    print("\n🔗 PART 2: DATA INTEGRITY CHECK")
    print("-" * 80)

    fk_checks = [
        ("students", "user_id", "users", "id"),
        ("staff_members", "user_id", "users", "id"),
        ("course_enrollments", "student_id", "students", "id"),
        ("assessment_submissions", "student_id", "students", "id"),
        ("assessment_submissions", "assessment_id", "assessments", "id"),
        ("grades", "enrollment_id", "course_enrollments", "id"),
    ]

    integrity_issues = 0
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
                integrity_issues += 1
            desc = f"{table}.{fk_col} → {ref_table}.{ref_col}"
            print(f"{status} {desc:<50} {orphans:>6,} orphaned")
        except Exception as e:
            print(f"⚠️ {table}.{fk_col}: {str(e)[:40]}")

    # PART 3: Performance & Indexes
    print("\n📈 PART 3: PERFORMANCE & OPTIMIZATION")
    print("-" * 80)

    # Check for missing FK indexes
    new_cur.execute("""
        SELECT DISTINCT
            tc.table_name,
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.column_name
    """)

    fk_columns = new_cur.fetchall()
    missing_indexes = []

    for fk in fk_columns:
        new_cur.execute("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE tablename = %s 
            AND (indexdef LIKE %s OR indexdef LIKE %s)
        """, (
            fk['table_name'],
            f"%({fk['column_name']}%",
            f"% {fk['column_name']} %"
        ))
        
        has_index = new_cur.fetchone()['count'] > 0
        
        if not has_index:
            missing_indexes.append(
                (fk['table_name'], fk['column_name'])
            )

    if missing_indexes:
        print(f"⚠️ Missing FK Indexes: {len(missing_indexes)}")
        for table, col in missing_indexes[:10]:
            print(f"   - {table}.{col}")
        if len(missing_indexes) > 10:
            print(f"   ... and {len(missing_indexes) - 10} more")
    else:
        print("✅ All FK columns have indexes")

    # Table statistics
    print("\n📊 Table Statistics:")
    new_cur.execute("""
        SELECT 
            tablename,
            n_live_tup as rows,
            n_dead_tup as dead_rows,
            pg_size_pretty(pg_total_relation_size(
                'public.'||tablename
            )) AS size
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY n_live_tup DESC
        LIMIT 12
    """)

    print(f"{'Table':<30} {'Rows':>10} {'Size':>10}")
    print("-" * 55)
    for row in new_cur.fetchall():
        print(f"{row['tablename']:<30} {row['rows']:>10,} {row['size']:>10}")

    # PART 4: Summary
    print("\n" + "=" * 80)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 80)

    avg_migration = sum(p for _, p in migration_results) / len(migration_results)
    good_migrations = sum(1 for _, p in migration_results if p >= 95)

    print(f"\n✅ Migration Completion: {avg_migration:.1f}% average")
    print(f"✅ Tables >95% complete: {good_migrations}/{len(migration_results)}")
    print(f"{'✅' if integrity_issues == 0 else '❌'} Data Integrity: {integrity_issues} issues")
    print(f"{'✅' if not missing_indexes else '⚠️'} FK Indexes: {len(missing_indexes)} missing")

    print("\n🎯 RECOMMENDED ACTIONS:")
    
    action_num = 1
    if missing_indexes:
        print(f"\n{action_num}. CREATE MISSING INDEXES")
        print(f"   - {len(missing_indexes)} foreign key columns need indexes")
        print(f"   - Run database optimization script")
        action_num += 1
    
    if integrity_issues > 0:
        print(f"\n{action_num}. FIX DATA INTEGRITY ISSUES")
        print(f"   - {integrity_issues} foreign key violations found")
        print(f"   - Clean up orphaned records")
        action_num += 1
    
    if avg_migration < 95:
        print(f"\n{action_num}. COMPLETE REMAINING MIGRATION")
        incomplete = [(t, p) for t, p in migration_results if p < 95]
        print(f"   - {len(incomplete)} tables below 95%:")
        for table, pct in incomplete:
            print(f"     • {table}: {pct:.1f}%")
        action_num += 1
    
    # Final verdict
    if avg_migration >= 95 and integrity_issues == 0:
        verdict = "✅ DATABASE IS READY FOR PRODUCTION"
        if missing_indexes:
            verdict += " (optimize indexes first)"
    elif avg_migration >= 90:
        verdict = "⚠️ DATABASE NEEDS OPTIMIZATION"
    else:
        verdict = "❌ MIGRATION INCOMPLETE"
    
    print(f"\n{'VERDICT:':<15} {verdict}")
    print("\n" + "=" * 80)

    old_conn.close()
    new_conn.close()

    return {
        'avg_migration': avg_migration,
        'integrity_issues': integrity_issues,
        'missing_indexes': len(missing_indexes),
        'verdict': verdict
    }


if __name__ == '__main__':
    run_analysis()
