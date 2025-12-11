# DATABASE STRUCTURES - EDU (Old) vs LMS (New)

**Analysis Date:** October 5, 2025  
**Purpose:** Complete understanding of both database structures for future development

---

## OLD DATABASE: EDU

### Connection Info
- **Host:** localhost
- **Port:** 5432
- **Database:** edu
- **User:** postgres
- **Password:** 1111
- **Total Tables:** 355+ tables

### Key Tables & Structure

#### 1. USERS & AUTHENTICATION

**accounts** (6,525 records)
```sql
- id: bigint (PK)
- user_id: bigint → users.id
- person_id: bigint → persons.id
- active: smallint (1=active, 0=inactive)
- password: text (base64 encoded)
- email: text
- create_date, update_date: timestamp
```

**users** (6,987 records)
```sql
- id: bigint (PK)
- username: text
- email: text
- role_id: bigint
- active: smallint
```

**persons** (6,523 records)
```sql
- id: bigint (PK)
- name: text
- surname: text
- patronymic: text
- birth_date: text (format: DD/MM/YYYY)
- gender_id: bigint → dictionaries
- photo: text (file path)
- phone: text
- email: text
```

**Key Pattern:** 
- Old DB uses JOIN table (accounts) to link users + persons
- Uses bigint for all IDs
- Dates stored as text in DD/MM/YYYY format
- Multilingual data in separate `dictionaries` table

---

#### 2. STUDENTS

**students** (6,507 total, 6,344 active)
```sql
- id: bigint (PK)
- person_id: bigint → persons.id
- user_id: bigint → users.id
- org_id: bigint → organizations.id
- education_line_id: bigint (bachelor/master)
- education_type_id: bigint (full-time/part-time)
- education_payment_type_id: bigint (paid/free)
- education_lang_id: bigint (az/en/ru)
- score: text (entrance exam score, e.g., "675")
- card_number: text (student card ID)
- status: bigint (enrollment status)
- active: smallint (1=active, 0=inactive)
- create_date, update_date: timestamp
```

**education_group** (419 groups)
```sql
- id: bigint (PK)
- group_code: text (e.g., "B03.1", "M02.2")
- org_id: bigint
- education_line_id: bigint
- active: smallint
```

---

#### 3. TEACHERS

**teachers** (464 total, 424 active)
```sql
- id: bigint (PK)
- person_id: bigint → persons.id
- kafedra_id: bigint → kafedra.id (department)
- degree_id: bigint → dictionaries (PhD, Prof, etc.)
- rank_id: bigint → dictionaries (academic rank)
- position_id: bigint → dictionaries (position title)
- employment_type_id: bigint (full-time/part-time)
- hire_date: timestamp
- active: smallint
```

**kafedra** (departments/units)
```sql
- id: bigint (PK)
- name_id: bigint → dictionaries (multilingual name)
- org_id: bigint → organizations.id
- active: smallint
```

---

#### 4. ORGANIZATIONS

**organizations** (60 records)
```sql
- id: bigint (PK)
- name_id: bigint → dictionaries
- short_name_id: bigint → dictionaries
- parent_id: bigint → organizations.id (self-reference)
- org_type_id: bigint (faculty, department, etc.)
- active: smallint
```

**dictionaries** (multilingual lookup table)
```sql
- id: bigint (PK)
- name_az: text (Azerbaijani)
- name_en: text (English)
- name_ru: text (Russian)
- dict_type: text (type of dictionary entry)
```

---

#### 5. COURSES & OFFERINGS

**subject_catalog** (895 subjects, 883 active)
```sql
- id: bigint (PK)
- subject_name_id: bigint → dictionaries
- organization_id: bigint → organizations.id
- credits: integer
- hours_total: integer
- hours_lecture: integer
- hours_seminar: integer
- hours_lab: integer
- active: smallint
```

**education_plan** (141 programs)
```sql
- id: bigint (PK)
- name_id: bigint → dictionaries
- org_id: bigint → organizations.id
- education_line_id: bigint (bachelor/master)
- education_type_id: bigint
- active: smallint
```

**education_plan_subject** (curriculum mapping)
```sql
- id: bigint (PK)
- education_plan_id: bigint → education_plan.id
- subject_catalog_id: bigint → subject_catalog.id
- semester_number: integer (1-8)
- is_required: boolean
- credits: integer
```

