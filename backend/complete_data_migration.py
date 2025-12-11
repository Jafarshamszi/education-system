#!/usr/bin/env python3
"""
Complete Data Migration Script
===============================
Migrates missing data from old 'edu' database to new 'lms' database:
- 4,439 missing courses (73.7%)
- 415,711 missing enrollments (81.5%)

Prerequisites:
1. Run complete_migration_plan.sql first to add tracking columns
2. Ensure both databases are accessible
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from datetime import datetime
import sys
from typing import Dict, List, Tuple
import uuid

# Database configurations
OLD_DB_CONFIG = {
    'dbname': 'edu',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': 5432
}

NEW_DB_CONFIG = {
    'dbname': 'lms',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': 5432
}

class DataMigrator:
    def __init__(self):
        self.old_conn = None
        self.new_conn = None
        self.old_cur = None
        self.new_cur = None
        
        # Statistics
        self.stats = {
            'courses_migrated': 0,
            'courses_skipped': 0,
            'courses_failed': 0,
            'enrollments_migrated': 0,
            'enrollments_skipped': 0,
            'enrollments_failed': 0,
        }
        
        # Mapping caches
        self.student_id_map = {}  # old_student_id -> new_student_uuid
        self.course_id_map = {}   # old_course_id -> new_offering_uuid
        self.term_id_map = {}     # old_semester_id -> new_term_uuid
        
    def connect(self):
        """Establish database connections"""
        print("Connecting to databases...")
        try:
            self.old_conn = psycopg2.connect(**OLD_DB_CONFIG, cursor_factory=RealDictCursor)
            self.new_conn = psycopg2.connect(**NEW_DB_CONFIG, cursor_factory=RealDictCursor)
            self.old_cur = self.old_conn.cursor()
            self.new_cur = self.new_conn.cursor()
            print("✅ Connected to both databases")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            sys.exit(1)
    
    def disconnect(self):
        """Close database connections"""
        if self.old_cur:
            self.old_cur.close()
        if self.new_cur:
            self.new_cur.close()
        if self.old_conn:
            self.old_conn.close()
        if self.new_conn:
            self.new_conn.close()
        print("Database connections closed")
    
    def load_student_mapping(self):
        """Load mapping of old student IDs to new UUIDs"""
        print("\nLoading student ID mappings...")
        
        # Try metadata mapping first (if students have metadata->>'old_student_id')
        self.new_cur.execute("""
            SELECT id, metadata->>'old_student_id' as old_id, student_number
            FROM students
            WHERE metadata->>'old_student_id' IS NOT NULL
        """)
        
        for row in self.new_cur.fetchall():
            old_id = int(row['old_id'])
            self.student_id_map[old_id] = row['id']
        
        print(f"✅ Loaded {len(self.student_id_map):,} student mappings")
    
    def load_existing_course_mappings(self):
        """Load already migrated courses"""
        print("\nLoading existing course mappings...")
        
        self.new_cur.execute("""
            SELECT id, old_course_id
            FROM course_offerings
            WHERE old_course_id IS NOT NULL
        """)
        
        for row in self.new_cur.fetchall():
            self.course_id_map[row['old_course_id']] = row['id']
        
        print(f"✅ Loaded {len(self.course_id_map):,} existing course mappings")
    
    def get_or_create_academic_term(self, semester_id: int, year_id: int) -> uuid.UUID:
        """Get or create academic term based on semester and year"""
        # Check cache first
        cache_key = f"{semester_id}_{year_id}"
        if cache_key in self.term_id_map:
            return self.term_id_map[cache_key]
        
        # Try to find existing term
        # For now, use a default term - you'll need to map semester/year to actual terms
        self.new_cur.execute("""
            SELECT id FROM academic_terms
            WHERE is_active = TRUE
            ORDER BY start_date DESC
            LIMIT 1
        """)
        
        result = self.new_cur.fetchone()
        if result:
            term_id = result['id']
            self.term_id_map[cache_key] = term_id
            return term_id
        
        # If no term exists, create a default one
        term_id = uuid.uuid4()
        self.new_cur.execute("""
            INSERT INTO academic_terms (
                id, term_name, term_code, start_date, end_date, 
                is_active, created_at, updated_at
            ) VALUES (
                %s, 'Default Term', 'DEFAULT', '2024-01-01', '2024-12-31',
                TRUE, NOW(), NOW()
            )
            ON CONFLICT (id) DO NOTHING
            RETURNING id
        """, (term_id,))
        
        self.term_id_map[cache_key] = term_id
        return term_id
    
    def migrate_courses(self, batch_size: int = 100):
        """Migrate missing courses from old to new database"""
        print("\n" + "="*80)
        print("MIGRATING COURSES")
        print("="*80)
        
        # Get courses that haven't been migrated yet
        self.old_cur.execute("""
            SELECT 
                c.id,
                c.code,
                c.education_plan_subject_id,
                c.semester_id,
                c.education_year_id,
                c.education_lang_id,
                c.education_type_id,
                c.m_hours,
                c.s_hours,
                c.l_hours,
                c.fm_hours,
                c.student_count,
                c.create_date,
                c.update_date
            FROM course c
            WHERE c.active = 1
            AND c.id NOT IN (
                SELECT old_course_id 
                FROM dblink('dbname=lms user=postgres password=1111 host=localhost',
                            'SELECT old_course_id FROM course_offerings WHERE old_course_id IS NOT NULL')
                AS t(old_course_id BIGINT)
            )
            ORDER BY c.id
        """)
        
        courses_to_migrate = self.old_cur.fetchall()
        total = len(courses_to_migrate)
        
        if total == 0:
            print("✅ No courses to migrate (all up to date)")
            return
        
        print(f"Found {total:,} courses to migrate")
        
        # Get a default course_id and term_id for migration
        # You'll need to implement proper mapping logic here
        self.new_cur.execute("SELECT id FROM courses LIMIT 1")
        default_course = self.new_cur.fetchone()
        if not default_course:
            print("❌ No courses exist in new database - cannot migrate offerings")
            return
        
        default_course_id = default_course['id']
        
        batch = []
        for i, course in enumerate(courses_to_migrate, 1):
            try:
                # Get or create academic term
                term_id = self.get_or_create_academic_term(
                    course['semester_id'], 
                    course['education_year_id']
                )
                
                # Create UUID for new offering
                offering_id = uuid.uuid4()
                
                # Prepare offering data
                offering = {
                    'id': offering_id,
                    'course_id': default_course_id,  # TODO: Map properly
                    'academic_term_id': term_id,
                    'section_code': course['code'] or f"MIGRATED_{course['id']}",
                    'max_enrollment': course['student_count'] or 50,
                    'current_enrollment': 0,  # Will be updated when enrollments are migrated
                    'delivery_mode': 'in_person',
                    'is_published': True,
                    'enrollment_status': 'open',
                    'old_course_id': course['id'],
                    'created_at': course['create_date'] or datetime.now(),
                    'updated_at': course['update_date'] or datetime.now()
                }
                
                batch.append(offering)
                
                # Cache mapping
                self.course_id_map[course['id']] = offering_id
                
                if len(batch) >= batch_size:
                    self._insert_course_batch(batch)
                    batch = []
                
                if i % 100 == 0:
                    print(f"Progress: {i:,}/{total:,} courses ({i/total*100:.1f}%)")
                    
            except Exception as e:
                print(f"❌ Error migrating course {course['id']}: {e}")
                self.stats['courses_failed'] += 1
        
        # Insert remaining batch
        if batch:
            self._insert_course_batch(batch)
        
        print(f"\n✅ Courses migrated: {self.stats['courses_migrated']:,}")
        print(f"⚠️  Courses failed: {self.stats['courses_failed']:,}")
    
    def _insert_course_batch(self, batch: List[Dict]):
        """Insert a batch of course offerings"""
        try:
            execute_batch(
                self.new_cur,
                """
                INSERT INTO course_offerings (
                    id, course_id, academic_term_id, section_code,
                    max_enrollment, current_enrollment, delivery_mode,
                    is_published, enrollment_status, old_course_id,
                    created_at, updated_at
                ) VALUES (
                    %(id)s, %(course_id)s, %(academic_term_id)s, %(section_code)s,
                    %(max_enrollment)s, %(current_enrollment)s, %(delivery_mode)s,
                    %(is_published)s, %(enrollment_status)s, %(old_course_id)s,
                    %(created_at)s, %(updated_at)s
                )
                ON CONFLICT (id) DO NOTHING
                """,
                batch
            )
            self.new_conn.commit()
            self.stats['courses_migrated'] += len(batch)
        except Exception as e:
            self.new_conn.rollback()
            print(f"❌ Batch insert failed: {e}")
            self.stats['courses_failed'] += len(batch)
    
    def migrate_enrollments(self, batch_size: int = 1000):
        """Migrate missing enrollments from old to new database"""
        print("\n" + "="*80)
        print("MIGRATING ENROLLMENTS")
        print("="*80)
        
        # Count total enrollments to migrate
        self.old_cur.execute("""
            SELECT COUNT(*) as total
            FROM journal
            WHERE active = 1
        """)
        total = self.old_cur.fetchone()['total']
        
        print(f"Processing {total:,} journal records...")
        
        # Process in batches
        offset = 0
        batch_num = 0
        
        while True:
            # Fetch batch
            self.old_cur.execute("""
                SELECT 
                    j.id,
                    j.course_id,
                    j.student_id,
                    j.point,
                    j.create_date,
                    j.update_date
                FROM journal j
                WHERE j.active = 1
                ORDER BY j.id
                LIMIT %s OFFSET %s
            """, (batch_size, offset))
            
            enrollments = self.old_cur.fetchall()
            
            if not enrollments:
                break
            
            batch_num += 1
            print(f"\nProcessing batch {batch_num} (records {offset+1:,}-{offset+len(enrollments):,})")
            
            enrollment_batch = []
            
            for enr in enrollments:
                try:
                    # Get student mapping
                    if enr['student_id'] not in self.student_id_map:
                        self.stats['enrollments_skipped'] += 1
                        continue
                    
                    student_uuid = self.student_id_map[enr['student_id']]
                    
                    # Get course offering mapping
                    if enr['course_id'] not in self.course_id_map:
                        self.stats['enrollments_skipped'] += 1
                        continue
                    
                    offering_uuid = self.course_id_map[enr['course_id']]
                    
                    # Check if already migrated
                    self.new_cur.execute("""
                        SELECT 1 FROM course_enrollments
                        WHERE old_journal_id = %s
                        LIMIT 1
                    """, (enr['id'],))
                    
                    if self.new_cur.fetchone():
                        self.stats['enrollments_skipped'] += 1
                        continue
                    
                    # Create enrollment record
                    enrollment_data = {
                        'id': uuid.uuid4(),
                        'course_offering_id': offering_uuid,
                        'student_id': student_uuid,
                        'enrollment_date': enr['create_date'] or datetime.now(),
                        'enrollment_status': 'enrolled',
                        'grade': enr['point'],
                        'old_journal_id': enr['id'],
                        'created_at': enr['create_date'] or datetime.now(),
                        'updated_at': enr['update_date'] or datetime.now()
                    }
                    
                    enrollment_batch.append(enrollment_data)
                    
                except Exception as e:
                    print(f"❌ Error processing enrollment {enr['id']}: {e}")
                    self.stats['enrollments_failed'] += 1
            
            # Insert batch
            if enrollment_batch:
                self._insert_enrollment_batch(enrollment_batch)
            
            offset += batch_size
            
            print(f"Batch progress: {self.stats['enrollments_migrated']:,} migrated, "
                  f"{self.stats['enrollments_skipped']:,} skipped, "
                  f"{self.stats['enrollments_failed']:,} failed")
        
        print(f"\n✅ Enrollments migrated: {self.stats['enrollments_migrated']:,}")
        print(f"⚠️  Enrollments skipped: {self.stats['enrollments_skipped']:,}")
        print(f"❌ Enrollments failed: {self.stats['enrollments_failed']:,}")
    
    def _insert_enrollment_batch(self, batch: List[Dict]):
        """Insert a batch of enrollments"""
        try:
            execute_batch(
                self.new_cur,
                """
                INSERT INTO course_enrollments (
                    id, course_offering_id, student_id, enrollment_date,
                    enrollment_status, grade, old_journal_id,
                    created_at, updated_at
                ) VALUES (
                    %(id)s, %(course_offering_id)s, %(student_id)s, %(enrollment_date)s,
                    %(enrollment_status)s, %(grade)s, %(old_journal_id)s,
                    %(created_at)s, %(updated_at)s
                )
                ON CONFLICT (id) DO NOTHING
                """,
                batch
            )
            self.new_conn.commit()
            self.stats['enrollments_migrated'] += len(batch)
        except Exception as e:
            self.new_conn.rollback()
            print(f"❌ Enrollment batch insert failed: {e}")
            self.stats['enrollments_failed'] += len(batch)
    
    def update_enrollment_counts(self):
        """Update current_enrollment counts in course_offerings"""
        print("\n" + "="*80)
        print("UPDATING ENROLLMENT COUNTS")
        print("="*80)
        
        self.new_cur.execute("""
            UPDATE course_offerings co
            SET current_enrollment = (
                SELECT COUNT(*)
                FROM course_enrollments ce
                WHERE ce.course_offering_id = co.id
                AND ce.enrollment_status = 'enrolled'
            ),
            updated_at = NOW()
        """)
        
        self.new_conn.commit()
        print("✅ Enrollment counts updated")
    
    def print_final_report(self):
        """Print final migration statistics"""
        print("\n" + "="*80)
        print("MIGRATION COMPLETE - FINAL REPORT")
        print("="*80)
        
        # Get final counts
        self.new_cur.execute("SELECT COUNT(*) FROM course_offerings")
        total_offerings = self.new_cur.fetchone()['count']
        
        self.new_cur.execute("SELECT COUNT(*) FROM course_offerings WHERE old_course_id IS NOT NULL")
        migrated_offerings = self.new_cur.fetchone()['count']
        
        self.new_cur.execute("SELECT COUNT(*) FROM course_enrollments")
        total_enrollments = self.new_cur.fetchone()['count']
        
        self.new_cur.execute("SELECT COUNT(*) FROM course_enrollments WHERE old_journal_id IS NOT NULL")
        migrated_enrollments = self.new_cur.fetchone()['count']
        
        print(f"\n📊 COURSES:")
        print(f"  Total in new DB: {total_offerings:,}")
        print(f"  Migrated from old DB: {migrated_offerings:,}")
        print(f"  Migration coverage: {migrated_offerings/total_offerings*100:.1f}%")
        
        print(f"\n📊 ENROLLMENTS:")
        print(f"  Total in new DB: {total_enrollments:,}")
        print(f"  Migrated from old DB: {migrated_enrollments:,}")
        print(f"  Migration coverage: {migrated_enrollments/total_enrollments*100:.1f}%")
        
        print(f"\n📈 THIS RUN:")
        print(f"  Courses migrated: {self.stats['courses_migrated']:,}")
        print(f"  Courses failed: {self.stats['courses_failed']:,}")
        print(f"  Enrollments migrated: {self.stats['enrollments_migrated']:,}")
        print(f"  Enrollments skipped: {self.stats['enrollments_skipped']:,}")
        print(f"  Enrollments failed: {self.stats['enrollments_failed']:,}")

def main():
    """Main migration execution"""
    print("="*80)
    print("COMPLETE DATA MIGRATION")
    print("="*80)
    print(f"Started at: {datetime.now()}")
    
    migrator = DataMigrator()
    
    try:
        migrator.connect()
        migrator.load_student_mapping()
        migrator.load_existing_course_mappings()
        
        # Migrate courses first
        migrator.migrate_courses()
        
        # Then migrate enrollments
        migrator.migrate_enrollments()
        
        # Update enrollment counts
        migrator.update_enrollment_counts()
        
        # Print final report
        migrator.print_final_report()
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        migrator.disconnect()
    
    print(f"\nCompleted at: {datetime.now()}")

if __name__ == "__main__":
    main()
