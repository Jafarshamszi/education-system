#!/usr/bin/env python3
"""
Final Migration Validation and Summary Report
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Database configs
OLD_DB = {
    'host': 'localhost', 'port': 5432, 'database': 'edu',
    'user': 'postgres', 'password': '1111'
}
NEW_DB = {
    'host': 'localhost', 'port': 5432, 'database': 'lms',
    'user': 'postgres', 'password': '1111'
}


def validate_complete_migration():
    """Comprehensive validation of migration"""
    logger.info("=" * 100)
    logger.info("COMPLETE MIGRATION VALIDATION REPORT")
    logger.info(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 100)
    
    old_conn = psycopg2.connect(**OLD_DB)
    new_conn = psycopg2.connect(**NEW_DB)
    
    try:
        with old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with new_conn.cursor(cursor_factory=RealDictCursor) as new_cur:
                
                # Define all data categories to validate
                validations = [
                    {
                        'category': 'Users & Persons',
                        'old_query': "SELECT COUNT(*) FROM accounts WHERE active = 1",
                        'new_query': "SELECT COUNT(*) FROM users WHERE is_active = true"
                    },
                    {
                        'category': 'Students',
                        'old_query': "SELECT COUNT(*) FROM students WHERE active = 1",
                        'new_query': "SELECT COUNT(*) FROM students"
                    },
                    {
                        'category': 'Teachers/Staff',
                        'old_query': "SELECT COUNT(*) FROM teachers WHERE active = 1",
                        'new_query': "SELECT COUNT(*) FROM staff_members"
                    },
                    {
                        'category': 'Organizations',
                        'old_query': "SELECT COUNT(*) FROM organizations WHERE active = 1",
                        'new_query': "SELECT COUNT(*) FROM organization_units"
                    },
                    {
                        'category': 'Courses (Master Catalog)',
                        'old_query': "SELECT COUNT(*) FROM subject_catalog WHERE active = 1",
                        'new_query': "SELECT COUNT(*) FROM courses"
                    },
                    {
                        'category': 'Course Offerings (Instances)',
                        'old_query': "SELECT COUNT(*) FROM course WHERE active = 1",
                        'new_query': "SELECT COUNT(*) FROM course_offerings"
                    },
                    {
                        'category': 'Enrollments',
                        'old_query': "SELECT COUNT(*) FROM journal WHERE active = 1",
                        'new_query': "SELECT COUNT(*) FROM course_enrollments"
                    },
                    {
                        'category': 'Exams',
                        'old_query': "SELECT COUNT(*) FROM exam WHERE active = 1",
                        'new_query': "SELECT COUNT(*) FROM assessments WHERE assessment_type = 'exam'"
                    },
                    {
                        'category': 'All Assessments',
                        'old_query': "SELECT COUNT(*) FROM exam WHERE active = 1",
                        'new_query': "SELECT COUNT(*) FROM assessments"
                    },
                    {
                        'category': 'Assessment Submissions',
                        'old_query': "SELECT COUNT(*) FROM exam_student",
                        'new_query': "SELECT COUNT(*) FROM assessment_submissions"
                    },
                ]
                
                total_old = 0
                total_new = 0
                
                print("\n")
                logger.info(f"{'Category':<40} | {'Old DB':>12} | {'New DB':>12} | {'Coverage':>10}")
                logger.info("-" * 100)
                
                for validation in validations:
                    old_cur.execute(validation['old_query'])
                    old_count = old_cur.fetchone()['count']
                    
                    new_cur.execute(validation['new_query'])
                    new_count = new_cur.fetchone()['count']
                    
                    coverage = (new_count / old_count * 100) if old_count > 0 else 0
                    status = "✅" if coverage >= 95 else "⚠️" if coverage >= 70 else "❌"
                    
                    logger.info(
                        f"{validation['category']:<40} | {old_count:>12,} | {new_count:>12,} | "
                        f"{coverage:>9.1f}% {status}"
                    )
                    
                    if validation['category'] not in ['All Assessments']:  # Don't double count
                        total_old += old_count
                        total_new += new_count
                
                # Overall statistics
                logger.info("-" * 100)
                overall_coverage = (total_new / total_old * 100) if total_old > 0 else 0
                logger.info(
                    f"{'TOTAL':<40} | {total_old:>12,} | {total_new:>12,} | "
                    f"{overall_coverage:>9.1f}%"
                )
                
                # Additional statistics
                logger.info("\n" + "=" * 100)
                logger.info("ADDITIONAL STATISTICS")
                logger.info("=" * 100)
                
                # Course instructors
                old_cur.execute("SELECT COUNT(*) FROM course_teacher WHERE active = 1")
                old_instructors = old_cur.fetchone()['count']
                
                new_cur.execute("SELECT COUNT(*) FROM course_instructors")
                new_instructors = new_cur.fetchone()['count']
                
                logger.info(f"\nCourse Instructor Assignments:")
                logger.info(f"  Old DB: {old_instructors:,}")
                logger.info(f"  New DB: {new_instructors:,}")
                logger.info(f"  Coverage: {(new_instructors/old_instructors*100) if old_instructors > 0 else 0:.1f}%")
                
                # Class schedules
                old_cur.execute("SELECT COUNT(*) FROM course_meeting WHERE active = 1")
                old_schedules = old_cur.fetchone()['count']
                
                new_cur.execute("SELECT COUNT(*) FROM class_schedules")
                new_schedules = new_cur.fetchone()['count']
                
                logger.info(f"\nClass Schedules:")
                logger.info(f"  Old DB: {old_schedules:,}")
                logger.info(f"  New DB: {new_schedules:,}")
                
                # Summary
                logger.info("\n" + "=" * 100)
                logger.info("MIGRATION SUMMARY")
                logger.info("=" * 100)
                logger.info(f"\n✅ Successfully migrated {total_new:,} out of {total_old:,} records")
                logger.info(f"📊 Overall coverage: {overall_coverage:.2f}%")
                
                if overall_coverage >= 95:
                    logger.info("\n🎉 MIGRATION COMPLETE - Excellent coverage!")
                elif overall_coverage >= 85:
                    logger.info("\n✅ MIGRATION MOSTLY COMPLETE - Good coverage")
                else:
                    logger.info("\n⚠️  MIGRATION INCOMPLETE - Additional work needed")
                
                logger.info("\n" + "=" * 100)
                
    finally:
        old_conn.close()
        new_conn.close()


if __name__ == "__main__":
    validate_complete_migration()
