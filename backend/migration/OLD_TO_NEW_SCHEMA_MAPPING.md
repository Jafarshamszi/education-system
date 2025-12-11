# Old Database to New Database Schema Mapping
## Education System Database Migration

**Migration Date:** October 3, 2025  
**Old Database:** edu (355 tables, 0 FK constraints)  
**New Database:** edu_v2 (Modern normalized structure with FK constraints)

---

## Executive Summary

This document maps every critical table and data element from the old education system database to the new redesigned schema. The migration preserves all existing data while transforming it to a modern, normalized structure with proper relationships, security, and multilingual support.

### Migration Scope
- **Source:** 355 tables with 6,987 users, 6,344 students, 424 teachers, 6,020 courses
- **Target:** ~80 core tables (3NF normalized) with proper FK constraints
- **Data Transformation:** Integer IDs → UUIDs, Single language → Multilingual JSONB
- **Key Changes:** Add referential integrity, implement RLS, multilingual support

---

## 1. Core Entity Mappings

### 1.1 Users & Authentication

#### OLD: users, accounts, persons → NEW: users, persons

```sql
-- MAPPING: users table
OLD: users (19 columns, 6987 rows)
├── id (integer) → NEW: users.id (uuid) [UUID generation needed]
├── username (varchar) → NEW: users.username (text)
├── email (varchar) → NEW: users.email (text)
├── password (varchar) → NEW: users.password_hash (text) [Already hashed]
├── is_active (boolean) → NEW: users.is_active (boolean)
├── last_login (timestamp) → NEW: users.last_login_at (timestamptz)
├── create_date (timestamp) → NEW: users.created_at (timestamptz)
├── update_date (timestamp) → NEW: users.updated_at (timestamptz)
├── account_id (integer) → [JOIN with accounts to get person_id]
└── [Other fields] → NEW: users.metadata (jsonb)

-- NEW FIELDS to populate:
users.email_verified = false (default, manual verification needed)
users.mfa_enabled = false (default)
users.failed_login_count = 0 (default)
users.is_locked = false (default)
users.password_changed_at = users.created_at (default)

-- MAPPING: accounts table
OLD: accounts (columns unknown, join table)
├── id → [Used to link users to persons]
└── person_id → [Link to persons table]

-- MAPPING: persons table
OLD: persons (22 columns)
├── id (integer) → NEW: persons.id (uuid)
├── first_name (varchar) → NEW: persons.first_name (text)
├── last_name (varchar) → NEW: persons.last_name (text)
├── middle_name (varchar) → NEW: persons.middle_name (text)
├── date_of_birth (date) → NEW: persons.date_of_birth (date)
├── gender (varchar) → NEW: persons.gender (text) [Normalize: M/F/male/female]
├── phone (varchar) → NEW: persons.phone_primary (text)
├── address (text) → NEW: persons.address (jsonb) [Convert to structured JSON]
├── photo_url (varchar) → NEW: persons.photo_url (text)
└── [user_id link] → NEW: persons.user_id (uuid) [Via accounts table]

-- MULTILINGUAL FIELDS (NEW):
persons.first_name_az = NULL (populate from dictionaries if available)
persons.last_name_az = NULL (populate from dictionaries if available)
persons.first_name_ru = NULL (populate from dictionaries if available)
persons.last_name_ru = NULL (populate from dictionaries if available)

-- ENCRYPTED FIELDS (NEW):
persons.national_id = NULL (add manually if needed)
persons.passport_number = NULL (add manually if needed)
persons.emergency_contact = NULL (add manually if needed)
```

