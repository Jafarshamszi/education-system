#!/usr/bin/env python3
"""
Education System Database Migration Script
==========================================
Migrates data from old database (edu) to new database (edu_v2)

Author: Database Migration Team
Date: October 3, 2025
Version: 1.0

Prerequisites:
- PostgreSQL 15+
- Python 3.10+
- psycopg2-binary
- uuid library

Usage:
    python migrate_database.py --phase all
    python migrate_database.py --phase 1  # Users and persons only
    python migrate_database.py --phase 2  # Students and teachers
    python migrate_database.py --phase 3  # Organizations and programs
    python migrate_database.py --phase 4  # Courses and offerings
    python migrate_database.py --phase 5  # Enrollments and grades
    python migrate_database.py --validate  # Run validation queries
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.extensions import register_adapter, AsIs
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any
import argparse
import sys
import base64

# Register UUID adapter for psycopg2
def adapt_uuid(val):
    return AsIs(f"'{val}'::uuid")

register_adapter(uuid.UUID, adapt_uuid)


def decode_base64_password(encoded_password):
    """Decode base64 encoded password from old database"""
    if not encoded_password:
        return 'placeholder_hash'
    try:
        # Decode base64 password
        decoded = base64.b64decode(encoded_password).decode('utf-8')
        return decoded
    except Exception as e:
        logger.warning(f"Failed to decode password: {e}, using as-is")
        return encoded_password


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Database connection configurations
OLD_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'edu',
    'user': 'postgres',
    'password': '1111'
}

NEW_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'lms',
    'user': 'postgres',
    'password': '1111'
}

class DatabaseMigration:
    """Handles complete database migration from old to new schema"""
    
    def __init__(self):
        self.old_conn = None
        self.new_conn = None
        self.id_mappings = {}
        self.stats = {
            'users': {'total': 0, 'migrated': 0, 'failed': 0},
            'persons': {'total': 0, 'migrated': 0, 'failed': 0},
            'students': {'total': 0, 'migrated': 0, 'failed': 0},
            'staff': {'total': 0, 'migrated': 0, 'failed': 0},
            'organizations': {'total': 0, 'migrated': 0, 'failed': 0},
            'courses': {'total': 0, 'migrated': 0, 'failed': 0},
            'course_offerings': {'total': 0, 'migrated': 0, 'failed': 0},
            'course_instructors': {'total': 0, 'migrated': 0, 'failed': 0},
            'enrollments': {'total': 0, 'migrated': 0, 'failed': 0},
            'assessments': {'total': 0, 'migrated': 0, 'failed': 0},
            'grades': {'total': 0, 'migrated': 0, 'failed': 0}
        }
    
    def connect_databases(self):
        """Establish connections to both old and new databases"""
        try:
            logger.info("Connecting to old database (edu)...")
            self.old_conn = psycopg2.connect(**OLD_DB_CONFIG)
            logger.info("✓ Connected to old database")
            
            logger.info("Connecting to new database (edu_v2)...")
            self.new_conn = psycopg2.connect(**NEW_DB_CONFIG)
            logger.info("✓ Connected to new database")
            
            # Load existing ID mappings from new database
            self.load_existing_mappings()
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def load_existing_mappings(self):
        """Load existing ID mappings from migrated data in new database"""
        try:
            with self.new_conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Load user mappings
                cur.execute("""
                    SELECT id, metadata
                    FROM users
                    WHERE metadata IS NOT NULL
                """)
                users = cur.fetchall()
                self.id_mappings['users'] = {}
                self.id_mappings['accounts'] = {}  # Also store by old account_id
                for user in users:
                    if 'old_user_id' in user['metadata']:
                        old_id = user['metadata']['old_user_id']
                        self.id_mappings['users'][old_id] = user['id']
                    if 'old_account_id' in user['metadata']:
                        old_account_id = user['metadata']['old_account_id']
                        self.id_mappings['accounts'][old_account_id] = user['id']
                
                if self.id_mappings['users']:
                    logger.info(f"Loaded {len(self.id_mappings['users'])} existing user mappings")
                
                # Load student mappings if they exist
                cur.execute("""
                    SELECT id, metadata
                    FROM students
                    WHERE metadata IS NOT NULL
                """)
                students = cur.fetchall()
                if students:
                    self.id_mappings['students'] = {}
                    for student in students:
                        if 'old_student_id' in student['metadata']:
                            old_id = student['metadata']['old_student_id']
                            self.id_mappings['students'][old_id] = student['id']
                    logger.info(f"Loaded {len(self.id_mappings['students'])} existing student mappings")
                
                # Build person_to_user mapping by querying both databases
                # We need old person_id → new user UUID mapping
                # Old: accounts.person_id → users.account_id → new users.id
                pass  # Will be built from accounts table
                
        except Exception as e:
            logger.warning(f"Could not load existing mappings: {e}")
            # Continue anyway - mappings will be built during migration
        
        # Build person_to_user mapping from old database
        try:
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
                # Get accounts.person_id → accounts.id mapping
                old_cur.execute("SELECT id, person_id FROM accounts WHERE person_id IS NOT NULL")
                accounts = old_cur.fetchall()
                
                # Map: old person_id → old account_id → new user_uuid
                self.id_mappings.setdefault('person_to_user', {})
                for account in accounts:
                    account_id = account['id']
                    person_id = account['person_id']
                    
                    # Get the new user UUID for this account_id  
                    user_uuid = self.id_mappings.get('accounts', {}).get(account_id)
                    if user_uuid and person_id:
                        self.id_mappings['person_to_user'][person_id] = user_uuid
                
                if self.id_mappings.get('person_to_user'):
                    logger.info(f"Built {len(self.id_mappings['person_to_user'])} person→user mappings")
                
        except Exception as e:
            logger.warning(f"Could not build person_to_user mappings: {e}")
        
        # Load course_offerings mappings from both databases
        # We need to map old course.id → new course_offering.id
        try:
            # Get all new courses and offerings
            with self.new_conn.cursor(
                cursor_factory=RealDictCursor
            ) as new_cur:
                new_cur.execute("""
                    SELECT c.id as course_uuid, c.code,
                           co.id as offering_uuid
                    FROM courses c
                    JOIN course_offerings co ON c.id = co.course_id
                """)
                new_offerings = new_cur.fetchall()
            
            if new_offerings:
                self.id_mappings.setdefault('course_offerings', {})
                
                # Build mapping: course code → list of offering UUIDs
                code_to_offerings = {}
                for offering in new_offerings:
                    code = offering['code']
                    if code not in code_to_offerings:
                        code_to_offerings[code] = []
                    code_to_offerings[code].append(
                        offering['offering_uuid']
                    )
                
                # Parse subject_catalog IDs from codes
                # Code format: SUBJ00121 (subject_catalog.id % 100000)
                code_to_subject_ids = {}
                with self.old_conn.cursor(
                    cursor_factory=RealDictCursor
                ) as old_cur:
                    old_cur.execute(
                        "SELECT id FROM subject_catalog WHERE active = 1"
                    )
                    subjects = old_cur.fetchall()
                    
                    for subject in subjects:
                        code = f"SUBJ{subject['id'] % 100000:05d}"
                        if code not in code_to_subject_ids:
                            code_to_subject_ids[code] = []
                        code_to_subject_ids[code].append(subject['id'])
                
                # Now map old course.id to offerings
                with self.old_conn.cursor(
                    cursor_factory=RealDictCursor
                ) as old_cur:
                    old_cur.execute("""
                        SELECT c.id, eps.subject_id
                        FROM course c
                        LEFT JOIN education_plan_subject eps
                            ON c.education_plan_subject_id = eps.id
                        WHERE eps.subject_id IS NOT NULL
                    """)
                    old_courses = old_cur.fetchall()
                    
                    for old_course in old_courses:
                        old_course_id = old_course['id']
                        subject_id = old_course['subject_id']
                        
                        # Find the code for this subject_id
                        code = f"SUBJ{subject_id % 100000:05d}"
                        
                        # Get first offering for this code
                        offerings = code_to_offerings.get(code, [])
                        if offerings:
                            # Map to first offering
                            self.id_mappings['course_offerings'][
                                old_course_id
                            ] = offerings[0]
                
                logger.info(
                    f"Loaded {len(self.id_mappings['course_offerings'])} "
                    "existing course offering mappings"
                )
        except Exception as e:
            logger.warning(
                f"Could not load course_offerings mappings: {e}"
            )
    
    def close_connections(self):
        """Close database connections"""
        if self.old_conn:
            self.old_conn.close()
            logger.info("Closed old database connection")
        if self.new_conn:
            self.new_conn.close()
            logger.info("Closed new database connection")
    
    def generate_uuid_mapping(self, table_name: str, id_column: str = 'id') -> Dict[int, uuid.UUID]:
        """
        Generate UUID mappings for integer IDs
        
        Args:
            table_name: Name of the table
            id_column: Name of the ID column
            
        Returns:
            Dictionary mapping old integer IDs to new UUIDs
        """
        logger.info(f"Generating UUID mappings for {table_name}...")
        
        with self.old_conn.cursor() as cur:
            cur.execute(f"SELECT DISTINCT {id_column} FROM {table_name} WHERE {id_column} IS NOT NULL")
            old_ids = [row[0] for row in cur.fetchall()]
        
        mapping = {old_id: uuid.uuid4() for old_id in old_ids}
        self.id_mappings[table_name] = mapping
        
        logger.info(f"✓ Generated {len(mapping)} UUID mappings for {table_name}")
        return mapping
    
    def normalize_gender(self, gender: str) -> str:
        """Normalize gender values"""
        if not gender:
            return 'prefer_not_to_say'
        
        gender_lower = str(gender).lower().strip()
        
        if gender_lower in ['m', 'male', 'erkek', 'мужской']:
            return 'male'
        elif gender_lower in ['f', 'female', 'qadın', 'kişi', 'женский']:
            return 'female'
        else:
            return 'prefer_not_to_say'
    
    def create_multilingual_json(self, text: str, lang: str = 'az') -> dict:
        """Create multilingual JSON from single language text"""
        return {
            'az': text or '',
            'en': text or '',
            'ru': text or ''
        }
    
    # ========================================================================
    # PHASE 1: MIGRATE USERS AND PERSONS
    # ========================================================================
    
    def migrate_users(self):
        """Migrate users table (linking users → accounts for credentials)"""
        logger.info("=" * 60)
        logger.info("PHASE 1: MIGRATING USERS")
        logger.info("=" * 60)
        
        try:
            # Generate UUID mappings
            user_mapping = self.generate_uuid_mapping('users')
            
            # Fetch users with account information from old database
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        u.id, u.account_id, u.active, u.is_blocked,
                        u.create_date, u.update_date, u.last_action_date,
                        a.username, a.email, a.password, a.person_id
                    FROM users u
                    LEFT JOIN accounts a ON u.account_id = a.id
                    WHERE u.id IS NOT NULL
                    ORDER BY u.id
                """)
                old_users = cur.fetchall()
            
            self.stats['users']['total'] = len(old_users)
            logger.info(f"Found {len(old_users)} users to migrate")
            
            # Insert users into new database
            insert_query = """
                INSERT INTO users (
                    id, username, email, password_hash, is_active,
                    last_login_at, password_changed_at, created_at, updated_at, metadata
                ) VALUES %s
                ON CONFLICT (username) DO NOTHING
            """
            
            values = []
            for user in old_users:
                new_uuid = user_mapping[user['id']]
                
                # Store mapping from old account_id to new user UUID
                if user.get('account_id'):
                    self.id_mappings.setdefault('accounts', {})[user['account_id']] = new_uuid
                
                # Store mapping from old person_id to prepare for persons migration
                if user.get('person_id'):
                    self.id_mappings.setdefault('person_to_user', {})[user['person_id']] = new_uuid
                
                # Ensure username and email exist
                username = user.get('username') or f"user_{user['id']}"
                
                # Email validation - ensure it's in proper format
                raw_email = user.get('email') or ''
                if '@' in raw_email and '.' in raw_email.split('@')[-1]:
                    email = raw_email  # Valid email format
                else:
                    # Invalid or missing email - generate from username
                    email = f"{username}@temp.bbu.edu.az"
                
                # Password is stored in accounts table - decode from base64
                encoded_password = user.get('password') or ''
                password_hash = decode_base64_password(encoded_password)
                
                # Determine active status
                is_active = user.get('active', 0) == 1 and user.get('is_blocked', 0) == 0
                
                values.append((
                    new_uuid,
                    username,
                    email,
                    password_hash,
                    is_active,
                    user.get('last_action_date'),  # last_login_at
                    user.get('create_date'),  # password_changed_at
                    user.get('create_date') or datetime.now(),
                    user.get('update_date') or datetime.now(),
                    json.dumps({
                        'old_user_id': user['id'],
                        'old_account_id': user.get('account_id')
                    })
                ))
            
            with self.new_conn.cursor() as cur:
                execute_values(cur, insert_query, values)
                self.new_conn.commit()
                self.stats['users']['migrated'] = len(values)
            
            # Update user_mapping to reflect only actually inserted users
            # Query the database to get all inserted user IDs and their metadata
            with self.new_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, metadata
                    FROM users
                    WHERE metadata IS NOT NULL
                """)
                actual_users = cur.fetchall()
            
            # Rebuild the user_mapping with only successfully inserted users
            self.id_mappings['users'] = {}
            for user in actual_users:
                metadata = user['metadata']
                if 'old_user_id' in metadata:
                    old_user_id = metadata['old_user_id']
                    self.id_mappings['users'][old_user_id] = user['id']
            
            logger.info(f"✓ Migrated {len(actual_users)} users successfully (skipped {len(values) - len(actual_users)} duplicates)")
            
        except Exception as e:
            logger.error(f"User migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    def migrate_persons(self):
        """Migrate persons table"""
        logger.info("\nMIGRATING PERSONS...")
        
        try:
            # Fetch persons with account and user linkage
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        p.id, p.firstname, p.lastname, p.patronymic,
                        p.birthdate, p.gender_id, p.pincode,
                        p.create_date, p.update_date,
                        a.id as account_id, u.id as user_id
                    FROM persons p
                    LEFT JOIN accounts a ON p.id = a.person_id
                    LEFT JOIN users u ON a.id = u.account_id
                    WHERE u.id IS NOT NULL
                    ORDER BY p.id
                """)
                old_persons = cur.fetchall()
            
            self.stats['persons']['total'] = len(old_persons)
            logger.info(f"Found {len(old_persons)} persons to migrate")
            
            insert_query = """
                INSERT INTO persons (
                    id, user_id, first_name, last_name, middle_name,
                    date_of_birth, gender, national_id,
                    created_at, updated_at
                ) VALUES %s
                ON CONFLICT (user_id) DO NOTHING
            """
            
            user_mapping = self.id_mappings['users']
            values = []
            
            for person in old_persons:
                if person['user_id'] not in user_mapping:
                    continue
                
                # Map gender_id to gender string (1=Male, 2=Female)
                gender_id = person.get('gender_id')
                if gender_id == 1:
                    gender = 'male'
                elif gender_id == 2:
                    gender = 'female'
                else:
                    gender = 'other'
                
                # Parse birthdate - handle DD/MM/YYYY format
                birthdate = None
                if person.get('birthdate'):
                    try:
                        # Try DD/MM/YYYY format first
                        birthdate = datetime.strptime(str(person['birthdate']), '%d/%m/%Y').date()
                    except Exception:
                        try:
                            # Try ISO format
                            birthdate = datetime.strptime(str(person['birthdate']), '%Y-%m-%d').date()
                        except Exception:
                            birthdate = None
                
                values.append((
                    uuid.uuid4(),
                    user_mapping[person['user_id']],
                    person.get('firstname', 'Unknown'),
                    person.get('lastname', 'Unknown'),
                    person.get('patronymic'),
                    birthdate,
                    gender,
                    person.get('pincode'),
                    person.get('create_date') or datetime.now(),
                    person.get('update_date') or datetime.now()
                ))
            
            with self.new_conn.cursor() as cur:
                execute_values(cur, insert_query, values)
                self.new_conn.commit()
                self.stats['persons']['migrated'] = len(values)
            
            logger.info(f"✓ Migrated {len(values)} persons successfully")
            
        except Exception as e:
            logger.error(f"Person migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    # ========================================================================
    # PHASE 2: MIGRATE STUDENTS AND STAFF
    # ========================================================================
    
    def migrate_students(self):
        """Migrate students table"""
        logger.info("=" * 60)
        logger.info("PHASE 2: MIGRATING STUDENTS")
        logger.info("=" * 60)
        
        try:
            # Generate student UUID mapping
            student_mapping = self.generate_uuid_mapping('students')
            
            # Fetch students with user linkage
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        s.id, s.person_id, s.user_id, s.org_id,
                        s.education_type_id, s.education_payment_type_id,
                        s.education_lang_id, s.score, s.card_number,
                        s.status, s.active, s.create_date, s.update_date
                    FROM students s
                    WHERE s.user_id IS NOT NULL AND s.active = 1
                    ORDER BY s.id
                """)
                old_students = cur.fetchall()
            
            self.stats['students']['total'] = len(old_students)
            logger.info(f"Found {len(old_students)} students to migrate")
            
            # Get user mapping
            user_mapping = self.id_mappings.get('users', {})
            
            insert_query = """
                INSERT INTO students (
                    id, user_id, student_number, enrollment_date, status,
                    study_mode, funding_type, gpa, total_credits_earned,
                    created_at, updated_at, metadata
                ) VALUES %s
                ON CONFLICT (student_number) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    metadata = EXCLUDED.metadata
            """
            
            user_mapping = self.id_mappings['users']
            values = []
            
            for student in old_students:
                if student['user_id'] not in user_mapping:
                    continue
                
                new_student_uuid = student_mapping[student['id']]
                
                # Store mapping for later use
                self.id_mappings.setdefault('students', {})[student['id']] = new_student_uuid
                
                # Generate student number from ID if card_number not available
                student_number = student.get('card_number') or f"STU{student['id']}"
                
                # Map status
                status_id = student.get('status')
                status = 'active' if student.get('active') == 1 else 'inactive'
                
                # Parse enrollment date
                enrollment_date = student.get('create_date')
                if enrollment_date:
                    enrollment_date = enrollment_date.date() if hasattr(enrollment_date, 'date') else enrollment_date
                else:
                    enrollment_date = datetime.now().date()
                
                # Map funding type from education_payment_type_id
                funding_type = 'self_funded'  # Default
                
                # Map study mode
                study_mode = 'full_time'  # Default
                
                # Parse GPA from score field
                gpa = None
                if student.get('score'):
                    try:
                        score_val = float(student['score'])
                        # Assuming score is 0-100, convert to 0-4.0 scale
                        if score_val <= 100:
                            gpa = round((score_val / 100.0) * 4.0, 2)
                        # If score is already in 0-4 range, use as-is
                        elif score_val <= 4.0:
                            gpa = round(score_val, 2)
                        # Cap at 4.0
                        if gpa and gpa > 4.0:
                            gpa = 4.0
                    except Exception:
                        gpa = None
                
                values.append((
                    new_student_uuid,
                    user_mapping[student['user_id']],
                    student_number,
                    enrollment_date,
                    status,
                    study_mode,
                    funding_type,
                    gpa,
                    0,  # total_credits_earned - to be calculated later
                    student.get('create_date') or datetime.now(),
                    student.get('update_date') or datetime.now(),
                    json.dumps({
                        'old_student_id': student['id'],
                        'old_person_id': student.get('person_id'),
                        'old_org_id': student.get('org_id'),
                        'education_type_id': student.get('education_type_id'),
                        'education_payment_type_id': student.get('education_payment_type_id'),
                        'education_lang_id': student.get('education_lang_id')
                    })
                ))
            
            with self.new_conn.cursor() as cur:
                execute_values(cur, insert_query, values)
                self.new_conn.commit()
                self.stats['students']['migrated'] = len(values)
            
            logger.info(f"✓ Migrated {len(values)} students successfully")
            
        except Exception as e:
            logger.error(f"Student migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    def migrate_staff(self):
        """Migrate teachers to staff_members table"""
        logger.info("\nMIGRATING STAFF (TEACHERS)...")
        
        try:
            # Generate staff UUID mapping
            staff_mapping = self.generate_uuid_mapping('teachers')
            
            # Fetch teachers with user linkage
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        t.id, t.person_id, t.user_id, t.organization_id,
                        t.staff_type_id, t.position_id, t.contract_type_id,
                        t.teaching, t.in_action_date, t.out_action_date,
                        t.active, t.create_date, t.update_date
                    FROM teachers t
                    WHERE t.user_id IS NOT NULL AND t.active = 1
                    ORDER BY t.id
                """)
                old_teachers = cur.fetchall()
            
            self.stats['staff']['total'] = len(old_teachers)
            logger.info(f"Found {len(old_teachers)} teachers to migrate")
            
            # Get user mapping
            user_mapping = self.id_mappings.get('users', {})
            
            insert_query = """
                INSERT INTO staff_members (
                    id, user_id, employee_number, position_title,
                    employment_type, hire_date, is_active,
                    created_at, updated_at
                ) VALUES %s
                ON CONFLICT (user_id) DO UPDATE SET
                    employee_number = EXCLUDED.employee_number,
                    position_title = EXCLUDED.position_title
            """
            
            values = []
            
            for teacher in old_teachers:
                if teacher['user_id'] not in user_mapping:
                    continue
                
                new_staff_uuid = staff_mapping[teacher['id']]
                
                # Store mapping for later use
                self.id_mappings.setdefault('teachers', {})[teacher['id']] = new_staff_uuid
                
                # Employee number
                employee_number = f"TCH{teacher['id']}"
                
                # Position title - store as multilingual JSON
                position_title = json.dumps({
                    'az': 'Müəllim',
                    'en': 'Teacher',
                    'ru': 'Преподаватель'
                })
                
                # Map employment type from contract_type_id
                employment_type = 'full_time'  # Default
                
                # Parse hire date from in_action_date (DD/MM/YYYY format)
                hire_date = None
                if teacher.get('in_action_date'):
                    try:
                        hire_date = datetime.strptime(str(teacher['in_action_date']), '%d/%m/%Y').date()
                    except Exception:
                        hire_date = None
                
                if not hire_date:
                    hire_date = teacher.get('create_date')
                    if hire_date:
                        hire_date = hire_date.date() if hasattr(hire_date, 'date') else hire_date
                    else:
                        hire_date = datetime.now().date()
                
                is_active = teacher.get('active') == 1 and not teacher.get('out_action_date')
                
                values.append((
                    new_staff_uuid,
                    user_mapping[teacher['user_id']],
                    employee_number,
                    position_title,
                    employment_type,
                    hire_date,
                    is_active,
                    teacher.get('create_date') or datetime.now(),
                    teacher.get('update_date') or datetime.now()
                ))
            
            with self.new_conn.cursor() as cur:
                execute_values(cur, insert_query, values)
                self.new_conn.commit()
                self.stats['staff']['migrated'] = len(values)
            
            logger.info(f"✓ Migrated {len(values)} staff members successfully")
            
            # Store teacher mapping for later use
            self.id_mappings['teachers'] = staff_mapping
            
        except Exception as e:
            logger.error(f"Staff migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    # ========================================================================
    # PHASE 3: MIGRATE ORGANIZATIONS AND ACADEMIC STRUCTURE
    # ========================================================================
    
    def migrate_organizations(self):
        """Migrate organizations to organization_units"""
        logger.info("=" * 60)
        logger.info("PHASE 3: MIGRATING ORGANIZATIONS")
        logger.info("=" * 60)
        
        try:
            # Generate organization UUID mapping for ALL orgs (including inactive ones as parents)
            org_mapping = self.generate_uuid_mapping('organizations')
            logger.info(f"Generated {len(org_mapping)} total organization UUID mappings")
            
            # Fetch ALL organizations (including inactive) to maintain hierarchy
            # Some active orgs may have inactive parents
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        o.id, o.parent_id, o.dictionary_name_id, o.formula,
                        o.type_id, o.nod_level, o.active,
                        o.create_date, o.update_date,
                        d.name_az, d.name_en, d.name_ru, d.code
                    FROM organizations o
                    LEFT JOIN dictionaries d ON d.id = o.dictionary_name_id
                    ORDER BY o.parent_id NULLS FIRST, o.id
                """)
                old_orgs = cur.fetchall()
            
            self.stats['organizations']['total'] = len(old_orgs)
            logger.info(f"Found {len(old_orgs)} total organizations (including inactive) to migrate")
            
            # Determine organization type based on hierarchy
            def determine_org_type(org, all_orgs):
                if org['parent_id'] is None:
                    return 'university'
                
                # Check if has children
                has_children = any(o['parent_id'] == org['id'] for o in all_orgs)
                
                if has_children:
                    # Check parent type
                    parent = next((o for o in all_orgs if o['id'] == org['parent_id']), None)
                    if parent and parent['parent_id'] is None:
                        return 'faculty'
                    else:
                        return 'department'
                else:
                    return 'program'
            
            insert_query = """
                INSERT INTO organization_units (
                    id, parent_id, type, code, name, is_active,
                    created_at, updated_at
                ) VALUES %s
                ON CONFLICT (code) DO UPDATE SET
                    parent_id = EXCLUDED.parent_id,
                    name = EXCLUDED.name,
                    updated_at = EXCLUDED.updated_at
            """
            
            values = []
            for org in old_orgs:
                org_type = determine_org_type(org, old_orgs)
                
                name_json = {
                    'az': org.get('name_az') or f"Organization {org['id']}",
                    'en': org.get('name_en') or org.get('name_az') or f"Organization {org['id']}",
                    'ru': org.get('name_ru') or org.get('name_az') or f"Organization {org['id']}"
                }
                
                # Use formula or code from dictionary, fallback to generated code
                org_code = (org.get('formula') or 
                           org.get('code') or 
                           f"ORG{org['id']}")
                
                parent_uuid = None
                if org['parent_id'] and org['parent_id'] in org_mapping:
                    parent_uuid = org_mapping[org['parent_id']]
                
                values.append((
                    org_mapping[org['id']],
                    parent_uuid,
                    org_type,
                    org_code,
                    json.dumps(name_json),
                    bool(org.get('active', 1)),
                    org.get('create_date') or datetime.now(),
                    org.get('update_date') or datetime.now()
                ))
            
            # Insert all organizations at once, sorted by hierarchy
            # Sort: roots first, then by parent_id to insert parents before children
            sorted_values = sorted(values, key=lambda x: (
                x[1] is not None,  # False (None) sorts first
                str(x[1]) if x[1] else ''  # Then sort by parent UUID string
            ))
            
            with self.new_conn.cursor() as cur:
                # Insert in batches to handle large datasets
                batch_size = 100
                total_inserted = 0
                
                for i in range(0, len(sorted_values), batch_size):
                    batch = sorted_values[i:i+batch_size]
                    execute_values(cur, insert_query, batch)
                    total_inserted += len(batch)
                
                logger.info(f"✓ Inserted {total_inserted} organizations")
                
                self.new_conn.commit()
                self.stats['organizations']['migrated'] = total_inserted
            
            logger.info(f"✓ Migrated {total_inserted} organizations successfully")
            
            # Store organization mapping
            self.id_mappings['organizations'] = org_mapping
            
        except Exception as e:
            logger.error(f"Organization migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    def migrate_academic_terms(self):
        """Create academic terms for 2020-2025"""
        logger.info("\nCREATING ACADEMIC TERMS...")
        
        try:
            insert_query = """
                INSERT INTO academic_terms (
                    id, academic_year, term_type, term_number,
                    start_date, end_date, is_current
                ) VALUES %s
                ON CONFLICT DO NOTHING
            """
            
            values = []
            for year in range(2020, 2026):
                # Fall semester
                values.append((
                    uuid.uuid4(),
                    f"{year}-{year+1}",
                    'fall',
                    1,
                    f"{year}-09-01",
                    f"{year}-12-31",
                    (year == 2024)  # 2024-2025 Fall is current
                ))
                
                # Spring semester
                values.append((
                    uuid.uuid4(),
                    f"{year}-{year+1}",
                    'spring',
                    2,
                    f"{year+1}-02-01",
                    f"{year+1}-06-30",
                    False
                ))
            
            with self.new_conn.cursor() as cur:
                execute_values(cur, insert_query, values)
                self.new_conn.commit()
            
            logger.info(f"✓ Created {len(values)} academic terms")
            
        except Exception as e:
            logger.error(f"Academic term creation failed: {e}")
            self.new_conn.rollback()
            raise
    
    # ========================================================================
    # PHASE 4: COURSES AND OFFERINGS
    # ========================================================================
    
    def get_multilingual_name(self, dictionary_id: int, cur) -> dict:
        """
        Fetch multilingual name from dictionaries table
        
        Args:
            dictionary_id: ID in dictionaries table
            cur: Database cursor
        
        Returns:
            dict with az, en, ru keys
        """
        if not dictionary_id:
            return {"az": "N/A", "en": "N/A", "ru": "N/A"}
        
        cur.execute("""
            SELECT name_az, name_en, name_ru 
            FROM dictionaries 
            WHERE id = %s
        """, (dictionary_id,))
        
        row = cur.fetchone()
        if row:
            return {
                "az": row['name_az'] or "N/A",
                "en": row['name_en'] or row['name_az'] or "N/A",
                "ru": row['name_ru'] or row['name_az'] or "N/A"
            }
        return {"az": f"Unknown {dictionary_id}", "en": f"Unknown {dictionary_id}", "ru": f"Unknown {dictionary_id}"}
    
    def migrate_courses(self):
        """Migrate subject_catalog → courses (Master Course Catalog)"""
        logger.info("=" * 60)
        logger.info("PHASE 4.1: Migrating Courses (Master Catalog)")
        logger.info("=" * 60)
        
        try:
            # First, load existing course mappings from new database
            # We need to match old subject_catalog IDs to existing course UUIDs by code
            with self.new_conn.cursor(cursor_factory=RealDictCursor) as new_cur:
                with self.old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
                    # Get all existing courses with their codes
                    new_cur.execute("SELECT id, code FROM courses")
                    existing_courses_by_code = {row['code']: row['id'] for row in new_cur.fetchall()}
                    
                    # Get all old subject_catalog entries to build mapping
                    old_cur.execute("SELECT id FROM subject_catalog WHERE active = 1")
                    old_subjects = old_cur.fetchall()
                    
                    # Build initial mappings for existing courses
                    self.id_mappings.setdefault('courses', {})
                    for subject in old_subjects:
                        course_code = f"SUBJ{subject['id'] % 100000:05d}"
                        if course_code in existing_courses_by_code:
                            self.id_mappings['courses'][subject['id']] = existing_courses_by_code[course_code]
                    
                    if self.id_mappings['courses']:
                        logger.info(f"Loaded {len(self.id_mappings['courses'])} existing course mappings")
            
            # Fetch all active subject catalog entries
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        sc.id, sc.subject_name_id, sc.organization_id, sc.active,
                        sc.create_date, sc.update_date,
                        d.name_az, d.name_en, d.name_ru
                    FROM subject_catalog sc
                    LEFT JOIN dictionaries d ON d.id = sc.subject_name_id
                    WHERE sc.active = 1
                    ORDER BY sc.id
                """)
                old_courses = cur.fetchall()
                
                self.stats['courses']['total'] = len(old_courses)
                logger.info(f"Found {len(old_courses)} courses to migrate")
                
                # Prepare course data with multilingual names
                course_values = []
                for course in old_courses:
                    # Generate course code
                    course_code = f"SUBJ{course['id'] % 100000:05d}"
                    
                    # Use existing UUID if available, otherwise generate new one
                    if course['id'] in self.id_mappings['courses']:
                        course_uuid = self.id_mappings['courses'][course['id']]
                    else:
                        course_uuid = uuid.uuid4()
                        self.id_mappings['courses'][course['id']] = course_uuid
                    
                    # Multilingual name
                    multilingual_name = {
                        'az': course.get('name_az') or f"Subject {course['id']}",
                        'en': course.get('name_en') or course.get('name_az') or f"Subject {course['id']}",
                        'ru': course.get('name_ru') or course.get('name_az') or f"Subject {course['id']}"
                    }
                    
                    # Map organization UUID
                    org_uuid = self.id_mappings.get('organizations', {}).get(course['organization_id'])
                    
                    course_values.append((
                        course_uuid,
                        course_code,
                        json.dumps(multilingual_name),
                        3,  # Default credit hours
                        org_uuid,
                        True,  # is_active
                        course.get('create_date') or datetime.now(),
                        course.get('update_date') or datetime.now()
                    ))
            
            # Insert into new database
            insert_query = """
                INSERT INTO courses (
                    id, code, name, credit_hours, organization_unit_id,
                    is_active, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    updated_at = EXCLUDED.updated_at
            """
            
            with self.new_conn.cursor() as cur:
                execute_values(cur, insert_query, course_values)
                self.new_conn.commit()
            
            self.stats['courses']['migrated'] = len(course_values)
            logger.info(f"✓ Migrated {len(course_values)} courses")

            
        except Exception as e:
            logger.error(f"Course migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    def migrate_course_offerings(self):
        """Migrate course → course_offerings (Course Instances)"""
        logger.info("=" * 60)
        logger.info("PHASE 4.2: Migrating Course Offerings")
        logger.info("=" * 60)
        
        try:
            # Fetch all course offerings with subject mapping
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        c.id, c.code, c.education_plan_subject_id,
                        c.semester_id, c.education_year_id, c.education_lang_id,
                        c.m_hours, c.s_hours, c.l_hours, c.fm_hours,
                        c.student_count, c.active, c.start_date,
                        c.create_date, c.update_date,
                        eps.subject_id
                    FROM course c
                    LEFT JOIN education_plan_subject eps 
                      ON c.education_plan_subject_id = eps.id
                    WHERE c.active = 1
                    ORDER BY c.id
                """)
                old_offerings = cur.fetchall()
                
                self.stats['course_offerings']['total'] = len(old_offerings)
                logger.info(f"Found {len(old_offerings)} course offerings to migrate")
            
            # Get academic terms from NEW database
            with self.new_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT id FROM academic_terms ORDER BY start_date LIMIT 1')
                result = cur.fetchone()
                default_term = result['id'] if result else None
                
                if not default_term:
                    logger.error("No academic terms found in new database")
                    return
                
                # Load existing course_offerings mappings
                # We need to map old course.id → new course_offering UUID by section_code
                with self.new_conn.cursor(cursor_factory=RealDictCursor) as new_cur:
                    # Get all existing course_offerings
                    new_cur.execute("SELECT id, section_code FROM course_offerings")
                    existing_offerings_by_section = {row['section_code']: row['id'] for row in new_cur.fetchall()}
                    
                    # Build initial mapping for existing offerings
                    self.id_mappings.setdefault('course_offerings', {})
                    
                offering_values = []
                seen_keys = set()  # Track (course_id, term_id, section_code) to avoid duplicates
                duplicate_count = 0
                skipped_no_mapping = 0
                
                for offering in old_offerings:
                    # Extract section code first (before generating UUID)
                    section_code = offering.get('code', f"S{offering['id'] % 10000:04d}")[:20]
                    
                    # Check if this offering already exists
                    if section_code in existing_offerings_by_section:
                        offering_uuid = existing_offerings_by_section[section_code]
                        self.id_mappings['course_offerings'][offering['id']] = offering_uuid
                        continue  # Skip - already exists
                    
                    # Generate new UUID for new offering
                    offering_uuid = uuid.uuid4()
                    self.id_mappings['course_offerings'][offering['id']] = offering_uuid
                    
                    # Map to master course via subject_id
                    subject_id = offering.get('subject_id')
                    course_uuid = self.id_mappings.get('courses', {}).get(subject_id)
                    
                    if not course_uuid:
                        # Skip offerings without valid course mapping
                        skipped_no_mapping += 1
                        if skipped_no_mapping <= 3:
                            logger.debug(f"No course mapping for subject_id {subject_id}, offering {offering['id']}")
                        continue
                    
                    # Use default academic term for now
                    term_uuid = default_term
                    
                    # Extract section code from course code
                    section_code = offering.get('code', f"S{offering['id'] % 10000:04d}")[:20]
                    
                    # Check for duplicates within this batch
                    key = (str(course_uuid), str(term_uuid), section_code)
                    if key in seen_keys:
                        # Modify section code to make it unique
                        section_code = f"{section_code}-{offering['id'] % 1000:03d}"[:20]
                        key = (str(course_uuid), str(term_uuid), section_code)
                        
                        if key in seen_keys:
                            duplicate_count += 1
                            continue  # Skip this duplicate
                    
                    seen_keys.add(key)
                    
                    # Language mapping
                    lang_map = {1: 'az', 2: 'en', 3: 'ru'}
                    lang = lang_map.get(offering.get('education_lang_id'), 'az')
                    
                    offering_values.append((
                        offering_uuid,
                        course_uuid,
                        term_uuid,
                        section_code,
                        lang,
                        offering.get('student_count') or 30,
                        0,  # current_enrollment
                        'online' if 'online' in str(offering.get('code', '')).lower() else 'in_person',
                        True,  # is_published
                        'open',  # enrollment_status
                        offering.get('create_date') or datetime.now(),
                        offering.get('update_date') or datetime.now()
                    ))
                
                if duplicate_count > 0:
                    logger.info(f"Skipped {duplicate_count} duplicate offerings")
                if skipped_no_mapping > 0:
                    logger.warning(f"Skipped {skipped_no_mapping} offerings without course mapping")
            
            if not offering_values:
                logger.warning("No course offerings to migrate (all filtered out)")
                return
            
            # Insert into new database
            insert_query = """
                INSERT INTO course_offerings (
                    id, course_id, academic_term_id, section_code,
                    language_of_instruction, max_enrollment, current_enrollment,
                    delivery_mode, is_published, enrollment_status,
                    created_at, updated_at
                ) VALUES %s
                ON CONFLICT (course_id, academic_term_id, section_code) DO UPDATE SET
                    max_enrollment = EXCLUDED.max_enrollment,
                    current_enrollment = EXCLUDED.current_enrollment,
                    updated_at = EXCLUDED.updated_at
            """
            
            with self.new_conn.cursor() as cur:
                execute_values(cur, insert_query, offering_values)
                self.new_conn.commit()
            
            self.stats['course_offerings']['migrated'] = len(offering_values)
            logger.info(f"✓ Migrated {len(offering_values)} course offerings")
            
        except Exception as e:
            logger.error(f"Course offering migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    def create_term_mapping(self, cur) -> Dict[Tuple[int, int], str]:
        """
        Create mapping from (semester_id, year_id) to term UUID
        
        Returns:
            Dictionary mapping (semester_id, year_id) to term UUID
        """
        mapping = {}
        
        with self.new_conn.cursor(cursor_factory=RealDictCursor) as new_cur:
            new_cur.execute("SELECT id, academic_year, term_type FROM academic_terms")
            terms = new_cur.fetchall()
            
            # Create mapping based on year and term type
            for term in terms:
                year = term['academic_year'].split('-')[0]  # "2024-2025" -> "2024"
                
                # Map semester_id to term_type (this is a simplification)
                # 110000135 might mean Fall, adjust based on actual data
                if term['term_type'] == 'fall':
                    semester_ids = [110000135]  # Add actual IDs
                elif term['term_type'] == 'spring':
                    semester_ids = [110000136]  # Add actual IDs
                
                # This is simplified - in production, query dictionaries for actual mapping
                mapping[(110000135, None)] = term['id']  # Placeholder
        
        return mapping
    
    def migrate_course_instructors(self):
        """Migrate course_teacher → course_instructors"""
        logger.info("=" * 60)
        logger.info("PHASE 4.3: Migrating Course Instructors")
        logger.info("=" * 60)
        
        try:
            # Build teacher ID → user UUID mapping (instructor_id references users table)
            # teacher.id → teacher.person_id → user.id
            teacher_to_user = {}
            
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
                # Get teacher → person mapping
                old_cur.execute("SELECT id, person_id FROM teachers WHERE active = 1")
                teachers = old_cur.fetchall()
                
                # Build the chain: teacher_id → person_id → user_uuid
                for teacher in teachers:
                    teacher_id = teacher['id']
                    person_id = teacher['person_id']
                    
                    # Get user UUID from person_to_user mapping
                    user_uuid = self.id_mappings.get('person_to_user', {}).get(person_id)
                    
                    if user_uuid:
                        teacher_to_user[teacher_id] = user_uuid
            
            logger.info(f"Built {len(teacher_to_user)} teacher→user mappings")
            
            # Fetch all course-teacher assignments
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        id, course_id, teacher_id, lesson_type_id, active,
                        create_date
                    FROM course_teacher
                    WHERE active = 1
                    ORDER BY id
                """)
                old_instructors = cur.fetchall()
                
                logger.info(f"Found {len(old_instructors)} course-instructor assignments to migrate")
                
                instructor_values = []
                seen_pairs = set()  # Track (offering_uuid, staff_uuid) to avoid duplicates
                skipped_no_offering = 0
                skipped_no_staff = 0
                skipped_duplicate = 0
                
                for instructor in old_instructors:
                    instructor_uuid = uuid.uuid4()
                    
                    # Map to course offering
                    offering_uuid = self.id_mappings.get('course_offerings', {}).get(instructor['course_id'])
                    
                    # Map teacher_id to user UUID (instructor_id references users table)
                    user_uuid = teacher_to_user.get(instructor['teacher_id'])
                    
                    if not offering_uuid:
                        skipped_no_offering += 1
                        continue
                    
                    if not user_uuid:
                        skipped_no_staff += 1
                        continue
                    
                    # Check for duplicates
                    pair_key = (str(offering_uuid), str(user_uuid))
                    if pair_key in seen_pairs:
                        skipped_duplicate += 1
                        continue
                    
                    seen_pairs.add(pair_key)
                    
                    # Map lesson type to role (simplified mapping)
                    role = 'primary'  # Default role
                    
                    instructor_values.append((
                        instructor_uuid,
                        offering_uuid,
                        user_uuid,
                        role,
                        instructor.get('create_date') or datetime.now()
                    ))
                
                if skipped_no_offering > 0:
                    logger.info(f"Skipped {skipped_no_offering} instructors (no offering mapping)")
                if skipped_no_staff > 0:
                    logger.info(f"Skipped {skipped_no_staff} instructors (no staff mapping)")
                if skipped_duplicate > 0:
                    logger.info(f"Skipped {skipped_duplicate} duplicate instructor assignments")
            
            if not instructor_values:
                logger.warning("No course instructors to migrate")
                return
            
            # Insert into new database
            insert_query = """
                INSERT INTO course_instructors (
                    id, course_offering_id, instructor_id, role,
                    assigned_date
                ) VALUES %s
            """
            
            with self.new_conn.cursor() as cur:
                execute_values(cur, insert_query, instructor_values)
                self.new_conn.commit()
            
            self.stats['course_instructors']['migrated'] = len(instructor_values)
            logger.info(f"✓ Migrated {len(instructor_values)} course instructor assignments")
            
        except Exception as e:
            logger.error(f"Course instructor migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    # ========================================================================
    # PHASE 5: ENROLLMENTS AND GRADES
    # ========================================================================
    
    def migrate_enrollments(self):
        """Migrate course_student → course_enrollments"""
        logger.info("=" * 60)
        logger.info("PHASE 5.1: Migrating Course Enrollments")
        logger.info("=" * 60)
        
        try:
            enrolled_students = set()  # Track to avoid duplicates
            enrollment_values = []
            skipped_no_offering = 0
            skipped_no_student = 0
            
            # Migrate direct course enrollments
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        id, course_id, student_id, active,
                        create_date, update_date, course_work
                    FROM course_student
                    WHERE active = 1
                    ORDER BY id
                """)
                course_students = cur.fetchall()
                
                logger.info(f"Found {len(course_students)} direct course enrollments")
                
                for enrollment in course_students:
                    enrollment_uuid = str(uuid.uuid4())
                    
                    # Map to course offering
                    offering_uuid = self.id_mappings.get('course_offerings', {}).get(enrollment['course_id'])
                    
                    # Map to student
                    student_uuid = self.id_mappings.get('students', {}).get(enrollment['student_id'])
                    
                    if not offering_uuid:
                        skipped_no_offering += 1
                        continue
                    
                    if not student_uuid:
                        skipped_no_student += 1
                        continue
                    
                    # Track enrollment to avoid duplicates
                    enrollment_key = (offering_uuid, student_uuid)
                    if enrollment_key in enrolled_students:
                        continue
                    enrolled_students.add(enrollment_key)
                    
                    # Determine enrollment status
                    enrollment_status = 'enrolled' if enrollment['active'] == 1 else 'completed'
                    
                    # Determine if retake
                    is_retake = bool(enrollment.get('course_work') == 1)
                    
                    enrollment_values.append((
                        enrollment_uuid,
                        offering_uuid,
                        student_uuid,
                        enrollment_status,
                        enrollment['create_date'] or datetime.now(),
                        None,  # status_changed_date
                        None,  # grade (filled later from grades)
                        None,  # grade_points (filled later from grades)
                        None,  # attendance_percentage (filled later)
                        is_retake,
                        None,  # notes
                        enrollment['create_date'] or datetime.now(),
                        datetime.now()
                    ))
                
                self.stats['enrollments']['total'] = len(course_students)
                self.stats['enrollments']['migrated'] = len(enrollment_values)
            
            # Insert into new database in batches
            insert_query = """
                INSERT INTO course_enrollments (
                    id, course_offering_id, student_id, enrollment_status,
                    enrollment_date, status_changed_date, grade, grade_points,
                    attendance_percentage, is_retake, notes, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (course_offering_id, student_id) 
                WHERE enrollment_status = 'enrolled'
                DO UPDATE SET
                    enrollment_date = EXCLUDED.enrollment_date,
                    enrollment_status = EXCLUDED.enrollment_status
            """
            
            batch_size = 5000
            for i in range(0, len(enrollment_values), batch_size):
                batch = enrollment_values[i:i+batch_size]
                with self.new_conn.cursor() as cur:
                    execute_values(cur, insert_query, batch)
                    self.new_conn.commit()
                logger.info(f"  Inserted batch {i//batch_size + 1}/{(len(enrollment_values)-1)//batch_size + 1}")
            
            logger.info(f"✓ Migrated {len(enrollment_values)} enrollments")
            if skipped_no_offering > 0:
                logger.info(f"Skipped {skipped_no_offering} enrollments (no offering mapping)")
            if skipped_no_student > 0:
                logger.info(f"Skipped {skipped_no_student} enrollments (no student mapping)")
            
        except Exception as e:
            logger.error(f"Enrollment migration failed: {e}")
            self.new_conn.rollback()
            raise

            raise
    
    def migrate_assessments(self):
        """Migrate journal → assessments"""
        logger.info("=" * 60)
        logger.info("PHASE 5.2: Migrating Assessments")
        logger.info("=" * 60)
        
        try:
            # Group journal entries by course_id + course_eva_id to create
            # assessments
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT
                        course_id, course_eva_id,
                        MIN(create_date) as create_date,
                        MAX(update_date) as update_date
                    FROM journal
                    WHERE active = 1
                    GROUP BY course_id, course_eva_id
                    ORDER BY course_id, course_eva_id
                """)
                assessment_groups = cur.fetchall()
                
                logger.info(
                    f"Found {len(assessment_groups)} unique assessments"
                )
                
                assessment_values = []
                skipped_no_offering = 0
                
                for assessment in assessment_groups:
                    assessment_uuid = str(uuid.uuid4())
                    
                    # Map to course offering
                    offering_uuid = self.id_mappings.get(
                        'course_offerings', {}
                    ).get(assessment['course_id'])
                    
                    if not offering_uuid:
                        skipped_no_offering += 1
                        continue
                    
                    # Store mapping for grades migration
                    key = (assessment['course_id'], assessment['course_eva_id'])
                    self.id_mappings.setdefault(
                        'assessments', {}
                    )[key] = assessment_uuid
                    
                    # Determine assessment type based on eva_id
                    eva_id = assessment['course_eva_id']
                    if eva_id:
                        # Simple heuristic - can be improved with actual data
                        if eva_id <= 2:
                            assessment_type = 'exam'
                            weight = 40.0
                        elif eva_id <= 5:
                            assessment_type = 'quiz'
                            weight = 10.0
                        else:
                            assessment_type = 'assignment'
                            weight = 15.0
                    else:
                        assessment_type = 'assignment'
                        weight = 15.0
                    
                    # Create multilingual title
                    title = {
                        "az": f"Qiymətləndirmə {eva_id}",
                        "en": f"Assessment {eva_id}",
                        "ru": f"Оценка {eva_id}"
                    }
                    
                    assessment_values.append((
                        assessment_uuid,
                        offering_uuid,
                        json.dumps(title),
                        None,  # description
                        assessment_type,
                        weight,
                        100.0,  # total_marks
                        None,  # passing_marks
                        assessment['update_date'],  # due_date
                        None,  # duration_minutes
                        None,  # instructions
                        None,  # submission_type
                        False,  # allows_late_submission
                        None,  # late_penalty_per_day
                        1,  # max_attempts
                        False,  # is_group_work
                        None,  # rubric
                        None,  # created_by
                        assessment['create_date'] or datetime.now(),
                        datetime.now()
                    ))
                
                self.stats['assessments']['total'] = len(assessment_groups)
                self.stats['assessments']['migrated'] = len(assessment_values)
            
            # Insert into new database in batches
            insert_query = """
                INSERT INTO assessments (
                    id, course_offering_id, title, description,
                    assessment_type, weight_percentage,
                    total_marks, passing_marks, due_date, duration_minutes,
                    instructions, submission_type, allows_late_submission,
                    late_penalty_per_day, max_attempts, is_group_work,
                    rubric, created_by, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (id) DO NOTHING
            """
            
            batch_size = 5000
            for i in range(0, len(assessment_values), batch_size):
                batch = assessment_values[i:i+batch_size]
                with self.new_conn.cursor() as cur:
                    execute_values(cur, insert_query, batch)
                    self.new_conn.commit()
                logger.info(
                    f"  Inserted batch {i//batch_size + 1}/"
                    f"{(len(assessment_values)-1)//batch_size + 1}"
                )
            
            logger.info(f"✓ Migrated {len(assessment_values)} assessments")
            if skipped_no_offering > 0:
                logger.info(
                    f"Skipped {skipped_no_offering} assessments "
                    "(no offering mapping)"
                )
            
        except Exception as e:
            logger.error(f"Assessment migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    def migrate_grades(self):

        """Migrate journal_details → grades (3.2M records - BATCHED)"""
        logger.info("=" * 60)
        logger.info("PHASE 5.3: Migrating Grades (3.2M records)")
        logger.info("=" * 60)
        
        try:
            # Count total records
            with self.old_conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM journal_details WHERE active = 1")
                total_grades = cur.fetchone()[0]
                self.stats['grades']['total'] = total_grades
                logger.info(f"Found {total_grades:,} grades to migrate")
            
            # Process in batches
            batch_size = 10000
            offset = 0
            migrated_count = 0
            skipped_no_assessment = 0
            skipped_no_student = 0
            
            while offset < total_grades:
                with self.old_conn.cursor(
                    cursor_factory=RealDictCursor
                ) as cur:
                    cur.execute("""
                        SELECT
                            jd.id, jd.journal_id, jd.point_id_1,
                            jd.status_1,
                            jd.create_date, jd.update_date,
                            j.course_id, j.student_id, j.course_eva_id
                        FROM journal_details jd
                        JOIN journal j ON jd.journal_id = j.id
                        WHERE jd.active = 1
                        ORDER BY jd.id
                        LIMIT %s OFFSET %s
                    """, (batch_size, offset))
                    
                    batch_grades = cur.fetchall()
                    
                    if not batch_grades:
                        break
                    
                    grade_values = []
                    for grade in batch_grades:
                        grade_uuid = str(uuid.uuid4())
                        
                        # Map to assessment
                        assessment_key = (
                            grade['course_id'],
                            grade['course_eva_id']
                        )
                        assessment_uuid = self.id_mappings.get(
                            'assessments', {}
                        ).get(assessment_key)
                        
                        # Map to student
                        student_uuid = self.id_mappings.get(
                            'students', {}
                        ).get(grade['student_id'])
                        
                        if not assessment_uuid:
                            skipped_no_assessment += 1
                            continue
                        
                        if not student_uuid:
                            skipped_no_student += 1
                            continue
                        
                        # Extract grade value
                        # Simplified - in production lookup in dictionaries
                        marks = 0.0
                        if grade['point_id_1']:
                            # Simple extraction - can be improved
                            marks = float(grade['point_id_1'] % 100)
                        
                        percentage = marks
                        
                        # Calculate letter grade
                        if percentage >= 90:
                            letter_grade = 'A'
                        elif percentage >= 80:
                            letter_grade = 'B'
                        elif percentage >= 70:
                            letter_grade = 'C'
                        elif percentage >= 60:
                            letter_grade = 'D'
                        else:
                            letter_grade = 'F'
                        
                        grade_values.append((
                            grade_uuid,
                            assessment_uuid,
                            student_uuid,
                            None,  # submission_id
                            None,  # graded_by
                            marks,
                            percentage,
                            letter_grade,
                            None,  # feedback
                            None,  # rubric_scores
                            True,  # is_final
                            grade['update_date'],  # graded_at
                            None,  # approved_by
                            None,  # approved_at
                            None,  # grade_history
                            grade['create_date'] or datetime.now(),
                            datetime.now()
                        ))
                    
                    # Insert batch
                    if grade_values:
                        insert_query = """
                            INSERT INTO grades (
                                id, assessment_id, student_id, submission_id,
                                graded_by, marks_obtained, percentage,
                                letter_grade, feedback, rubric_scores,
                                is_final, graded_at, approved_by, approved_at,
                                grade_history, created_at, updated_at
                            ) VALUES %s
                            ON CONFLICT (id) DO NOTHING
                        """
                        
                        with self.new_conn.cursor() as new_cur:
                            execute_values(new_cur, insert_query, grade_values)
                            self.new_conn.commit()
                        
                        migrated_count += len(grade_values)
                        self.stats['grades']['migrated'] = migrated_count
                
                offset += batch_size
                progress = (offset / total_grades) * 100
                logger.info(
                    f"  Progress: {migrated_count:,}/{total_grades:,} "
                    f"({progress:.1f}%)"
                )
            
            logger.info(f"✓ Migrated {migrated_count:,} grades")
            if skipped_no_assessment > 0:
                logger.info(
                    f"Skipped {skipped_no_assessment:,} grades "
                    "(no assessment mapping)"
                )
            if skipped_no_student > 0:
                logger.info(
                    f"Skipped {skipped_no_student:,} grades "
                    "(no student mapping)"
                )

            
        except Exception as e:
            logger.error(f"Grade migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate_migration(self):
        """Run validation queries to ensure data integrity"""
        logger.info("=" * 60)
        logger.info("VALIDATING MIGRATION")
        logger.info("=" * 60)
        
        validations = []
        
        with self.old_conn.cursor(cursor_factory=RealDictCursor) as old_cur, \
             self.new_conn.cursor(cursor_factory=RealDictCursor) as new_cur:
            
            # Validate user counts
            old_cur.execute("SELECT COUNT(*) as count FROM users")
            old_users = old_cur.fetchone()['count']
            
            new_cur.execute("SELECT COUNT(*) as count FROM users")
            new_users = new_cur.fetchone()['count']
            
            validations.append({
                'check': 'User Count',
                'old': old_users,
                'new': new_users,
                'match': old_users == new_users
            })
            
            # Validate student counts
            old_cur.execute("SELECT COUNT(*) as count FROM students")
            old_students = old_cur.fetchone()['count']
            
            new_cur.execute("SELECT COUNT(*) as count FROM students")
            new_students = new_cur.fetchone()['count']
            
            validations.append({
                'check': 'Student Count',
                'old': old_students,
                'new': new_students,
                'match': old_students == new_students
            })
            
            # Validate teacher counts
            old_cur.execute("SELECT COUNT(*) as count FROM teachers")
            old_teachers = old_cur.fetchone()['count']
            
            new_cur.execute("SELECT COUNT(*) as count FROM staff_members")
            new_staff = new_cur.fetchone()['count']
            
            validations.append({
                'check': 'Staff Count',
                'old': old_teachers,
                'new': new_staff,
                'match': old_teachers == new_staff
            })
            
            # Check for orphaned records
            new_cur.execute("""
                SELECT COUNT(*) as count
                FROM students s
                LEFT JOIN users u ON s.user_id = u.id
                WHERE u.id IS NULL
            """)
            orphaned_students = new_cur.fetchone()['count']
            
            validations.append({
                'check': 'Orphaned Students',
                'old': 0,
                'new': orphaned_students,
                'match': orphaned_students == 0
            })
        
        # Print validation results
        logger.info("\n" + "=" * 60)
        logger.info("VALIDATION RESULTS")
        logger.info("=" * 60)
        
        for v in validations:
            status = "✓ PASS" if v['match'] else "✗ FAIL"
            logger.info(f"{status} | {v['check']}: Old={v['old']}, New={v['new']}")
        
        return all(v['match'] for v in validations)
    
    def print_statistics(self):
        """Print migration statistics"""
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION STATISTICS")
        logger.info("=" * 60)
        
        for entity, stats in self.stats.items():
            success_rate = (stats['migrated'] / stats['total'] * 100) if stats['total'] > 0 else 0
            logger.info(f"{entity.upper():20} | Total: {stats['total']:6} | Migrated: {stats['migrated']:6} | Failed: {stats['failed']:6} | Success: {success_rate:5.1f}%")
    
    def run_migration(self, phase: str = 'all'):
        """
        Run migration based on phase
        
        Args:
            phase: Migration phase ('all', '1', '2', '3', '4', '5')
        """
        try:
            self.connect_databases()
            
            if phase == 'all' or phase == '1':
                self.migrate_users()
                self.migrate_persons()
            
            if phase == 'all' or phase == '2':
                self.migrate_students()
                self.migrate_staff()
            
            if phase == 'all' or phase == '3':
                self.migrate_organizations()
                self.migrate_academic_terms()
            
            if phase == 'all' or phase == '4':
                self.migrate_courses()
                self.migrate_course_offerings()
                self.migrate_course_instructors()
            
            if phase == 'all' or phase == '5':
                self.migrate_enrollments()
                self.migrate_assessments()
                self.migrate_grades()
            
            # Print statistics
            self.print_statistics()
            
            logger.info("\n" + "=" * 60)
            logger.info("MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.close_connections()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Education System Database Migration')
    parser.add_argument('--phase', default='all', choices=['all', '1', '2', '3', '4', '5'],
                       help='Migration phase to run')
    parser.add_argument('--validate', action='store_true',
                       help='Run validation only')
    
    args = parser.parse_args()
    
    migration = DatabaseMigration()
    
    try:
        if args.validate:
            migration.connect_databases()
            validation_passed = migration.validate_migration()
            migration.close_connections()
            
            if validation_passed:
                logger.info("\n✓ All validations passed!")
                sys.exit(0)
            else:
                logger.error("\n✗ Some validations failed!")
                sys.exit(1)
        else:
            migration.run_migration(args.phase)
    
    except KeyboardInterrupt:
        logger.warning("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nMigration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
