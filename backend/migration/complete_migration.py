#!/usr/bin/env python3
"""
Complete Database Migration Script
Migrates remaining data from edu (old) to lms (new) database
Uses actual schema columns: old_course_id, old_journal_id, metadata, etc.
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.extensions import register_adapter, AsIs
import uuid
import logging
from datetime import datetime
import sys

# Register UUID adapter for psycopg2
def adapt_uuid(val):
    return AsIs(f"'{val}'::uuid")

register_adapter(uuid.UUID, adapt_uuid)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
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
        self.stats = {
            'course_offerings': {'attempted': 0, 'migrated': 0, 'skipped': 0},
            'enrollments': {'attempted': 0, 'migrated': 0, 'skipped': 0},
            'grades': {'attempted': 0, 'migrated': 0, 'skipped': 0},
        }
        
    def close(self):
        if self.old_conn:
            self.old_conn.close()
        if self.new_conn:
            self.new_conn.close()
    
    def build_existing_mappings(self):
        """Build ID mappings from existing migrated data"""
        logger.info("Building existing ID mappings...")
        
        with self.old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with self.new_conn.cursor(
                cursor_factory=RealDictCursor
            ) as new_cur:
                
                # 1. Students mapping (use metadata jsonb)
                self.id_mappings['students'] = {}
                new_cur.execute("""
                    SELECT id, metadata->>'old_student_id' as old_id
                    FROM students
                    WHERE metadata->>'old_student_id' IS NOT NULL
                """)
                for row in new_cur.fetchall():
                    if row['old_id']:
                        old_id = int(row['old_id'])
                        self.id_mappings['students'][old_id] = row['id']
                
                logger.info(
                    f"  Loaded {len(self.id_mappings['students'])} "
                    f"student mappings"
                )
                
                # 2. Courses mapping (subjects → courses)
                self.id_mappings['courses'] = {}
                new_cur.execute("SELECT id, code FROM courses")
                courses_by_code = {
                    row['code']: row['id'] for row in new_cur.fetchall()
                }
                
                old_cur.execute(
                    "SELECT id FROM subject_catalog WHERE active = 1"
                )
                for row in old_cur.fetchall():
                    subject_id = row['id']
                    course_code = f"SUBJ{subject_id % 100000:05d}"
                    if course_code in courses_by_code:
                        self.id_mappings['courses'][subject_id] = (
                            courses_by_code[course_code]
                        )
                
                logger.info(
                    f"  Loaded {len(self.id_mappings['courses'])} "
                    f"course mappings"
                )
                
                # 3. Course offerings mapping (use old_course_id column)
                self.id_mappings['course_offerings'] = {}
                new_cur.execute("""
                    SELECT id, old_course_id
                    FROM course_offerings
                    WHERE old_course_id IS NOT NULL
                """)
                for row in new_cur.fetchall():
                    if row['old_course_id']:
                        self.id_mappings['course_offerings'][
                            row['old_course_id']
                        ] = row['id']
                
                logger.info(
                    f"  Loaded {len(self.id_mappings['course_offerings'])} "
                    f"course offering mappings"
                )
                
                # 4. Enrollment mappings (use old_journal_id)
                self.id_mappings['enrollments'] = {}
                new_cur.execute("""
                    SELECT id, old_journal_id
                    FROM course_enrollments
                    WHERE old_journal_id IS NOT NULL
                """)
                for row in new_cur.fetchall():
                    if row['old_journal_id']:
                        self.id_mappings['enrollments'][
                            row['old_journal_id']
                        ] = row['id']
                
                logger.info(
                    f"  Loaded {len(self.id_mappings['enrollments'])} "
                    f"enrollment mappings"
                )
                
                # 5. Get default academic term
                new_cur.execute("""
                    SELECT id FROM academic_terms
                    ORDER BY start_date LIMIT 1
                """)
                result = new_cur.fetchone()
                if result:
                    self.default_term = result['id']
                    logger.info(f"  Default term: {self.default_term}")
                else:
                    raise Exception("No academic terms found in new database!")
        
        logger.info("✓ Mapping build complete\n")
    
    def migrate_remaining_courses(self):
        """Migrate ALL remaining course offerings"""
        logger.info("=" * 80)
        logger.info("PHASE 4: MIGRATING REMAINING COURSE OFFERINGS")
        logger.info("=" * 80)
        
        with self.old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with self.new_conn.cursor(
                cursor_factory=RealDictCursor
            ) as new_cur:
                
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
                
                logger.info(
                    f"Found {len(old_courses)} courses in old database"
                )
                
                # Check existing
                new_cur.execute(
                    "SELECT COUNT(*) as count FROM course_offerings"
                )
                existing_count = new_cur.fetchone()['count']
                logger.info(
                    f"Currently {existing_count} course offerings "
                    f"in new database"
                )
                
                # Prepare data
                offering_values = []
                skipped_no_subject = 0
                skipped_exists = 0
                skipped_no_course_mapping = 0
                
                for course in old_courses:
                    self.stats['course_offerings']['attempted'] += 1
                    
                    # Check if already migrated
                    if course['id'] in self.id_mappings.get(
                        'course_offerings', {}
                    ):
                        skipped_exists += 1
                        self.stats['course_offerings']['skipped'] += 1
                        continue
                    
                    # Get subject_id
                    subject_id = course.get('subject_id')
                    if not subject_id:
                        skipped_no_subject += 1
                        self.stats['course_offerings']['skipped'] += 1
                        continue
                    
                    # Map to master course
                    course_uuid = self.id_mappings.get(
                        'courses', {}
                    ).get(subject_id)
                    if not course_uuid:
                        skipped_no_course_mapping += 1
                        self.stats['course_offerings']['skipped'] += 1
                        continue
                    
                    # Generate UUID for offering
                    offering_uuid = uuid.uuid4()
                    self.id_mappings.setdefault(
                        'course_offerings', {}
                    )[course['id']] = offering_uuid
                    
                    # Get academic term
                    term_uuid = self.default_term
                    
                    # Extract section code
                    code_str = course.get('code', f"S{course['id'] % 10000:04d}")
                    section_code = code_str[-20:] if code_str else f"S{course['id'] % 10000:04d}"
                    
                    # Language mapping
                    lang_map = {1: 'az', 2: 'en', 3: 'ru'}
                    lang = lang_map.get(
                        course.get('education_lang_id'), 'az'
                    )
                    
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
                        course['id'],  # old_course_id
                        course.get('create_date') or datetime.now(),
                        course.get('update_date') or datetime.now()
                    ))
                
                logger.info(
                    f"Prepared {len(offering_values)} new course offerings"
                )
                logger.info(f"Skipped {skipped_exists} already migrated")
                logger.info(f"Skipped {skipped_no_subject} without subject_id")
                logger.info(
                    f"Skipped {skipped_no_course_mapping} "
                    f"without course mapping"
                )
                
                if offering_values:
                    # Insert in batches
                    batch_size = 1000
                    total_inserted = 0
                    
                    for i in range(0, len(offering_values), batch_size):
                        batch = offering_values[i:i+batch_size]
                        
                        insert_query = """
                            INSERT INTO course_offerings (
                                id, course_id, academic_term_id, section_code,
                                language_of_instruction, max_enrollment,
                                current_enrollment, delivery_mode, is_published,
                                enrollment_status, old_course_id,
                                created_at, updated_at
                            ) VALUES %s
                            ON CONFLICT (course_id, academic_term_id, section_code)
                            DO NOTHING
                        """
                        
                        execute_values(new_cur, insert_query, batch)
                        self.new_conn.commit()
                        
                        # Get actual inserted count
                        batch_num = i//batch_size + 1
                        total_batches = (len(offering_values)-1)//batch_size + 1
                        logger.info(f"  Inserted batch {batch_num}/{total_batches}")
                    
                    self.stats['course_offerings']['migrated'] = len(offering_values)
                    logger.info(f"✓ Migrated {len(offering_values)} course offerings\n")
                    
                    # Reload mappings after insertion
                    logger.info("Reloading course offering mappings...")
                    new_cur.execute("""
                        SELECT id, old_course_id
                        FROM course_offerings
                        WHERE old_course_id IS NOT NULL
                    """)
                    self.id_mappings['course_offerings'] = {}
                    for row in new_cur.fetchall():
                        if row['old_course_id']:
                            self.id_mappings['course_offerings'][
                                row['old_course_id']
                            ] = row['id']
                    logger.info(
                        f"  Reloaded {len(self.id_mappings['course_offerings'])} "
                        f"course offering mappings\n"
                    )
                else:
                    logger.info("No new course offerings to migrate\n")
    
    def migrate_enrollments(self):
        """Migrate ALL student enrollments from journal table"""
        logger.info("=" * 80)
        logger.info("PHASE 5A: MIGRATING ENROLLMENTS")
        logger.info("=" * 80)
        
        with self.old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with self.new_conn.cursor(
                cursor_factory=RealDictCursor
            ) as new_cur:
                
                # Get all enrollments
                old_cur.execute("""
                    SELECT
                        id, student_id, course_id, active,
                        point, point_id,
                        create_date, update_date
                    FROM journal
                    WHERE active = 1
                    ORDER BY id
                """)
                old_enrollments = old_cur.fetchall()
                
                logger.info(
                    f"Found {len(old_enrollments)} enrollments in old database"
                )
                
                # Check existing
                new_cur.execute(
                    "SELECT COUNT(*) as count FROM course_enrollments"
                )
                existing_count = new_cur.fetchone()['count']
                logger.info(
                    f"Currently {existing_count} enrollments in new database"
                )
                
                # Prepare data
                enrollment_values = []
                skipped_no_student = 0
                skipped_no_offering = 0
                skipped_exists = 0
                
                for enrollment in old_enrollments:
                    self.stats['enrollments']['attempted'] += 1
                    
                    # Check if already migrated
                    if enrollment['id'] in self.id_mappings.get(
                        'enrollments', {}
                    ):
                        skipped_exists += 1
                        self.stats['enrollments']['skipped'] += 1
                        continue
                    
                    # Map student
                    student_uuid = self.id_mappings.get(
                        'students', {}
                    ).get(enrollment['student_id'])
                    if not student_uuid:
                        skipped_no_student += 1
                        self.stats['enrollments']['skipped'] += 1
                        continue
                    
                    # Map course offering
                    offering_uuid = self.id_mappings.get(
                        'course_offerings', {}
                    ).get(enrollment['course_id'])
                    if not offering_uuid:
                        skipped_no_offering += 1
                        self.stats['enrollments']['skipped'] += 1
                        continue
                    
                    # Generate UUID
                    enrollment_uuid = uuid.uuid4()
                    self.id_mappings.setdefault(
                        'enrollments', {}
                    )[enrollment['id']] = enrollment_uuid
                    
                    # Status mapping - use active field
                    status = 'enrolled' if enrollment.get('active') == 1 else 'completed'
                    
                    # Extract grade if available
                    grade_letter = enrollment.get('point')
                    grade_points = None
                    
                    enrollment_values.append((
                        enrollment_uuid,
                        offering_uuid,
                        student_uuid,
                        enrollment.get('create_date') or datetime.now(),
                        status,
                        grade_letter,
                        grade_points,
                        enrollment['id'],  # old_journal_id
                        enrollment.get('create_date') or datetime.now(),
                        enrollment.get('update_date') or datetime.now()
                    ))
                
                logger.info(
                    f"Prepared {len(enrollment_values)} new enrollments"
                )
                logger.info(f"Skipped {skipped_exists} already migrated")
                logger.info(
                    f"Skipped {skipped_no_student} without student mapping"
                )
                logger.info(
                    f"Skipped {skipped_no_offering} "
                    f"without course offering mapping"
                )
                
                if enrollment_values:
                    # Insert in batches
                    batch_size = 5000
                    
                    for i in range(0, len(enrollment_values), batch_size):
                        batch = enrollment_values[i:i+batch_size]
                        
                        insert_query = """
                            INSERT INTO course_enrollments (
                                id, course_offering_id, student_id,
                                enrollment_date, enrollment_status, grade,
                                grade_points, old_journal_id,
                                created_at, updated_at
                            ) VALUES %s
                            ON CONFLICT (course_offering_id, student_id)
                            WHERE enrollment_status = 'enrolled'
                            DO NOTHING
                        """
                        
                        execute_values(new_cur, insert_query, batch)
                        self.new_conn.commit()
                        
                        batch_num = i//batch_size + 1
                        total_batches = (len(enrollment_values)-1)//batch_size + 1
                        logger.info(f"  Inserted batch {batch_num}/{total_batches}")
                    
                    self.stats['enrollments']['migrated'] = len(enrollment_values)
                    logger.info(f"✓ Migrated {len(enrollment_values)} enrollments\n")
                else:
                    logger.info("No new enrollments to migrate\n")
    
    def migrate_grades(self):
        """Migrate grades from journal_details table"""
        logger.info("=" * 80)
        logger.info("PHASE 5B: MIGRATING GRADES")
        logger.info("=" * 80)
        
        with self.old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with self.new_conn.cursor(
                cursor_factory=RealDictCursor
            ) as new_cur:
                
                # Count total grades
                old_cur.execute("SELECT COUNT(*) as count FROM journal_details")
                total_grades = old_cur.fetchone()['count']
                logger.info(f"Found {total_grades:,} grades in old database")
                
                # Check existing
                new_cur.execute("SELECT COUNT(*) as count FROM grades")
                existing_count = new_cur.fetchone()['count']
                logger.info(
                    f"Currently {existing_count:,} grades in new database"
                )
                
                # Process in batches
                batch_size = 50000
                offset = 0
                total_migrated = 0
                total_skipped = 0
                
                while True:
                    # Fetch batch of grades
                    old_cur.execute(f"""
                        SELECT
                            id, journal_id, course_meeting_id,
                            point_id_1, status_1, note_1,
                            point_id_2, status_2, note_2,
                            point_id_3, status_3, note_3,
                            create_date, update_date, active
                        FROM journal_details
                        WHERE active = 1
                        ORDER BY id
                        LIMIT {batch_size} OFFSET {offset}
                    """)
                    grades_batch = old_cur.fetchall()
                    
                    if not grades_batch:
                        break
                    
                    grade_values = []
                    skipped_no_enrollment = 0
                    
                    for grade in grades_batch:
                        self.stats['grades']['attempted'] += 1
                        
                        # Map enrollment
                        enrollment_uuid = self.id_mappings.get(
                            'enrollments', {}
                        ).get(grade['journal_id'])
                        if not enrollment_uuid:
                            skipped_no_enrollment += 1
                            self.stats['grades']['skipped'] += 1
                            continue
                        
                        # Extract point grades (up to 3 grades per detail record)
                        points = [
                            (grade.get('point_id_1'), grade.get('status_1')),
                            (grade.get('point_id_2'), grade.get('status_2')),
                            (grade.get('point_id_3'), grade.get('status_3'))
                        ]
                        
                        for idx, (point_id, status) in enumerate(points):
                            if point_id:
                                # Generate UUID for each grade
                                grade_uuid = uuid.uuid4()
                                
                                grade_values.append((
                                    grade_uuid,
                                    enrollment_uuid,
                                    None,  # assessment_id (NULL for now)
                                    point_id,  # score (point_id represents the score)
                                    100,  # max_score (default)
                                    None,  # weight
                                    grade.get('create_date') or datetime.now(),
                                    None,  # graded_by
                                    datetime.now(),  # created_at
                                    datetime.now()   # updated_at
                                ))
                    
                    if grade_values:
                        insert_query = """
                            INSERT INTO grades (
                                id, enrollment_id, assessment_id, score,
                                max_score, weight, graded_date, graded_by,
                                created_at, updated_at
                            ) VALUES %s
                            ON CONFLICT DO NOTHING
                        """
                        
                        execute_values(new_cur, insert_query, grade_values)
                        self.new_conn.commit()
                        
                        total_migrated += len(grade_values)
                        total_skipped += skipped_no_enrollment
                        
                        logger.info(
                            f"  Processed offset {offset:,} - "
                            f"Migrated {len(grade_values):,}, "
                            f"Skipped {skipped_no_enrollment:,}"
                        )
                    
                    offset += batch_size
                
                self.stats['grades']['migrated'] = total_migrated
                logger.info(f"✓ Migrated {total_migrated:,} grades")
                logger.info(f"  Skipped {total_skipped:,} without enrollment mapping\n")
    
    def print_final_stats(self):
        """Print final migration statistics"""
        logger.info("=" * 80)
        logger.info("MIGRATION STATISTICS")
        logger.info("=" * 80)
        
        for category, stats in self.stats.items():
            logger.info(f"\n{category.upper().replace('_', ' ')}:")
            logger.info(f"  Attempted: {stats['attempted']:,}")
            logger.info(f"  Migrated:  {stats['migrated']:,}")
            logger.info(f"  Skipped:   {stats['skipped']:,}")
        
        logger.info("\n" + "=" * 80)
    
    def run_complete_migration(self):
        """Execute complete migration in proper order"""
        try:
            logger.info("STARTING COMPLETE MIGRATION")
            logger.info("=" * 80 + "\n")
            
            # Step 1: Build mappings from existing data
            self.build_existing_mappings()
            
            # Step 2: Migrate remaining course offerings
            self.migrate_remaining_courses()
            
            # Step 3: Migrate enrollments
            self.migrate_enrollments()
            
            # Step 4: Migrate grades
            self.migrate_grades()
            
            # Print final statistics
            self.print_final_stats()
            
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