**Migration Script:**
```sql
-- Step 1: Create UUID mapping table for users
CREATE TEMP TABLE user_id_mapping AS
SELECT 
    old_id::integer as old_id,
    gen_random_uuid() as new_uuid
FROM (SELECT DISTINCT id FROM old_db.users) u;

-- Step 2: Migrate users
INSERT INTO new_db.users (id, username, email, password_hash, is_active, last_login_at, created_at, updated_at, metadata)
SELECT 
    m.new_uuid,
    u.username,
    COALESCE(u.email, u.username || '@temp.bbu.edu.az'),
    u.password,
    COALESCE(u.is_active, true),
    u.last_login,
    COALESCE(u.create_date, CURRENT_TIMESTAMP),
    COALESCE(u.update_date, CURRENT_TIMESTAMP),
    jsonb_build_object(
        'old_id', u.id,
        'migrated_at', CURRENT_TIMESTAMP,
        'source', 'legacy_users_table'
    )
FROM old_db.users u
JOIN user_id_mapping m ON u.id = m.old_id;

-- Step 3: Migrate persons (via accounts link)
INSERT INTO new_db.persons (id, user_id, first_name, last_name, middle_name, date_of_birth, 
                             gender, phone_primary, photo_url, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    u_map.new_uuid,
    p.first_name,
    p.last_name,
    p.middle_name,
    p.date_of_birth,
    CASE 
        WHEN LOWER(p.gender) IN ('m', 'male', 'erkek') THEN 'male'
        WHEN LOWER(p.gender) IN ('f', 'female', 'qadın', 'женский') THEN 'female'
        ELSE 'prefer_not_to_say'
    END,
    p.phone,
    p.photo_url,
    COALESCE(p.create_date, CURRENT_TIMESTAMP),
    COALESCE(p.update_date, CURRENT_TIMESTAMP)
FROM old_db.persons p
JOIN old_db.accounts a ON p.id = a.person_id
JOIN old_db.users u ON a.id = u.account_id
JOIN user_id_mapping u_map ON u.id = u_map.old_id;
```

---

### 1.2 Students

#### OLD: students → NEW: students

```sql
-- MAPPING: students table
OLD: students (22 columns, 6344 rows)
├── id (integer) → NEW: students.id (uuid)
├── person_id (integer) → NEW: students.user_id (uuid) [Via persons→users link]
├── student_number (varchar) → NEW: students.student_number (text)
├── active (boolean) → NEW: students.status (text) [Map: true='active', false='inactive']
├── create_date (timestamp) → NEW: students.enrollment_date (date)
├── update_date (timestamp) → NEW: students.updated_at (timestamptz)
└── [Other fields] → NEW: students.metadata (jsonb)

-- NEW REQUIRED FIELDS:
students.academic_program_id = NULL (populate from education_group mapping)
students.enrollment_date = students.create_date
students.status = CASE WHEN active=true THEN 'active' ELSE 'inactive' END
students.study_mode = 'full_time' (default, update manually if needed)
students.funding_type = 'self_funded' (default, update manually if needed)
students.gpa = NULL (calculate from journal grades)
students.total_credits_earned = 0 (calculate from completed courses)
students.academic_advisor_id = NULL (assign manually)
```

**Migration Script:**
```sql
-- Step 1: Create student UUID mapping
CREATE TEMP TABLE student_id_mapping AS
SELECT 
    old_id::integer as old_id,
    gen_random_uuid() as new_uuid
FROM (SELECT DISTINCT id FROM old_db.students) s;

-- Step 2: Migrate students
INSERT INTO new_db.students (
    id, user_id, student_number, enrollment_date, status, 
    study_mode, funding_type, gpa, total_credits_earned, 
    created_at, updated_at, metadata
)
SELECT 
    s_map.new_uuid,
    u_map.new_uuid, -- user_id from persons link
    s.student_number,
    COALESCE(s.create_date::date, CURRENT_DATE),
    CASE WHEN COALESCE(s.active, false) THEN 'active' ELSE 'inactive' END,
    'full_time',
    'self_funded',
    NULL, -- Calculate separately
    0,    -- Calculate separately
    COALESCE(s.create_date, CURRENT_TIMESTAMP),
    COALESCE(s.update_date, CURRENT_TIMESTAMP),
    jsonb_build_object(
        'old_id', s.id,
        'old_person_id', s.person_id,
        'migrated_at', CURRENT_TIMESTAMP
    )
FROM old_db.students s
JOIN student_id_mapping s_map ON s.id = s_map.old_id
LEFT JOIN old_db.persons p ON s.person_id = p.id
LEFT JOIN old_db.accounts a ON p.id = a.person_id
LEFT JOIN old_db.users u ON a.id = u.account_id
LEFT JOIN user_id_mapping u_map ON u.id = u_map.old_id
WHERE u_map.new_uuid IS NOT NULL;
```