**course** (8,391 total, 6,020 active) - COURSE INSTANCES
```sql
- id: bigint (PK)
- code: text (e.g., "2024/2025_PY_HF-B03.1_2724")
- education_plan_subject_id: bigint → education_plan_subject.id
- semester_id: bigint → dictionaries (Fall/Spring)
- education_year_id: bigint (academic year)
- teacher_id: bigint → teachers.id (primary instructor)
- m_hours: integer (lecture hours)
- s_hours: integer (seminar hours)
- l_hours: integer (lab hours)
- student_count: smallint
- active: smallint
```

**course_teacher** (13,605 assignments)
```sql
- id: bigint (PK)
- course_id: bigint → course.id
- teacher_id: bigint → teachers.id
- is_primary: boolean
```

**Key Pattern:**
- subject_catalog = master course catalog (reusable subjects)
- education_plan = academic programs
- education_plan_subject = curriculum (which subjects in which program)
- course = actual course instance for a specific semester/year
- Multiple teachers can teach one course

---

#### 6. ENROLLMENTS

**journal** (591,485 records) - ENROLLMENTS
```sql
- id: bigint (PK)
- student_id: bigint → students.id
- course_id: bigint → course.id
- enrollment_date: timestamp
- status: integer (1=enrolled, 2=completed, 3=dropped)
- final_grade: numeric
- letter_grade: text (A, B, C, D, F)
- gpa_points: numeric (4.0 scale)
```

**Key Pattern:**
- journal = enrollment records (student + course instance)
- Stores both enrollment and final grades

---

#### 7. GRADES

**journal_details** (3,209,747 records) - GRANULAR GRADES
```sql
- id: bigint (PK)
- journal_id: bigint → journal.id
- grade_type_id: bigint → dictionaries (midterm, final, quiz, hw)
- grade_value: numeric
- max_value: numeric
- weight_percentage: numeric
- grade_date: timestamp
- graded_by: bigint → teachers.id
```

**Key Pattern:**
- journal_details = individual grade components
- One enrollment (journal) has many grade details
- Example: 1 enrollment → [midterm:25, final:30, hw1:10, hw2:10]

---

#### 8. ASSESSMENTS & EXAMS

**exam** (5,833 exams, 5,719 active)
```sql
- id: bigint (PK)
- course_id: bigint → course.id
- exam_type_id: bigint → dictionaries (midterm, final, quiz)
- title: text
- description: text
- total_marks: numeric
- passing_marks: numeric
- exam_date: text (DD/MM/YYYY)
- start_time: text (HH:MM)
- duration_minutes: integer
- active: smallint
```

**exam_student** (68,365 submissions)
```sql
- id: bigint (PK)
- exam_id: bigint → exam.id
- student_id: bigint → students.id
- submission_date: timestamp
- score: numeric
- status: integer (1=submitted, 2=graded)
- attempt_number: integer
```

---

#### 9. COURSE MATERIALS

**files** (14,816 files)
```sql
- id: bigint (PK)
- name: text (filename)
- path: text (file system path)
- content_type: text (MIME type)
- file_size: bigint (bytes)
- upload_date: timestamp
- uploaded_by: bigint → users.id
```

**course_meeting_topic** (topics/modules)
```sql
- id: bigint (PK)
- course_meeting_id: bigint → course_meeting.id
- topic_name: text
- sequence_number: integer
```

**course_meeting_topic_file** (9,324 links)
```sql
- id: bigint (PK)
- topic_id: bigint → course_meeting_topic.id
- file_id: bigint → files.id
```

**Key Pattern:**
- files = central file repository
- course_meeting_topic = organize materials by topic
- Link files to topics/modules

---

#### 10. ATTENDANCE & SCHEDULES

**course_meeting** (194,500 total, 185,276 active)
```sql
- id: bigint (PK)
- course_id: bigint → course.id
- meeting_date: date
- start_time: time
- end_time: time
- room_id: bigint → rooms.id
- topic: text
- meeting_type_id: bigint (lecture, seminar, lab)
- active: smallint
```

**course_meeting_attendance** (0 records in current DB)
```sql
- id: bigint (PK)
- meeting_id: bigint → course_meeting.id
- student_id: bigint → students.id
- status: integer (present, absent, late)
```

---

## NEW DATABASE: LMS

