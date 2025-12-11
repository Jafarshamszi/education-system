#!/usr/bin/env python3
"""
Analyze unmigrated records and complete 100% migration
Targets the remaining records from:
- Exams: 99.9% → 100%
- Course Materials: 97.3% → 100%
- Class Schedules: 96.3% → 100%
- Exam Submissions: 95.8% → 100%
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import sys

class CompleteMigration:
    def __init__(self):
        self.old_conn = None
        self.new_conn = None
        self.stats = {
            'exams': {'total': 0, 'migrated': 0, 'can_migrate': 0, 'cannot': 0},
            'schedules': {'total': 0, 'migrated': 0, 'can_migrate': 0, 'cannot': 0},
            'materials': {'total': 0, 'migrated': 0, 'can_migrate': 0, 'cannot': 0},
            'submissions': {'total': 0, 'migrated': 0, 'can_migrate': 0, 'cannot': 0}
        }
    
    def connect_databases(self):
        """Connect to both old and new databases"""
        try:
            self.old_conn = psycopg2.connect(
                dbname='edu',
                user='postgres',
                password='1111',
                host='localhost',
                port='5432'
            )
            self.new_conn = psycopg2.connect(
                dbname='lms',
                user='postgres',
                password='1111',
                host='localhost',
                port='5432'
            )
            print("✓ Connected to both databases")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            sys.exit(1)
    
    def analyze_unmigrated_exams(self):
        """Find and analyze unmigrated exams"""
        print("\n" + "=" * 80)
        print("1. ANALYZING UNMIGRATED EXAMS")
        print("=" * 80)
        
        old_cur = self.old_conn.cursor(cursor_factory=RealDictCursor)
        new_cur = self.new_conn.cursor(cursor_factory=RealDictCursor)
        
        # Get total exams
        old_cur.execute("SELECT COUNT(*) as count FROM exam WHERE active = 1")
        total = old_cur.fetchone()['count']
        
        # Get migrated exam IDs
        new_cur.execute("""
            SELECT rubric->>'old_exam_id' as old_exam_id 
            FROM assessments 
            WHERE assessment_type = 'exam' AND rubric IS NOT NULL
        """)
        migrated_ids = {row['old_exam_id'] for row in new_cur.fetchall()}
        
        self.stats['exams']['total'] = total
        self.stats['exams']['migrated'] = len(migrated_ids)
        
        print(f"Total active exams: {total}")
        print(f"Already migrated: {len(migrated_ids)}")
        print(f"Missing: {total - len(migrated_ids)}")
        
        # Find unmigrated exams
        old_cur.execute("""
            SELECT e.id, e.course_id, e.start_date, e.start_time, e.duration,
                   e.passing_grade, e.type_id, e.end_time,
                   c.code as course_code
            FROM exam e
            LEFT JOIN course c ON e.course_id = c.id
            WHERE e.active = 1
        """)
        
        unmigrated_exams = []
        for exam in old_cur.fetchall():
            if str(exam['id']) not in migrated_ids:
                # Check if offering exists
                section_code = exam['course_code'][:20] if exam['course_code'] else None
                if section_code:
                    new_cur.execute("""
                        SELECT id FROM course_offerings WHERE section_code = %s
                    """, (section_code,))
                    offering = new_cur.fetchone()
                    if offering:
                        exam['offering_id'] = offering['id']
                        unmigrated_exams.append(exam)
                        self.stats['exams']['can_migrate'] += 1
                        print(f"  ✓ Exam {exam['id']}: Can migrate (has offering)")
                    else:
                        self.stats['exams']['cannot'] += 1
                        print(f"  ✗ Exam {exam['id']}: No offering for '{section_code}'")
                else:
                    self.stats['exams']['cannot'] += 1
                    print(f"  ✗ Exam {exam['id']}: No course code")
        
        old_cur.close()
        new_cur.close()
        return unmigrated_exams
    
    def analyze_unmigrated_schedules(self):
        """Find and analyze unmigrated class schedules"""
        print("\n" + "=" * 80)
        print("2. ANALYZING UNMIGRATED CLASS SCHEDULES")
        print("=" * 80)
        
        old_cur = self.old_conn.cursor(cursor_factory=RealDictCursor)
        new_cur = self.new_conn.cursor(cursor_factory=RealDictCursor)
        
        # Get totals
        old_cur.execute("SELECT COUNT(*) as count FROM course_meeting WHERE active = 1")
        total = old_cur.fetchone()['count']
        
        new_cur.execute("SELECT COUNT(*) as count FROM class_schedules")
        migrated = new_cur.fetchone()['count']
        
        self.stats['schedules']['total'] = total
        self.stats['schedules']['migrated'] = migrated
        
        print(f"Total active meetings: {total}")
        print(f"Already migrated: {migrated}")
        print(f"Missing: {total - migrated}")
        
        # Build existing schedule tracking
        new_cur.execute("""
            SELECT course_offering_id, day_of_week, start_time, end_time
            FROM class_schedules
        """)
        existing_schedules = set()
        for row in new_cur.fetchall():
            key = (str(row['course_offering_id']), row['day_of_week'], 
                   str(row['start_time']), str(row['end_time']))
            existing_schedules.add(key)
        
        print(f"Loaded {len(existing_schedules)} existing schedule signatures")
        
        # Build offering mappings
        new_cur.execute("SELECT id, section_code FROM course_offerings")
        offerings_by_section = {row['section_code']: row['id'] for row in new_cur.fetchall()}
        
        # Get time slot mappings
        new_cur.execute("SELECT id, start_time, end_time FROM time_slots ORDER BY id")
        time_slots = list(new_cur.fetchall())
        
        # Get all meetings
        old_cur.execute("""
            SELECT cm.id, cm.course_id, cm.week_day, cm.start_time_slot_id, 
                   cm.end_time_slot_id, cm.room_id, c.code as course_code
            FROM course_meeting cm
            LEFT JOIN course c ON cm.course_id = c.id
            WHERE cm.active = 1
            ORDER BY cm.id
        """)
        
        unmigrated_schedules = []
        sample_count = 0
        
        for meeting in old_cur.fetchall():
            section_code = meeting['course_code'][:20] if meeting['course_code'] else None
            if not section_code or section_code not in offerings_by_section:
                self.stats['schedules']['cannot'] += 1
                continue
            
            offering_id = offerings_by_section[section_code]
            
            # Normalize day
            raw_day = meeting['week_day'] if meeting['week_day'] is not None else 1
            day_of_week = raw_day % 7 if raw_day >= 0 else 0
            
            # Get time slots
            start_slot_idx = (meeting['start_time_slot_id'] - 1) if meeting['start_time_slot_id'] else 0
            end_slot_idx = (meeting['end_time_slot_id'] - 1) if meeting['end_time_slot_id'] else 0
            
            if 0 <= start_slot_idx < len(time_slots) and 0 <= end_slot_idx < len(time_slots):
                start_time = time_slots[start_slot_idx]['start_time']
                end_time = time_slots[end_slot_idx]['end_time']
                
                # Check if already exists
                schedule_key = (str(offering_id), day_of_week, str(start_time), str(end_time))
                if schedule_key not in existing_schedules:
                    unmigrated_schedules.append({
                        'offering_id': offering_id,
                        'day_of_week': day_of_week,
                        'start_time': start_time,
                        'end_time': end_time,
                        'room_id': meeting['room_id']
                    })
                    self.stats['schedules']['can_migrate'] += 1
                    
                    if sample_count < 10:
                        print(f"  ✓ Meeting {meeting['id']}: Can migrate (new schedule)")
                        sample_count += 1
        
        print(f"\nFound {len(unmigrated_schedules)} unique schedules to migrate")
        
        old_cur.close()
        new_cur.close()
        return unmigrated_schedules
    
    def analyze_unmigrated_materials(self):
        """Find and analyze unmigrated course materials"""
        print("\n" + "=" * 80)
        print("3. ANALYZING UNMIGRATED COURSE MATERIALS")
        print("=" * 80)
        
        old_cur = self.old_conn.cursor(cursor_factory=RealDictCursor)
        new_cur = self.new_conn.cursor(cursor_factory=RealDictCursor)
        
        # Get totals
        old_cur.execute("SELECT COUNT(*) as count FROM course_meeting_topic_file WHERE active = 1")
        total = old_cur.fetchone()['count']
        
        new_cur.execute("SELECT COUNT(*) as count FROM course_materials")
        migrated = new_cur.fetchone()['count']
        
        self.stats['materials']['total'] = total
        self.stats['materials']['migrated'] = migrated
        
        print(f"Total active materials: {total}")
        print(f"Already migrated: {migrated}")
        print(f"Missing: {total - migrated}")
        
        # Build existing materials tracking
        new_cur.execute("SELECT metadata->>'old_topic_file_id' as old_id FROM course_materials WHERE metadata IS NOT NULL")
        migrated_ids = {row['old_id'] for row in new_cur.fetchall() if row['old_id']}
        
        print(f"Loaded {len(migrated_ids)} migrated material IDs")
        
        # Build mappings
        new_cur.execute("SELECT id, section_code FROM course_offerings")
        offerings_by_section = {row['section_code']: row['id'] for row in new_cur.fetchall()}
        
        # Get unmigrated materials
        old_cur.execute("""
            SELECT cmtf.id, cmtf.file_id, cmtf.course_meeting_topic_id,
                   cm.course_id, c.code as course_code,
                   f.path, f.type, f.size, f.author_name
            FROM course_meeting_topic_file cmtf
            JOIN course_meeting_topic cmt ON cmtf.course_meeting_topic_id = cmt.id
            JOIN course_meeting cm ON cmt.course_meeting_id = cm.id
            JOIN course c ON cm.course_id = c.id
            LEFT JOIN files f ON cmtf.file_id = f.id
            WHERE cmtf.active = 1
            ORDER BY cmtf.id
        """)
        
        unmigrated_materials = []
        sample_count = 0
        
        for mat in old_cur.fetchall():
            if str(mat['id']) in migrated_ids:
                continue
            
            section_code = mat['course_code'][:20] if mat['course_code'] else None
            if section_code and section_code in offerings_by_section:
                offering_id = offerings_by_section[section_code]
                
                # Determine material type
                file_type = (mat['type'] or '').lower()
                if 'video' in file_type or 'mp4' in file_type:
                    material_type = 'video'
                elif 'quiz' in file_type or 'test' in file_type:
                    material_type = 'quiz'
                elif 'assignment' in file_type or 'homework' in file_type:
                    material_type = 'assignment'
                elif 'lecture' in file_type or 'ppt' in file_type or 'presentation' in file_type:
                    material_type = 'lecture'
                else:
                    material_type = 'reading'
                
                unmigrated_materials.append({
                    'offering_id': offering_id,
                    'material_type': material_type,
                    'old_id': mat['id'],
                    'file_id': mat['file_id'],
                    'path': mat['path'],
                    'file_type': mat['type'],
                    'size': mat['size'],
                    'author': mat['author_name']
                })
                self.stats['materials']['can_migrate'] += 1
                
                if sample_count < 10:
                    print(f"  ✓ Material {mat['id']}: Can migrate (has offering)")
                    sample_count += 1
            else:
                self.stats['materials']['cannot'] += 1
        
        print(f"\nFound {len(unmigrated_materials)} materials to migrate")
        
        old_cur.close()
        new_cur.close()
        return unmigrated_materials
    
    def analyze_unmigrated_submissions(self):
        """Find and analyze unmigrated exam submissions"""
        print("\n" + "=" * 80)
        print("4. ANALYZING UNMIGRATED EXAM SUBMISSIONS")
        print("=" * 80)
        
        old_cur = self.old_conn.cursor(cursor_factory=RealDictCursor)
        new_cur = self.new_conn.cursor(cursor_factory=RealDictCursor)
        
        # Get totals
        old_cur.execute("SELECT COUNT(*) as count FROM exam_student WHERE active = 1")
        total = old_cur.fetchone()['count']
        
        new_cur.execute("SELECT COUNT(*) as count FROM assessment_submissions")
        migrated = new_cur.fetchone()['count']
        
        self.stats['submissions']['total'] = total
        self.stats['submissions']['migrated'] = migrated
        
        print(f"Total active submissions: {total}")
        print(f"Already migrated: {migrated}")
        print(f"Missing: {total - migrated}")
        
        # Build mappings
        new_cur.execute("""
            SELECT id, rubric->>'old_exam_id' as old_exam_id
            FROM assessments 
            WHERE assessment_type = 'exam' AND rubric IS NOT NULL
        """)
        exam_mappings = {row['old_exam_id']: row['id'] for row in new_cur.fetchall() if row['old_exam_id']}
        
        new_cur.execute("""
            SELECT id, metadata->>'old_student_id' as old_student_id
            FROM students WHERE metadata IS NOT NULL
        """)
        student_mappings = {row['old_student_id']: row['id'] 
                           for row in new_cur.fetchall() if row['old_student_id']}
        
        print(f"Loaded {len(exam_mappings)} exam mappings")
        print(f"Loaded {len(student_mappings)} student mappings")
        
        # Track existing submissions
        new_cur.execute("""
            SELECT assessment_id, student_id, attempt_number
            FROM assessment_submissions
        """)
        existing_submissions = {(str(row['assessment_id']), str(row['student_id']), row['attempt_number'])
                               for row in new_cur.fetchall()}
        
        print(f"Loaded {len(existing_submissions)} existing submissions")
        
        # Get unmigrated submissions
        old_cur.execute("""
            SELECT id, exam_id, student_id, finish_status, submit_date, grade
            FROM exam_student
            WHERE active = 1
            ORDER BY exam_id, student_id, id
        """)
        
        unmigrated_submissions = []
        attempt_tracker = {}
        no_exam = 0
        no_student = 0
        already_exists = 0
        sample_count = 0
        
        for sub in old_cur.fetchall():
            exam_id_str = str(sub['exam_id'])
            student_id_str = str(sub['student_id'])
            
            if exam_id_str not in exam_mappings:
                no_exam += 1
                continue
            
            if student_id_str not in student_mappings:
                no_student += 1
                continue
            
            assessment_id = exam_mappings[exam_id_str]
            student_id = student_mappings[student_id_str]
            
            # Track attempt number
            key = (exam_id_str, student_id_str)
            attempt_tracker[key] = attempt_tracker.get(key, 0) + 1
            attempt_number = attempt_tracker[key]
            
            # Check if already exists
            submission_key = (str(assessment_id), str(student_id), attempt_number)
            if submission_key in existing_submissions:
                already_exists += 1
                continue
            
            # Map status
            status_map = {1: 'submitted', 2: 'graded', 3: 'returned'}
            status = status_map.get(sub['finish_status'], 'submitted')
            
            unmigrated_submissions.append({
                'assessment_id': assessment_id,
                'student_id': student_id,
                'attempt_number': attempt_number,
                'status': status,
                'submitted_at': sub['submit_date'],
                'score': sub['grade'] if sub['grade'] else None
            })
            self.stats['submissions']['can_migrate'] += 1
            
            if sample_count < 10:
                print(f"  ✓ Submission for exam {sub['exam_id']}, student {sub['student_id']}: Can migrate")
                sample_count += 1
        
        self.stats['submissions']['cannot'] = no_exam + no_student
        
        print(f"\nSkip reasons:")
        print(f"  - No exam mapping: {no_exam}")
        print(f"  - No student mapping: {no_student}")
        print(f"  - Already exists: {already_exists}")
        print(f"Found {len(unmigrated_submissions)} new submissions to migrate")
        
        old_cur.close()
        new_cur.close()
        return unmigrated_submissions
    
    def migrate_exams(self, exams):
        """Migrate remaining exams"""
        if not exams:
            print("\nNo exams to migrate")
            return 0
        
        print(f"\n{'='*80}")
        print(f"MIGRATING {len(exams)} EXAMS")
        print('='*80)
        
        new_cur = self.new_conn.cursor()
        migrated = 0
        
        for exam in exams:
            try:
                # Parse date
                if exam['start_date'] and '/' in exam['start_date']:
                    parts = exam['start_date'].split('/')
                    if len(parts) == 3:
                        day, month, year = parts
                        due_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        if exam['start_time']:
                            due_date += f" {exam['start_time']}"
                    else:
                        due_date = None
                else:
                    due_date = exam['start_date']
                
                rubric = {
                    'old_exam_id': exam['id'],
                    'type_id': exam['type_id'],
                    'start_date': exam['start_date'],
                    'start_time': exam['start_time'],
                    'end_time': exam['end_time']
                }
                
                new_cur.execute("""
                    INSERT INTO assessments (
                        course_offering_id, assessment_type, title, description,
                        total_marks, passing_marks, weight_percentage,
                        due_date, duration_minutes, instructions, rubric,
                        is_published, allows_late_submission,
                        created_at, updated_at
                    ) VALUES (
                        %s, 'exam', %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """, (
                    exam['offering_id'],
                    f"Exam {exam['id']}",
                    "Migrated exam",
                    100,
                    exam['passing_grade'] if exam['passing_grade'] else 50,
                    50,
                    due_date,
                    exam['duration'] if exam['duration'] else 60,
                    "Exam instructions",
                    json.dumps(rubric),
                    True,
                    False
                ))
                migrated += 1
                print(f"  ✓ Migrated exam {exam['id']}")
                
            except Exception as e:
                print(f"  ✗ Failed to migrate exam {exam['id']}: {e}")
        
        self.new_conn.commit()
        new_cur.close()
        print(f"\n✓ Migrated {migrated}/{len(exams)} exams")
        return migrated
    
    def migrate_schedules(self, schedules):
        """Migrate remaining schedules"""
        if not schedules:
            print("\nNo schedules to migrate")
            return 0
        
        print(f"\n{'='*80}")
        print(f"MIGRATING {len(schedules)} CLASS SCHEDULES")
        print('='*80)
        
        new_cur = self.new_conn.cursor()
        migrated = 0
        batch_size = 5000
        
        for i in range(0, len(schedules), batch_size):
            batch = schedules[i:i+batch_size]
            
            try:
                values = []
                for sched in batch:
                    values.append(new_cur.mogrify("(%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                        (sched['offering_id'], sched['day_of_week'], sched['start_time'],
                         sched['end_time'], sched['room_id'], True)).decode('utf-8'))
                
                query = f"""
                    INSERT INTO class_schedules (
                        course_offering_id, day_of_week, start_time, end_time,
                        room_id, is_active, created_at, updated_at
                    ) VALUES {','.join(values)}
                    ON CONFLICT DO NOTHING
                """
                
                new_cur.execute(query)
                migrated += len(batch)
                print(f"  ✓ Migrated batch {i//batch_size + 1}: {len(batch)} schedules")
                
            except Exception as e:
                print(f"  ✗ Failed batch {i//batch_size + 1}: {e}")
        
        self.new_conn.commit()
        new_cur.close()
        print(f"\n✓ Migrated {migrated}/{len(schedules)} schedules")
        return migrated
    
    def migrate_materials(self, materials):
        """Migrate remaining materials"""
        if not materials:
            print("\nNo materials to migrate")
            return 0
        
        print(f"\n{'='*80}")
        print(f"MIGRATING {len(materials)} COURSE MATERIALS")
        print('='*80)
        
        new_cur = self.new_conn.cursor()
        migrated = 0
        batch_size = 1000
        
        for i in range(0, len(materials), batch_size):
            batch = materials[i:i+batch_size]
            
            try:
                values = []
                for mat in batch:
                    title = f"Material {mat['old_id']}"
                    metadata = {
                        'old_topic_file_id': mat['old_id'],
                        'old_file_id': mat['file_id'],
                        'file_path': mat['path'],
                        'file_type': mat['file_type'],
                        'file_size': mat['size'],
                        'author': mat['author']
                    }
                    
                    values.append(new_cur.mogrify(
                        "(%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                        (mat['offering_id'], mat['material_type'], title,
                         "Migrated course material", mat['path'],
                         json.dumps(metadata), True)
                    ).decode('utf-8'))
                
                query = f"""
                    INSERT INTO course_materials (
                        course_offering_id, material_type, title, description,
                        file_url, metadata, is_available, created_at, updated_at
                    ) VALUES {','.join(values)}
                    ON CONFLICT DO NOTHING
                """
                
                new_cur.execute(query)
                migrated += len(batch)
                print(f"  ✓ Migrated batch {i//batch_size + 1}: {len(batch)} materials")
                
            except Exception as e:
                print(f"  ✗ Failed batch {i//batch_size + 1}: {e}")
        
        self.new_conn.commit()
        new_cur.close()
        print(f"\n✓ Migrated {migrated}/{len(materials)} materials")
        return migrated
    
    def migrate_submissions(self, submissions):
        """Migrate remaining submissions"""
        if not submissions:
            print("\nNo submissions to migrate")
            return 0
        
        print(f"\n{'='*80}")
        print(f"MIGRATING {len(submissions)} EXAM SUBMISSIONS")
        print('='*80)
        
        new_cur = self.new_conn.cursor()
        migrated = 0
        batch_size = 5000
        
        for i in range(0, len(submissions), batch_size):
            batch = submissions[i:i+batch_size]
            
            try:
                values = []
                for sub in batch:
                    values.append(new_cur.mogrify(
                        "(%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                        (sub['assessment_id'], sub['student_id'], sub['attempt_number'],
                         sub['submitted_at'], sub['status'], sub['score'])
                    ).decode('utf-8'))
                
                query = f"""
                    INSERT INTO assessment_submissions (
                        assessment_id, student_id, attempt_number,
                        submitted_at, status, score,
                        created_at, updated_at
                    ) VALUES {','.join(values)}
                    ON CONFLICT (assessment_id, student_id, attempt_number) DO NOTHING
                """
                
                new_cur.execute(query)
                migrated += len(batch)
                print(f"  ✓ Migrated batch {i//batch_size + 1}: {len(batch)} submissions")
                
            except Exception as e:
                print(f"  ✗ Failed batch {i//batch_size + 1}: {e}")
        
        self.new_conn.commit()
        new_cur.close()
        print(f"\n✓ Migrated {migrated}/{len(submissions)} submissions")
        return migrated
    
    def print_summary(self):
        """Print final summary"""
        print("\n" + "=" * 80)
        print("FINAL MIGRATION SUMMARY")
        print("=" * 80)
        
        for category, stats in self.stats.items():
            total = stats['total']
            migrated = stats['migrated']
            can_migrate = stats['can_migrate']
            cannot = stats['cannot']
            
            final_count = migrated + can_migrate
            success_rate = (final_count / total * 100) if total > 0 else 0
            
            print(f"\n{category.upper()}:")
            print(f"  Total in old DB: {total:,}")
            print(f"  Previously migrated: {migrated:,}")
            print(f"  Newly migrated: {can_migrate:,}")
            print(f"  Cannot migrate: {cannot:,}")
            print(f"  Final total: {final_count:,}/{total:,} ({success_rate:.1f}%)")
    
    def run(self):
        """Run complete analysis and migration"""
        self.connect_databases()
        
        # Analyze all categories
        unmigrated_exams = self.analyze_unmigrated_exams()
        unmigrated_schedules = self.analyze_unmigrated_schedules()
        unmigrated_materials = self.analyze_unmigrated_materials()
        unmigrated_submissions = self.analyze_unmigrated_submissions()
        
        # Migrate remaining records
        print("\n" + "=" * 80)
        print("STARTING MIGRATION OF REMAINING RECORDS")
        print("=" * 80)
        
        self.migrate_exams(unmigrated_exams)
        self.migrate_schedules(unmigrated_schedules)
        self.migrate_materials(unmigrated_materials)
        self.migrate_submissions(unmigrated_submissions)
        
        # Print summary
        self.print_summary()
        
        self.old_conn.close()
        self.new_conn.close()

if __name__ == '__main__':
    migration = CompleteMigration()
    migration.run()