---

### 1.3 Teachers/Staff

#### OLD: teachers → NEW: staff_members

```sql
-- MAPPING: teachers table
OLD: teachers (18 columns, 424 rows)
├── id (integer) → NEW: staff_members.id (uuid)
├── person_id (integer) → NEW: staff_members.user_id (uuid) [Via persons→users]
├── organization_id (integer) → NEW: staff_members.organization_unit_id (uuid)
├── active (boolean) → NEW: staff_members.is_active (boolean)
├── create_date (timestamp) → NEW: staff_members.hire_date (date)
└── [Other fields] → NEW: staff_members.metadata (jsonb)

-- NEW REQUIRED FIELDS:
staff_members.employee_number = 'T' || teacher_id (generate if not exists)
staff_members.position_title = {"az": "Müəllim", "en": "Teacher", "ru": "Преподаватель"}
staff_members.employment_type = 'full_time' (default)
staff_members.academic_rank = NULL (derive from metadata or assign manually)
staff_members.administrative_role = NULL (derive from organization role)
```

**Migration Script:**
```sql
-- Step 1: Create teacher/staff UUID mapping
CREATE TEMP TABLE staff_id_mapping AS
SELECT 
    old_id::integer as old_id,
    gen_random_uuid() as new_uuid
FROM (SELECT DISTINCT id FROM old_db.teachers) t;

-- Step 2: Migrate teachers to staff_members
INSERT INTO new_db.staff_members (
    id, user_id, employee_number, organization_unit_id, 
    position_title, employment_type, hire_date, is_active,
    created_at, updated_at, metadata
)
SELECT 
    t_map.new_uuid,
    u_map.new_uuid,
    'T' || LPAD(t.id::text, 6, '0'),
    org_map.new_uuid, -- organization mapping
    jsonb_build_object(
        'az', 'Müəllim',
        'en', 'Teacher',
        'ru', 'Преподаватель'
    ),
    'full_time',
    COALESCE(t.create_date::date, CURRENT_DATE),
    COALESCE(t.active, true),
    COALESCE(t.create_date, CURRENT_TIMESTAMP),
    COALESCE(t.update_date, CURRENT_TIMESTAMP),
    jsonb_build_object(
        'old_id', t.id,
        'old_person_id', t.person_id,
        'old_organization_id', t.organization_id,
        'migrated_at', CURRENT_TIMESTAMP
    )
FROM old_db.teachers t
JOIN staff_id_mapping t_map ON t.id = t_map.old_id
LEFT JOIN old_db.persons p ON t.person_id = p.id
LEFT JOIN old_db.accounts a ON p.id = a.person_id
LEFT JOIN old_db.users u ON a.id = u.account_id
LEFT JOIN user_id_mapping u_map ON u.id = u_map.old_id
LEFT JOIN organization_id_mapping org_map ON t.organization_id = org_map.old_id
WHERE u_map.new_uuid IS NOT NULL;
```

---

### 1.4 Organizations & Academic Structure

#### OLD: organizations, education_group → NEW: organization_units, academic_programs

