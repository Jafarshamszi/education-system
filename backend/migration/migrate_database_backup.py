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
    'database': 'edu_test',
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
                for user in users:
                    if 'old_user_id' in user['metadata']:
                        old_id = user['metadata']['old_user_id']
                        self.id_mappings['users'][old_id] = user['id']
                
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
                
                # Load staff mappings if they exist
                cur.execute("""
                    SELECT id, metadata
                    FROM staff_members
                    WHERE metadata IS NOT NULL
                """)
                staff = cur.fetchall()
                if staff:
                    self.id_mappings['teachers'] = {}
                    for member in staff:
                        if 'old_teacher_id' in member['metadata']:
                            old_id = member['metadata']['old_teacher_id']
                            self.id_mappings['teachers'][old_id] = member['id']
                    logger.info(f"Loaded {len(self.id_mappings['teachers'])} existing staff mappings")
                
        except Exception as e:
            logger.warning(f"Could not load existing mappings: {e}")
            # Continue anyway - mappings will be built during migration
            self.new_conn = psycopg2.connect(**NEW_DB_CONFIG)
            logger.info("✓ Connected to new database")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
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
            # Generate organization UUID mapping
            org_mapping = self.generate_uuid_mapping('organizations')
            
            # Fetch organizations with dictionary names
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        o.id, o.parent_id, o.name_dictionary_id, o.code, o.active,
                        o.create_date, o.update_date,
                        d_az.value as name_az,
                        d_en.value as name_en,
                        d_ru.value as name_ru
                    FROM organizations o
                    LEFT JOIN dictionaries d_az ON o.name_dictionary_id = d_az.id AND d_az.language = 'az'
                    LEFT JOIN dictionaries d_en ON o.name_dictionary_id = d_en.id AND d_en.language = 'en'
                    LEFT JOIN dictionaries d_ru ON o.name_dictionary_id = d_ru.id AND d_ru.language = 'ru'
                    ORDER BY o.parent_id NULLS FIRST, o.id
                """)
                old_orgs = cur.fetchall()
            
            self.stats['organizations']['total'] = len(old_orgs)
            logger.info(f"Found {len(old_orgs)} organizations to migrate")
            
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
                    created_at, updated_at, metadata
                ) VALUES %s
            """
            
            values = []
            for org in old_orgs:
                org_type = determine_org_type(org, old_orgs)
                
                name_json = {
                    'az': org.get('name_az') or f"Organization {org['id']}",
                    'en': org.get('name_en') or org.get('name_az') or f"Organization {org['id']}",
                    'ru': org.get('name_ru') or org.get('name_az') or f"Organization {org['id']}"
                }
                
                values.append((
                    org_mapping[org['id']],
                    org_mapping[org['parent_id']] if org['parent_id'] and org['parent_id'] in org_mapping else None,
                    org_type,
                    org.get('code') or f"ORG{org['id']}",
                    json.dumps(name_json),
                    org.get('active', True),
                    org.get('create_date') or datetime.now(),
                    org.get('update_date') or datetime.now(),
                    json.dumps({
                        'old_id': org['id'],
                        'old_parent_id': org.get('parent_id'),
                        'migrated_at': datetime.now().isoformat()
                    })
                ))
            
            with self.new_conn.cursor() as cur:
                execute_values(cur, insert_query, values)
                self.new_conn.commit()
                self.stats['organizations']['migrated'] = len(values)
            
            logger.info(f"✓ Migrated {len(values)} organizations successfully")
            
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
            # Fetch all active subject catalog entries
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        id, subject_name_id, organization_id, active, note,
                        create_date, update_date
                    FROM subject_catalog
                    WHERE active = 1
                    ORDER BY id
                """)
                old_courses = cur.fetchall()
                
                self.stats['courses']['total'] = len(old_courses)
                logger.info(f"Found {len(old_courses)} courses to migrate")
                
                # Prepare course data with multilingual names
                course_values = []
                for course in old_courses:
                    course_uuid = str(uuid.uuid4())
                    self.id_mappings.setdefault('courses', {})[course['id']] = course_uuid
                    
                    # Fetch multilingual name
                    multilingual_name = self.get_multilingual_name(course['subject_name_id'], cur)
                    
                    # Map organization
                    org_uuid = self.id_mappings.get('organizations', {}).get(course['organization_id'])
                    
                    # Generate course code
                    course_code = f"SUBJ{course['id'] % 10000:04d}"
                    
                    course_values.append((
                        course_uuid,
                        course_code,
                        json.dumps(multilingual_name),
                        3.0,  # Default credit hours
                        org_uuid,
                        None,  # description
                        None,  # prerequisites
                        None,  # corequisites
                        None,  # syllabus_template
                        'active' if course['active'] == 1 else 'inactive',
                        json.dumps({"old_id": course['id'], "subject_name_id": course['subject_name_id']}),
                        course['create_date'] or datetime.now(),
                        course['update_date'] or datetime.now()
                    ))
            
            # Insert into new database
            insert_query = """
                INSERT INTO courses (
                    id, code, name, credit_hours, organization_unit_id,
                    description, prerequisites, corequisites, syllabus_template,
                    status, metadata, created_at, updated_at
                ) VALUES %s
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
            # Fetch all course offerings
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
                    LEFT JOIN education_plan_subject eps ON c.education_plan_subject_id = eps.id
                    WHERE c.active IN (0, 1)
                    ORDER BY c.id
                """)
                old_offerings = cur.fetchall()
                
                self.stats['course_offerings']['total'] = len(old_offerings)
                logger.info(f"Found {len(old_offerings)} course offerings to migrate")
                
                # Map semester + year to academic terms
                term_mapping = self.create_term_mapping(cur)
                
                offering_values = []
                for offering in old_offerings:
                    offering_uuid = str(uuid.uuid4())
                    self.id_mappings.setdefault('course_offerings', {})[offering['id']] = offering_uuid
                    
                    # Map to master course
                    subject_id = offering['subject_id'] or offering['education_plan_subject_id']
                    course_uuid = self.id_mappings.get('courses', {}).get(subject_id)
                    
                    # Map to academic term
                    term_key = (offering['semester_id'], offering['education_year_id'])
                    term_uuid = term_mapping.get(term_key)
                    
                    # Extract section code
                    section_code = offering['code'].split('_')[-1] if offering['code'] else f"S{offering['id'] % 1000:03d}"
                    
                    # Calculate total hours
                    total_hours = (offering['m_hours'] or 0) + (offering['s_hours'] or 0) + (offering['l_hours'] or 0) + (offering['fm_hours'] or 0)
                    
                    offering_values.append((
                        offering_uuid,
                        course_uuid,
                        term_uuid,
                        section_code[:20],
                        offering['student_count'] or 30,
                        'in_person',  # Default delivery mode
                        'active' if offering['active'] == 1 else 'inactive',
                        None,  # grading_scheme
                        json.dumps({
                            "old_id": offering['id'],
                            "code": offering['code'],
                            "lecture_hours": offering['m_hours'],
                            "seminar_hours": offering['s_hours'],
                            "lab_hours": offering['l_hours'],
                            "total_hours": total_hours
                        }),
                        offering['create_date'] or datetime.now(),
                        offering['update_date'] or datetime.now()
                    ))
            
            # Insert into new database
            insert_query = """
                INSERT INTO course_offerings (
                    id, course_id, academic_term_id, section_code, max_enrollment,
                    delivery_mode, status, grading_scheme, metadata,
                    created_at, updated_at
                ) VALUES %s
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
            # Fetch all course-teacher assignments
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        id, course_id, teacher_id, lesson_type_id, active,
                        create_date, update_date
                    FROM course_teacher
                    WHERE active = 1
                    ORDER BY id
                """)
                old_instructors = cur.fetchall()
                
                logger.info(f"Found {len(old_instructors)} course-instructor assignments to migrate")
                
                instructor_values = []
                for instructor in old_instructors:
                    instructor_uuid = str(uuid.uuid4())
                    
                    # Map to course offering
                    offering_uuid = self.id_mappings.get('course_offerings', {}).get(instructor['course_id'])
                    
                    # Map to staff member
                    staff_uuid = self.id_mappings.get('staff_members', {}).get(instructor['teacher_id'])
                    
                    if not offering_uuid or not staff_uuid:
                        continue  # Skip if mapping missing
                    
                    # Map lesson type to role
                    lesson_type = instructor['lesson_type_id']
                    if lesson_type == 110000111:
                        role = 'primary'
                    elif lesson_type == 110000112:
                        role = 'secondary'
                    else:
                        role = 'assistant'
                    
                    instructor_values.append((
                        instructor_uuid,
                        offering_uuid,
                        staff_uuid,
                        role,
                        instructor['create_date'] or datetime.now(),
                        datetime.now()
                    ))
            
            # Insert into new database
            insert_query = """
                INSERT INTO course_instructors (
                    id, course_offering_id, instructor_id, instructor_role,
                    assigned_at, updated_at
                ) VALUES %s
            """
            
            with self.new_conn.cursor() as cur:
                execute_values(cur, insert_query, instructor_values)
                self.new_conn.commit()
            
            logger.info(f"✓ Migrated {len(instructor_values)} course instructor assignments")
            
        except Exception as e:
            logger.error(f"Course instructor migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    # ========================================================================
    # PHASE 5: ENROLLMENTS AND GRADES
    # ========================================================================
    
    def migrate_enrollments(self):
        """Migrate course_student + education_group_student → course_enrollments"""
        logger.info("=" * 60)
        logger.info("PHASE 5.1: Migrating Course Enrollments")
        logger.info("=" * 60)
        
        try:
            enrolled_students = set()  # Track to avoid duplicates
            enrollment_values = []
            
            # First: Migrate direct course enrollments
            with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        id, course_id, student_id, active,
                        create_date, update_date
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
                    
                    if not offering_uuid or not student_uuid:
                        continue
                    
                    # Track enrollment
                    enrolled_students.add((offering_uuid, student_uuid))
                    
                    enrollment_values.append((
                        enrollment_uuid,
                        offering_uuid,
                        student_uuid,
                        'enrolled' if enrollment['active'] == 1 else 'dropped',
                        enrollment['create_date'] or datetime.now(),
                        None,  # completion_date
                        None,  # grade (filled later)
                        None,  # gpa_points
                        False,  # is_retake
                        json.dumps({"old_id": enrollment['id'], "source": "course_student"}),
                        enrollment['create_date'] or datetime.now(),
                        datetime.now()
                    ))
                
                # Second: Migrate group-based enrollments
                # (Skip for now to avoid complexity - can add later if needed)
                
                self.stats['enrollments']['total'] = len(course_students)
                self.stats['enrollments']['migrated'] = len(enrollment_values)
            
            # Insert into new database in batches
            insert_query = """
                INSERT INTO course_enrollments (
                    id, course_offering_id, student_id, enrollment_status,
                    enrollment_date, completion_date, grade, gpa_points,
                    is_retake, metadata, created_at, updated_at
                ) VALUES %s
            """
            
            batch_size = 5000
            for i in range(0, len(enrollment_values), batch_size):
                batch = enrollment_values[i:i+batch_size]
                with self.new_conn.cursor() as cur:
                    execute_values(cur, insert_query, batch)
                    self.new_conn.commit()
                logger.info(f"  Inserted batch {i//batch_size + 1}/{(len(enrollment_values)-1)//batch_size + 1}")
            
            logger.info(f"✓ Migrated {len(enrollment_values)} enrollments")
            
        except Exception as e:
            logger.error(f"Enrollment migration failed: {e}")
            self.new_conn.rollback()
            raise
    
    def migrate_assessments(self):
        """Migrate journal → assessments"""
        logger.info("=" * 60)
        logger.info("PHASE 5.2: Migrating Assessments")
        logger.info("=" * 60)
        
        try:
            # Group journal entries by course_id + course_eva_id to create assessments
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
                
                logger.info(f"Found {len(assessment_groups)} unique assessments")
                
                assessment_values = []
                for assessment in assessment_groups:
                    assessment_uuid = str(uuid.uuid4())
                    
                    # Map to course offering
                    offering_uuid = self.id_mappings.get('course_offerings', {}).get(assessment['course_id'])
                    
                    if not offering_uuid:
                        continue
                    
                    # Store mapping for grades migration
                    key = (assessment['course_id'], assessment['course_eva_id'])
                    self.id_mappings.setdefault('assessments', {})[key] = assessment_uuid
                    
                    # Determine assessment type
                    eva_id = assessment['course_eva_id']
                    if eva_id and 'exam' in str(eva_id).lower():
                        assessment_type = 'exam'
                        weight = 40.0
                    elif eva_id and 'quiz' in str(eva_id).lower():
                        assessment_type = 'quiz'
                        weight = 10.0
                    else:
                        assessment_type = 'assignment'
                        weight = 20.0
                    
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
                        assessment_type,
                        weight,
                        100.0,  # total_marks
                        assessment['update_date'],  # due_date
                        None,  # instructions
                        None,  # rubric
                        'active',
                        json.dumps({"course_eva_id": eva_id}),
                        assessment['create_date'] or datetime.now(),
                        datetime.now()
                    ))
            
            # Insert into new database
            insert_query = """
                INSERT INTO assessments (
                    id, course_offering_id, title, assessment_type, weight_percentage,
                    total_marks, due_date, instructions, rubric, status, metadata,
                    created_at, updated_at
                ) VALUES %s
            """
            
            with self.new_conn.cursor() as cur:
                execute_values(cur, insert_query, assessment_values)
                self.new_conn.commit()
            
            logger.info(f"✓ Migrated {len(assessment_values)} assessments")
            
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
            
            while offset < total_grades:
                with self.old_conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            jd.id, jd.journal_id, jd.point_id_1, jd.status_1,
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
                        assessment_key = (grade['course_id'], grade['course_eva_id'])
                        assessment_uuid = self.id_mappings.get('assessments', {}).get(assessment_key)
                        
                        # Map to student
                        student_uuid = self.id_mappings.get('students', {}).get(grade['student_id'])
                        
                        if not assessment_uuid or not student_uuid:
                            continue
                        
                        # Extract grade value (simplified - need actual dictionary lookup)
                        marks = 0.0
                        if grade['point_id_1']:
                            # In production, lookup in dictionaries table
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
                            marks,
                            percentage,
                            letter_grade,
                            None,  # submitted_at
                            grade['update_date'],  # graded_at
                            None,  # graded_by
                            None,  # feedback
                            None,  # rubric_scores
                            True,  # is_final
                            None,  # grade_history
                            json.dumps({"old_id": grade['id'], "point_id": grade['point_id_1']}),
                            grade['create_date'] or datetime.now(),
                            datetime.now()
                        ))
                    
                    # Insert batch
                    if grade_values:
                        insert_query = """
                            INSERT INTO grades (
                                id, assessment_id, student_id, marks_obtained, percentage,
                                letter_grade, submitted_at, graded_at, graded_by, feedback,
                                rubric_scores, is_final, grade_history, metadata,
                                created_at, updated_at
                            ) VALUES %s
                        """
                        
                        with self.new_conn.cursor() as new_cur:
                            execute_values(new_cur, insert_query, grade_values)
                            self.new_conn.commit()
                        
                        migrated_count += len(grade_values)
                        self.stats['grades']['migrated'] = migrated_count
                
                offset += batch_size
                progress = (offset / total_grades) * 100
                logger.info(f"  Progress: {migrated_count:,}/{total_grades:,} ({progress:.1f}%)")
            
            logger.info(f"✓ Migrated {migrated_count:,} grades")
            
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