### Connection Info
- **Host:** localhost
- **Port:** 5432
- **Database:** lms
- **User:** postgres
- **Password:** 1111
- **Total Tables:** 36 tables

### Key Design Improvements

#### 1. UUID Instead of BIGINT
```sql
-- Old: id: bigint
-- New: id: uuid DEFAULT gen_random_uuid()
```
**Benefits:**
- Better security (not sequential/guessable)
- Easier distributed systems
- No ID collision in merges

#### 2. JSONB for Multilingual Fields
```sql
-- Old: name_id → dictionaries table
-- New: title: jsonb = {"az": "...", "en": "...", "ru": "..."}
```
**Benefits:**
- No JOIN needed for translations
- Atomic updates
- Flexible language support

#### 3. Proper Enum Types
```sql
CREATE TYPE enrollment_status AS ENUM ('enrolled', 'completed', 'dropped', 'withdrawn');
CREATE TYPE assessment_type AS ENUM ('exam', 'quiz', 'assignment', 'project', 'presentation');
```

#### 4. Audit Trails
```sql
-- Every table has:
created_at: timestamp DEFAULT CURRENT_TIMESTAMP
updated_at: timestamp DEFAULT CURRENT_TIMESTAMP
```

---

### Key Tables in New Database

#### **users** (6,490 records)
```sql
- id: uuid (PK)
- email: text UNIQUE NOT NULL
- password_hash: text (bcrypt/argon2)
- role: enum
- is_active: boolean DEFAULT true
- last_login: timestamp
- created_at, updated_at: timestamp
```

#### **persons** (6,471 records)
```sql
- id: uuid (PK)
- user_id: uuid → users.id
- first_name: text
- last_name: text
- patronymic: text
- birth_date: date (proper date type!)
- gender: enum ('male', 'female', 'other')
- phone: text
- photo_url: text
- metadata: jsonb (flexible extra data)
```

#### **students** (5,959 records)
```sql
- id: uuid (PK)
- user_id: uuid → users.id UNIQUE
- person_id: uuid → persons.id
- student_number: text UNIQUE
- admission_date: date
- current_year: integer
- gpa: numeric(3,2) (0.00-4.00 scale)
- academic_status: enum
- metadata: jsonb (old_student_id, etc.)
```

#### **staff_members** (350 records)
```sql
- id: uuid (PK)
- user_id: uuid → users.id
- person_id: uuid → persons.id
- employee_number: text UNIQUE
- organization_unit_id: uuid → organization_units.id
- position_title: jsonb (multilingual)
- employment_type: enum
- hire_date: date
- academic_degree: text
- academic_rank: text
```

#### **courses** (883 records) - MASTER CATALOG
```sql
- id: uuid (PK)
- code: text UNIQUE (e.g., "CS101")
- name: jsonb (multilingual)
- description: jsonb
- credit_hours: integer
- organization_unit_id: uuid
- prerequisites: uuid[] (array of course IDs)
- metadata: jsonb
```

#### **course_offerings** (1,581 records) - INSTANCES
```sql
- id: uuid (PK)
- course_id: uuid → courses.id
- academic_term_id: uuid → academic_terms.id
- section_code: text (e.g., "01", "02")
- max_enrollment: integer
- delivery_mode: enum ('in_person', 'online', 'hybrid')
- old_course_id: bigint (mapping to old DB)
```

#### **course_enrollments** (94,558 records)
```sql
- id: uuid (PK)
- course_offering_id: uuid → course_offerings.id
- student_id: uuid → students.id
- enrollment_date: timestamp
- enrollment_status: enum
- grade: text
- grade_points: numeric(3,2)
- old_journal_id: bigint (mapping)
```

#### **grades** (194,966 records)
```sql
- id: uuid (PK)
- enrollment_id: uuid → course_enrollments.id
- assessment_id: uuid → assessments.id
- score: numeric
- max_score: numeric
- weight: numeric
- graded_date: timestamp
- graded_by: uuid → users.id
- feedback: text
```

#### **assessments** (66,365 records)
```sql
- id: uuid (PK)
- course_offering_id: uuid → course_offerings.id
- title: jsonb (multilingual)
- description: jsonb
- assessment_type: text ('exam', 'quiz', 'assignment')
- weight_percentage: numeric(5,2)
- total_marks: numeric
- due_date: timestamp
- duration_minutes: integer
- rubric: jsonb
```