```sql
-- MAPPING: organizations table
OLD: organizations (hierarchy with parent_id, 419 rows)
├── id (integer) → NEW: organization_units.id (uuid)
├── parent_id (integer) → NEW: organization_units.parent_id (uuid)
├── name_dictionary_id (integer) → NEW: organization_units.name (jsonb) [From dictionaries]
├── type/level (integer) → NEW: organization_units.type (text)
├── code (varchar) → NEW: organization_units.code (text)
└── [Other fields] → NEW: organization_units.metadata (jsonb)

-- TYPE MAPPING:
Level 1 = 'university'
Level 2 = 'faculty'
Level 3 = 'department'
Level 4+ = 'program' or 'center'

-- MAPPING: education_group → academic_programs
OLD: education_group (14 columns, 419 rows)
├── id (integer) → NEW: academic_programs.id (uuid)
├── organization_id (integer) → NEW: academic_programs.organization_unit_id (uuid)
├── name (varchar) → NEW: academic_programs.name (jsonb)
├── code (varchar) → NEW: academic_programs.code (text)
├── education_plan_id (integer) → [Link to curriculum structure]
└── [Other fields] → NEW: academic_programs.metadata (jsonb)

-- NEW REQUIRED FIELDS:
academic_programs.degree_type = 'bachelor' (derive from education plan)
academic_programs.duration_years = 4 (default, update from plan)
academic_programs.total_credits = (calculate from education_plan_subject)
academic_programs.language_of_instruction = ['az'] (default)
```

**Migration Script:**
```sql
-- Step 1: Create organization UUID mapping
CREATE TEMP TABLE organization_id_mapping AS
SELECT 
    old_id::integer as old_id,
    gen_random_uuid() as new_uuid
FROM (SELECT DISTINCT id FROM old_db.organizations) o;

-- Step 2: Get organization names from dictionaries
CREATE TEMP TABLE organization_names AS
SELECT 
    o.id as org_id,
    jsonb_build_object(
        'az', COALESCE(d_az.value, 'Unknown'),
        'en', COALESCE(d_en.value, d_az.value, 'Unknown'),
        'ru', COALESCE(d_ru.value, d_az.value, 'Unknown')
    ) as name_json
FROM old_db.organizations o
LEFT JOIN old_db.dictionaries d_az ON o.name_dictionary_id = d_az.id AND d_az.language = 'az'
LEFT JOIN old_db.dictionaries d_en ON o.name_dictionary_id = d_en.id AND d_en.language = 'en'
LEFT JOIN old_db.dictionaries d_ru ON o.name_dictionary_id = d_ru.id AND d_ru.language = 'ru';

-- Step 3: Migrate organizations
INSERT INTO new_db.organization_units (
    id, parent_id, type, code, name, is_active, 
    created_at, updated_at, metadata
)
SELECT 
    o_map.new_uuid,
    parent_map.new_uuid,
    CASE 
        WHEN o.parent_id IS NULL THEN 'university'
        WHEN EXISTS(SELECT 1 FROM old_db.organizations WHERE parent_id = o.id) 
            AND o.parent_id IS NOT NULL THEN 'faculty'
        WHEN o.parent_id IN (SELECT id FROM old_db.organizations WHERE parent_id IS NOT NULL) THEN 'department'
        ELSE 'program'
    END,
    COALESCE(o.code, 'ORG' || o.id),
    on.name_json,
    COALESCE(o.active, true),
    COALESCE(o.create_date, CURRENT_TIMESTAMP),
    COALESCE(o.update_date, CURRENT_TIMESTAMP),
    jsonb_build_object(
        'old_id', o.id,
        'old_parent_id', o.parent_id,
        'migrated_at', CURRENT_TIMESTAMP
    )
FROM old_db.organizations o
JOIN organization_id_mapping o_map ON o.id = o_map.old_id
LEFT JOIN organization_id_mapping parent_map ON o.parent_id = parent_map.old_id
LEFT JOIN organization_names on ON o.id = on.org_id;
```

---

### 1.5 Courses & Course Catalog

#### OLD: course, subject_catalog, education_plan_subject → NEW: courses, course_offerings

```sql
-- MAPPING: subject_catalog (master course definitions)
OLD: subject_catalog
├── id (integer) → NEW: courses.id (uuid)
├── code (varchar) → NEW: courses.code (text)
├── name (varchar) → NEW: courses.name (jsonb) [Convert to multilingual]
├── credit (integer) → NEW: courses.credit_hours (integer)
├── description (text) → NEW: courses.description (jsonb)
└── [Other fields] → NEW: courses.metadata (jsonb)

-- MAPPING: course (course instances/offerings)
OLD: course (34 columns, 6020 rows)
├── id (integer) → NEW: course_offerings.id (uuid)
├── subject_catalog_id (integer) → NEW: course_offerings.course_id (uuid)
├── education_group_id (integer) → NEW: academic_term link (complex)
├── semester (integer) → NEW: academic_term_id (create terms first)
├── max_students (integer) → NEW: course_offerings.max_enrollment (integer)
├── active (boolean) → NEW: course_offerings.is_published (boolean)
└── [Other fields] → NEW: course_offerings.metadata (jsonb)

-- NEW STRUCTURES NEEDED:
1. Create academic_terms for each semester
2. Map courses to terms
3. Create course_instructors from course_teacher table
4. Create course_enrollments from education_group_student table
```

