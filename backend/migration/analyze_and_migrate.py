#!/usr/bin/env python3
"""
Complete Migration Execution Script
Migrates ALL remaining data from old edu database to new lms database
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import uuid
import json
import logging
from datetime import datetime
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'complete_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
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


class CompleteMigration:
    def __init__(self):
        self.old_conn = psycopg2.connect(**OLD_DB)
        self.new_conn = psycopg2.connect(**NEW_DB)
        self.id_mappings = {}
        self.stats = {}
        
    def close(self):
        if self.old_conn:
            self.old_conn.close()
        if self.new_conn:
            self.new_conn.close()
    
    def build_existing_mappings(self):
        """Build ID mappings from existing migrated data"""
        logger.info("Building existing ID mappings...")
        
        with self.old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with self.new_conn.cursor(cursor_factory=RealDictCursor) as new_cur:
                
                # Students mapping
                self.id_mappings['students'] = {}
                new_cur.execute("""
                    SELECT id, metadata->>'old_student_id' as old_id 
                    FROM students 
                    WHERE metadata->>'old_student_id' IS NOT NULL
                """)
                for row in new_cur.fetchall():
                    if row['old_id']:
                        self.id_mappings['students'][int(row['old_id'])] = row['id']
                
                logger.info(f"  Loaded {len(self.id_mappings['students'])} student mappings")
                
                # Courses mapping
                self.id_mappings['courses'] = {}
                new_cur.execute("SELECT id, code FROM courses")
                courses_by_code = {row['code']: row['id'] for row in new_cur.fetchall()}
                
                old_cur.execute("SELECT id FROM subject_catalog WHERE active = 1")
                for row in old_cur.fetchall():
                    subject_id = row['id']
                    course_code = f"SUBJ{subject_id % 100000:05d}"
                    if course_code in courses_by_code:
                        self.id_mappings['courses'][subject_id] = courses_by_code[course_code]
                
                logger.info(f"  Loaded {len(self.id_mappings['courses'])} course mappings")
                
                # Course offerings mapping
                self.id_mappings['course_offerings'] = {}
                new_cur.execute("""
                    SELECT id, section_code, 
                           metadata->>'old_course_id' as old_id
                    FROM course_offerings
                    WHERE metadata->>'old_course_id' IS NOT NULL
                """)
                for row in new_cur.fetchall():
                    if row['old_id']:
                        self.id_mappings['course_offerings'][int(row['old_id'])] = row['id']
                
                logger.info(f"  Loaded {len(self.id_mappings['course_offerings'])} course offering mappings")
                
                # Teachers/Staff mapping
                self.id_mappings['staff'] = {}
                new_cur.execute("""
                    SELECT id, user_id,
                           metadata->>'old_teacher_id' as old_id
                    FROM staff_members
                    WHERE metadata->>'old_teacher_id' IS NOT NULL
                """)
                for row in new_cur.fetchall():
                    if row['old_id']:
                        self.id_mappings['staff'][int(row['old_id'])] = row['user_id']
                
                logger.info(f"  Loaded {len(self.id_mappings['staff'])} staff mappings")
                
                # Academic terms
                self.id_mappings['terms'] = {}
                new_cur.execute("SELECT id, academic_year, term_type FROM academic_terms ORDER BY start_date")
                terms = new_cur.fetchall()
                if terms:
                    self.default_term = terms[0]['id']
                    for term in terms:
                        # Simple mapping: semester_id from old DB to term UUID
                        # We'll use the first available term as default
                        self.id_mappings['terms'][110000135] = term['id']  # Fall term
                        self.id_mappings['terms'][110000136] = term['id']  # Spring term  
                logger.info(f"  Default term: {self.default_term}")
        
        logger.info("✓ Mapping build complete")
    
    def migrate_remaining_courses(self):
        """Migrate ALL remaining course offerings"""
        logger.info("=" * 80)
        logger.info("MIGRATING REMAINING COURSE OFFERINGS")
        logger.info("=" * 80)
        
        with self.old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with self.new_conn.cursor(cursor_factory=RealDictCursor) as new_cur:
                
                # Get all active courses from old DB
                old_cur.execute("""
                    SELECT 
                        c.id, c.code, c.education_plan_subject_id,
                        c.semester_id, c.student_count, c.education_lang_id,
                        c.create_date, c.update_date,
                        eps.subject_id
                    FROM course c
                    LEFT JOIN education_plan_subject eps 
                      ON c.education_plan_subject_id = eps.id
                    WHERE c.active = 1
                    ORDER BY c.id
                """)
                old_courses = old_cur.fetchall()
                
                logger.info(f"Found {len(old_courses)} courses in old database")
                
                # Check existing
                new_cur.execute("SELECT COUNT(*) as count FROM course_offerings")
                existing_count = new_cur.fetchone()['count']
                logger.info(f"Currently {existing_count} course offerings in new database")
                
                # Prepare data
                offering_values = []
                skipped_no_subject = 0
                skipped_exists = 0
                
                for course in old_courses:
                    # Check if already migrated
                    if course['id'] in self.id_mappings.get('course_offerings', {}):
                        skipped_exists += 1
                        continue
                    
                    # Get subject_id
                    subject_id = course.get('subject_id')
                    if not subject_id:
                        skipped_no_subject += 1
                        continue
                    
                    # Map to master course
                    course_uuid = self.id_mappings.get('courses', {}).get(subject_id)
                    if not course_uuid:
                        # Subject not migrated, skip for now
                        skipped_no_subject += 1
                        continue
                    
                    # Generate UUID for offering
                    offering_uuid = uuid.uuid4()
                    self.id_mappings.setdefault('course_offerings', {})[course['id']] = offering_uuid
                    
                    # Get academic term
                    semester_id = course.get('semester_id')
                    term_uuid = self.id_mappings.get('terms', {}).get(semester_id, self.default_term)
                    
                    # Extract section code
                    section_code = course.get('code', f"S{course['id'] % 10000:04d}")[-20:]
                    
                    # Language mapping
                    lang_map = {1: 'az', 2: 'en', 3: 'ru'}
                    lang = lang_map.get(course.get('education_lang_id'), 'az')
                    
                    # Metadata with old ID for tracking
                    metadata = json.dumps({'old_course_id': course['id']})
                    
                    offering_values.append((
                        offering_uuid,
                        course_uuid,
                        term_uuid,
                        section_code,
                        lang,
                        course.get('student_count') or 30,
                        0,  # current_enrollment
                        'in_person',
                        True,  # is_published
                        'open',
                        metadata,
                        course.get('create_date') or datetime.now(),
                        course.get('update_date') or datetime.now()
                    ))
                
                logger.info(f"Prepared {len(offering_values)} new course offerings")
                logger.info(f"Skipped {skipped_exists} already migrated")
                logger.info(f"Skipped {skipped_no_subject} without subject mapping")
                
                if offering_values:
                    # Insert in batches
                    batch_size = 1000
                    for i in range(0, len(offering_values), batch_size):
                        batch = offering_values[i:i+batch_size]
                        
                        insert_query = """
                            INSERT INTO course_offerings (
                                id, course_id, academic_term_id, section_code,
                                language_of_instruction, max_enrollment, current_enrollment,
                                delivery_mode, is_published, enrollment_status,
                                metadata, created_at, updated_at
                            ) VALUES %s
                            ON CONFLICT (course_id, academic_term_id, section_code) DO NOTHING
                        """
                        
                        execute_values(new_cur, insert_query, batch)
                        self.new_conn.commit()
                        logger.info(f"  Inserted batch {i//batch_size + 1}/{(len(offering_values)-1)//batch_size + 1}")
                    
                    logger.info(f"✓ Migrated {len(offering_values)} course offerings")
                else:
                    logger.info("No new course offerings to migrate")
    
    def migrate_enrollments(self):
        """Migrate ALL student enrollments from journal table"""
        logger.info("=" * 80)
        logger.info("MIGRATING ENROLLMENTS")
        logger.info("=" * 80)
        
        with self.old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with self.new_conn.cursor(cursor_factory=RealDictCursor) as new_cur:
                
                # Get all enrollments
                old_cur.execute("""
                    SELECT 
                        id, student_id, course_id, status,
                        final_grade, letter_grade, gpa_points,
                        create_date, update_date
                    FROM journal
                    ORDER BY id
                """)
                old_enrollments = old_cur.fetchall()
                
                logger.info(f"Found {len(old_enrollments)} enrollments in old database")
                
                # Check existing
                new_cur.execute("SELECT COUNT(*) as count FROM course_enrollments")
                existing_count = new_cur.fetchone()['count']
                logger.info(f"Currently {existing_count} enrollments in new database")
                
                # Prepare data
                enrollment_values = []
                skipped_no_student = 0
                skipped_no_offering = 0
                
                # Build reverse mapping for checking duplicates
                new_cur.execute("""
                    SELECT metadata->>'old_journal_id' as old_id
                    FROM course_enrollments
                    WHERE metadata->>'old_journal_id' IS NOT NULL
                """)
                migrated_journal_ids = {int(row['old_id']) for row in new_cur.fetchall() if row['old_id']}
                
                for enrollment in old_enrollments:
                    # Check if already migrated
                    if enrollment['id'] in migrated_journal_ids:
                        continue
                    
                    # Map student
                    student_uuid = self.id_mappings.get('students', {}).get(enrollment['student_id'])
                    if not student_uuid:
                        skipped_no_student += 1
                        continue
                    
                    # Map course offering
                    offering_uuid = self.id_mappings.get('course_offerings', {}).get(enrollment['course_id'])
                    if not offering_uuid:
                        skipped_no_offering += 1
                        continue
                    
                    # Generate UUID
                    enrollment_uuid = uuid.uuid4()
                    
                    # Status mapping
                    status_map = {1: 'enrolled', 2: 'completed', 3: 'dropped'}
                    status = status_map.get(enrollment.get('status'), 'enrolled')
                    
                    # Metadata
                    metadata = json.dumps({'old_journal_id': enrollment['id']})
                    
                    enrollment_values.append((
                        enrollment_uuid,
                        offering_uuid,
                        student_uuid,
                        enrollment.get('create_date') or datetime.now(),
                        status,
                        enrollment.get('letter_grade'),
                        enrollment.get('gpa_points'),
                        metadata,
                        enrollment.get('create_date') or datetime.now(),
                        enrollment.get('update_date') or datetime.now()
                    ))
                
                logger.info(f"Prepared {len(enrollment_values)} new enrollments")
                logger.info(f"Skipped {skipped_no_student} without student mapping")
                logger.info(f"Skipped {skipped_no_offering} without course offering mapping")
                
                if enrollment_values:
                    # Insert in batches
                    batch_size = 5000
                    for i in range(0, len(enrollment_values), batch_size):
                        batch = enrollment_values[i:i+batch_size]
                        
                        insert_query = """
                            INSERT INTO course_enrollments (
                                id, course_offering_id, student_id, enrollment_date,
                                enrollment_status, grade, grade_points, metadata,
                                created_at, updated_at
                            ) VALUES %s
                            ON CONFLICT (course_offering_id, student_id) DO NOTHING
                        """
                        
                        execute_values(new_cur, insert_query, batch)
                        self.new_conn.commit()
                        logger.info(f"  Inserted batch {i//batch_size + 1}/{(len(enrollment_values)-1)//batch_size + 1}")
                    
                    logger.info(f"✓ Migrated {len(enrollment_values)} enrollments")
                else:
                    logger.info("No new enrollments to migrate")
    
    def run_complete_migration(self):
        """Execute complete migration in proper order"""
        try:
            logger.info("STARTING COMPLETE MIGRATION")
            logger.info("=" * 80)
            
            # Step 1: Build mappings from existing data
            self.build_existing_mappings()
            
            # Step 2: Migrate remaining course offerings
            self.migrate_remaining_courses()
            
            # Step 3: Migrate enrollments
            self.migrate_enrollments()
            
            logger.info("=" * 80)
            logger.info("MIGRATION COMPLETE")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            raise
        finally:
            self.close()


if __name__ == "__main__":
    migration = CompleteMigration()
    migration.run_complete_migration()