#### **assessment_submissions** (63,781 records)
```sql
- id: uuid (PK)
- assessment_id: uuid → assessments.id
- student_id: uuid → students.id
- submission_date: timestamp
- score: numeric
- feedback: text
- attempt_number: integer
- status: enum
```

#### **class_schedules** (232,347 records)
```sql
- id: uuid (PK)
- course_offering_id: uuid → course_offerings.id
- room_id: uuid → rooms.id
- scheduled_date: date
- start_time: time
- end_time: time
- session_type: enum ('lecture', 'seminar', 'lab', 'exam')
- topic: jsonb
```

#### **course_materials** (8,991 records)
```sql
- id: uuid (PK)
- course_offering_id: uuid → course_offerings.id
- title: jsonb
- material_type: enum ('lecture', 'reading', 'video', 'assignment')
- file_url: text
- file_size: bigint
- metadata: jsonb
```

---

## KEY DIFFERENCES SUMMARY

| Feature | OLD (edu) | NEW (lms) |
|---------|-----------|-----------|
| **ID Type** | bigint | uuid |
| **Multilingual** | dictionaries table | JSONB fields |
| **Date Format** | text "DD/MM/YYYY" | date type |
| **Enums** | bigint → dictionaries | Native ENUM types |
| **Audit Trail** | Inconsistent | All tables have timestamps |
| **Foreign Keys** | Some missing | All enforced with indexes |
| **Password** | Base64 encoded | Properly hashed |
| **Metadata** | Fixed columns | JSONB for flexibility |

---

## MIGRATION MAPPINGS

### ID Mappings (stored in metadata/tracking columns)

```sql
-- Students
OLD: students.id (bigint)
NEW: students.metadata->>'old_student_id' → students.id (uuid)

-- Teachers
OLD: teachers.id (bigint)
NEW: staff_members.metadata->>'old_teacher_id' → staff_members.id (uuid)

-- Courses
OLD: course.id (bigint)
NEW: course_offerings.old_course_id → course_offerings.id (uuid)

-- Enrollments
OLD: journal.id (bigint)
NEW: course_enrollments.old_journal_id → course_enrollments.id (uuid)
```

### Enum Mappings

```sql
-- OLD: gender_id = 1/2 in dictionaries
-- NEW: gender ENUM = 'male'/'female'

-- OLD: active = 1/0 (smallint)
-- NEW: is_active = true/false (boolean)

-- OLD: status = 1,2,3 (integers)
-- NEW: enrollment_status = 'enrolled'/'completed'/'dropped' (enum)
```

---

## QUERIES FOR COMMON OPERATIONS

### Check Migration Status
```sql
-- Count migrated vs source
SELECT 
  'students' as entity,
  (SELECT COUNT(*) FROM edu.students WHERE active=1) as old_count,
  (SELECT COUNT(*) FROM lms.students) as new_count;
```

### Find Unmigrated Records
```sql
-- Students not migrated
SELECT s.id, s.person_id, s.user_id
FROM edu.students s
WHERE s.id NOT IN (
  SELECT CAST(metadata->>'old_student_id' AS BIGINT)
  FROM lms.students
  WHERE metadata->>'old_student_id' IS NOT NULL
);
```

### Verify Foreign Key Integrity
```sql
-- Check for orphaned enrollments
SELECT COUNT(*)
FROM lms.course_enrollments ce
LEFT JOIN lms.students s ON ce.student_id = s.id
WHERE s.id IS NULL;
```

---

## NEXT STEPS FOR DEVELOPMENT

### With This Knowledge You Can:

1. **Complete Migrations**
   - Understand source and target schemas
   - Know which fields map to which
   - Handle data type conversions

2. **Build APIs**
   - Know table relationships
   - Understand data structures
   - Write efficient queries

3. **Fix Data Issues**
   - Identify orphaned records
   - Validate foreign keys
   - Clean up inconsistencies

4. **Optimize Performance**
   - Know which tables are large (3M+ grades)
   - Understand query patterns
   - Add appropriate indexes

5. **Extend System**
   - Use JSONB for flexible metadata
   - Add new enums as needed
   - Follow established patterns

---

**Database Structures Fully Learned ✅**

Ready for next tasks:
- Complete migration implementation
- API development
- Frontend integration
- Performance optimization
- Production deployment