**Migration Script:**
```sql
-- Step 1: Create academic terms (2020-2025, Fall/Spring)
INSERT INTO new_db.academic_terms (id, academic_year, term_type, term_number, start_date, end_date, is_current)
SELECT 
    gen_random_uuid(),
    year || '-' || (year+1),
    CASE WHEN term = 1 THEN 'fall' ELSE 'spring' END,
    term,
    (year || '-' || CASE WHEN term = 1 THEN '09-01' ELSE '02-01' END)::date,
    (CASE WHEN term = 1 THEN year ELSE year+1 END || '-' || CASE WHEN term = 1 THEN '12-31' ELSE '06-30' END)::date,
    (year = 2024 AND term = 1) -- Current term
FROM generate_series(2020, 2025) year
CROSS JOIN generate_series(1, 2) term;

-- Step 2: Create course UUID mapping
CREATE TEMP TABLE course_id_mapping AS
SELECT 
    old_id::integer as old_id,
    gen_random_uuid() as new_uuid
FROM (SELECT DISTINCT id FROM old_db.subject_catalog) c;

-- Step 3: Migrate subject catalog to courses
INSERT INTO new_db.courses (
    id, code, name, description, credit_hours, 
    course_level, is_active, created_at, updated_at, metadata
)
SELECT 
    c_map.new_uuid,
    sc.code,
    jsonb_build_object(
        'az', sc.name,
        'en', sc.name, -- Translate manually if needed
        'ru', sc.name
    ),
    jsonb_build_object(
        'az', COALESCE(sc.description, ''),
        'en', COALESCE(sc.description, ''),
        'ru', COALESCE(sc.description, '')
    ),
    COALESCE(sc.credit, 0),
    'undergraduate', -- Default
    COALESCE(sc.active, true),
    COALESCE(sc.create_date, CURRENT_TIMESTAMP),
    COALESCE(sc.update_date, CURRENT_TIMESTAMP),
    jsonb_build_object(
        'old_id', sc.id,
        'migrated_at', CURRENT_TIMESTAMP
    )
FROM old_db.subject_catalog sc
JOIN course_id_mapping c_map ON sc.id = c_map.old_id;

-- Step 4: Create course offerings UUID mapping
CREATE TEMP TABLE course_offering_id_mapping AS
SELECT 
    old_id::integer as old_id,
    gen_random_uuid() as new_uuid
FROM (SELECT DISTINCT id FROM old_db.course) co;

-- Step 5: Migrate course instances to course_offerings
INSERT INTO new_db.course_offerings (
    id, course_id, academic_term_id, section_code,
    language_of_instruction, max_enrollment, current_enrollment,
    delivery_mode, is_published, created_at, updated_at, metadata
)
SELECT 
    co_map.new_uuid,
    c_map.new_uuid,
    (SELECT id FROM new_db.academic_terms WHERE term_number = c.semester ORDER BY start_date DESC LIMIT 1),
    COALESCE(c.section, 'A'),
    'az',
    COALESCE(c.max_students, 50),
    0, -- Calculate from enrollments
    'in_person',
    COALESCE(c.active, true),
    COALESCE(c.create_date, CURRENT_TIMESTAMP),
    COALESCE(c.update_date, CURRENT_TIMESTAMP),
    jsonb_build_object(
        'old_id', c.id,
        'old_subject_catalog_id', c.subject_catalog_id,
        'old_education_group_id', c.education_group_id,
        'migrated_at', CURRENT_TIMESTAMP
    )
FROM old_db.course c
JOIN course_offering_id_mapping co_map ON c.id = co_map.old_id
LEFT JOIN course_id_mapping c_map ON c.subject_catalog_id = c_map.old_id;
```

---

### 1.6 Course Enrollments & Registrations

#### OLD: education_group_student, course_student → NEW: course_enrollments

```sql
-- MAPPING: education_group_student + course_student
OLD: education_group_student (student to program mapping)
OLD: course_student (student to course instance mapping)
↓
NEW: course_enrollments (student course registrations)

Fields:
├── student_id (old) → student_id (new uuid)
├── course_id (old) → course_offering_id (new uuid)
├── enrollment_date → created_at
├── status → enrollment_status (active→enrolled, inactive→dropped)
└── grade → grade field (preserve grades)
```

**Migration Script:**
```sql
-- Migrate course enrollments
INSERT INTO new_db.course_enrollments (
    id, course_offering_id, student_id, enrollment_date,
    enrollment_status, grade, created_at, updated_at, metadata
)
SELECT 
    gen_random_uuid(),
    co_map.new_uuid,
    s_map.new_uuid,
    COALESCE(cs.create_date, CURRENT_TIMESTAMP),
    CASE 
        WHEN cs.active THEN 'enrolled'
        WHEN cs.completed THEN 'completed'
        ELSE 'dropped'
    END,
    cs.grade,
    COALESCE(cs.create_date, CURRENT_TIMESTAMP),
    COALESCE(cs.update_date, CURRENT_TIMESTAMP),
    jsonb_build_object(
        'old_course_student_id', cs.id,
        'migrated_at', CURRENT_TIMESTAMP
    )
FROM old_db.course_student cs
JOIN course_offering_id_mapping co_map ON cs.course_id = co_map.old_id
JOIN student_id_mapping s_map ON cs.student_id = s_map.old_id;
```

---

### 1.7 Grading & Assessments

#### OLD: journal, journal_details → NEW: assessments, assessment_submissions, grades

```sql
-- MAPPING: journal (assessment definitions)
OLD: journal (591,485 rows)
├── id → assessments.id (uuid)
├── course_id → course_offering_id link
├── assessment_type → assessment_type
├── weight → weight_percentage
└── max_score → total_marks

-- MAPPING: journal_details (student grades)
OLD: journal_details (3,209,747 rows)
├── id → grades.id (uuid)
├── journal_id → assessment_id link
├── student_id → student_id (uuid)
├── score → marks_obtained
├── grade → letter_grade
└── feedback → feedback
```

**Migration Script:**
```sql
-- Step 1: Migrate journal to assessments
CREATE TEMP TABLE journal_id_mapping AS
SELECT 
    old_id::integer as old_id,
    gen_random_uuid() as new_uuid
FROM (SELECT DISTINCT id FROM old_db.journal) j;

INSERT INTO new_db.assessments (
    id, course_offering_id, title, assessment_type,
    weight_percentage, total_marks, due_date,
    created_at, updated_at, metadata
)
SELECT 
    j_map.new_uuid,
    co_map.new_uuid,
    jsonb_build_object(
        'az', COALESCE(j.name, 'Qiymətləndirmə'),
        'en', COALESCE(j.name, 'Assessment'),
        'ru', COALESCE(j.name, 'Оценка')
    ),
    CASE 
        WHEN j.type LIKE '%exam%' THEN 'exam'
        WHEN j.type LIKE '%quiz%' THEN 'quiz'
        WHEN j.type LIKE '%assignment%' THEN 'assignment'
        ELSE 'other'
    END,
    COALESCE(j.weight, 100),
    COALESCE(j.max_score, 100),
    j.due_date,
    COALESCE(j.create_date, CURRENT_TIMESTAMP),
    COALESCE(j.update_date, CURRENT_TIMESTAMP),
    jsonb_build_object(
        'old_id', j.id,
        'migrated_at', CURRENT_TIMESTAMP
    )
FROM old_db.journal j
JOIN journal_id_mapping j_map ON j.id = j_map.old_id
LEFT JOIN course_offering_id_mapping co_map ON j.course_id = co_map.old_id;

-- Step 2: Migrate journal_details to grades
INSERT INTO new_db.grades (
    id, assessment_id, student_id, marks_obtained,
    percentage, letter_grade, feedback, is_final,
    graded_at, created_at, updated_at, metadata
)
SELECT 
    gen_random_uuid(),
    j_map.new_uuid,
    s_map.new_uuid,
    jd.score,
    (jd.score / NULLIF(j.max_score, 0) * 100),
    jd.grade,
    jd.feedback,
    true,
    COALESCE(jd.graded_date, jd.update_date, CURRENT_TIMESTAMP),
    COALESCE(jd.create_date, CURRENT_TIMESTAMP),
    COALESCE(jd.update_date, CURRENT_TIMESTAMP),
    jsonb_build_object(
        'old_journal_detail_id', jd.id,
        'migrated_at', CURRENT_TIMESTAMP
    )
FROM old_db.journal_details jd
JOIN old_db.journal j ON jd.journal_id = j.id
JOIN journal_id_mapping j_map ON j.id = j_map.old_id
JOIN student_id_mapping s_map ON jd.student_id = s_map.old_id;
```

---

## 2. Supporting Data Migrations

### 2.1 Roles & Permissions

```sql
-- Create default roles
INSERT INTO new_db.roles (id, code, name, description, level, is_system)
VALUES
(gen_random_uuid(), 'RECTOR', '{"az":"Rektor","en":"Rector","ru":"Ректор"}', NULL, 1, true),
(gen_random_uuid(), 'VICE_RECTOR', '{"az":"Prorektor","en":"Vice Rector","ru":"Проректор"}', NULL, 2, true),
(gen_random_uuid(), 'DEAN', '{"az":"Dekan","en":"Dean","ru":"Декан"}', NULL, 3, true),
(gen_random_uuid(), 'VICE_DEAN', '{"az":"Prodekan","en":"Vice Dean","ru":"Продекан"}', NULL, 4, true),
(gen_random_uuid(), 'DEPT_HEAD', '{"az":"Kafedra müdiri","en":"Department Head","ru":"Заведующий кафедрой"}', NULL, 5, true),
(gen_random_uuid(), 'TEACHER', '{"az":"Müəllim","en":"Teacher","ru":"Преподаватель"}', NULL, 6, true),
(gen_random_uuid(), 'STUDENT', '{"az":"Tələbə","en":"Student","ru":"Студент"}', NULL, 7, true),
(gen_random_uuid(), 'ADMIN', '{"az":"Administrator","en":"Administrator","ru":"Администратор"}', NULL, 0, true);

-- Assign roles to users based on old data
INSERT INTO new_db.user_roles (id, user_id, role_id, organization_unit_id, is_primary)
SELECT 
    gen_random_uuid(),
    s_map.new_uuid,
    (SELECT id FROM new_db.roles WHERE code = 'STUDENT'),
    NULL,
    true
FROM old_db.students s
JOIN student_id_mapping s_map ON s.id = s_map.old_id;

INSERT INTO new_db.user_roles (id, user_id, role_id, organization_unit_id, is_primary)
SELECT 
    gen_random_uuid(),
    t_map.new_uuid,
    (SELECT id FROM new_db.roles WHERE code = 'TEACHER'),
    org_map.new_uuid,
    true
FROM old_db.teachers t
JOIN staff_id_mapping t_map ON t.id = t_map.old_id
LEFT JOIN organization_id_mapping org_map ON t.organization_id = org_map.old_id;
```

### 2.2 Course Instructors

```sql
-- Migrate course_teacher to course_instructors
INSERT INTO new_db.course_instructors (
    id, course_offering_id, instructor_id, role, assigned_date
)
SELECT 
    gen_random_uuid(),
    co_map.new_uuid,
    t_map.new_uuid,
    'primary',
    COALESCE(ct.create_date, CURRENT_TIMESTAMP)
FROM old_db.course_teacher ct
JOIN course_offering_id_mapping co_map ON ct.course_id = co_map.old_id
JOIN staff_id_mapping t_map ON ct.teacher_id = t_map.old_id;
```

---

## 3. Data Validation Queries

```sql
-- Validate user counts
SELECT 
    'OLD' as source, COUNT(*) as user_count FROM old_db.users
UNION ALL
SELECT 
    'NEW' as source, COUNT(*) as user_count FROM new_db.users;

-- Validate student counts
SELECT 
    'OLD' as source, COUNT(*) as student_count FROM old_db.students
UNION ALL
SELECT 
    'NEW' as source, COUNT(*) as student_count FROM new_db.students;

-- Validate course counts
SELECT 
    'OLD' as source, COUNT(*) as course_count FROM old_db.course
UNION ALL
SELECT 
    'NEW' as source, COUNT(*) as course_offering_count FROM new_db.course_offerings;

-- Validate grade counts
SELECT 
    'OLD' as source, COUNT(*) as grade_count FROM old_db.journal_details
UNION ALL
SELECT 
    'NEW' as source, COUNT(*) as grade_count FROM new_db.grades;

-- Validate referential integrity
SELECT 
    'Students with valid users' as check,
    COUNT(*) 
FROM new_db.students s
JOIN new_db.users u ON s.user_id = u.id;

SELECT 
    'Course offerings with valid courses' as check,
    COUNT(*) 
FROM new_db.course_offerings co
JOIN new_db.courses c ON co.course_id = c.id;

-- Find orphaned records
SELECT 'Orphaned students (no user)' as issue, COUNT(*)
FROM new_db.students s
LEFT JOIN new_db.users u ON s.user_id = u.id
WHERE u.id IS NULL;

SELECT 'Orphaned course offerings (no course)' as issue, COUNT(*)
FROM new_db.course_offerings co
LEFT JOIN new_db.courses c ON co.course_id = c.id
WHERE c.id IS NULL;
```

---

## 4. Tables Not Migrated (To Review)

The following tables from old database need review for migration necessity:

### Backup/Duplicate Tables (41 tables)
- `*_backup`, `*_copy`, `*_old` tables → **DO NOT MIGRATE**

### Logging Tables (Keep for historical analysis)
- `error_transaction` (21 GB, 27M rows) → **Archive separately**
- `common_action_log` (1.9 GB, 4.4M rows) → **Archive separately**
- `action_logs` (1.1 GB, 7.3M rows) → **Archive separately**
- `user_enter_logs` (127 MB, 1.3M rows) → **Archive separately**

### System Tables (Migrate selectively)
- `notifications`, `notification_to` → Migrate recent (last 6 months)
- `user_session` → DO NOT migrate (regenerate on login)

### Uncategorized (168 tables - needs analysis)
- Review each table in old database
- Determine business value
- Migrate if critical, archive if historical, drop if obsolete

---

## 5. Migration Timeline

### Phase 1: Preparation (Week 1-2)
- Create new database schema
- Set up migration scripts
- Create UUID mapping tables
- Test on small dataset

### Phase 2: Core Data Migration (Week 3-4)
- Migrate users, persons
- Migrate students, teachers
- Migrate organizations
- Validate data integrity

### Phase 3: Academic Data Migration (Week 5-6)
- Migrate courses, course offerings
- Migrate enrollments
- Migrate assessments and grades
- Validate academic data

### Phase 4: Validation & Testing (Week 7-8)
- Run all validation queries
- Test API compatibility
- Performance testing
- Fix issues

### Phase 5: Cutover (Week 9)
- Final data sync
- Switch application to new database
- Monitor for issues
- Rollback plan ready

---

## 6. Rollback Strategy

```sql
-- Backup old database
pg_dump -U postgres -h localhost edu > edu_backup_$(date +%Y%m%d).sql

-- If migration fails, restore
psql -U postgres -h localhost edu_v2 < edu_backup_20251003.sql

-- Revert application connection strings
-- Restart services
```

---

**Document Status:** Draft v1.0  
**Next Steps:** Review mapping, test migration scripts, validate with stakeholders
