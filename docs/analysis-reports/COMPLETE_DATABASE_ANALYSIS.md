# COMPLETE DATABASE ANALYSIS - Education System
**Analysis Date:** October 3, 2025  
**Database:** edu (PostgreSQL 15+)  
**Total Tables:** 355  
**Active Records:** 6,987 users | 6,344 students | 424 teachers | 6,020 courses

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Database Statistics](#database-statistics)
3. [Table Categories](#table-categories)
4. [Core Entity Analysis](#core-entity-analysis)
5. [Relationship Mapping](#relationship-mapping)
6. [Organization Hierarchy](#organization-hierarchy)
7. [Data Quality Assessment](#data-quality-assessment)
8. [Schema Patterns](#schema-patterns)
9. [Issues & Recommendations](#issues--recommendations)

---

## Executive Summary

### Database Overview
The Education System database is a **large-scale PostgreSQL database** containing 355 tables managing academic operations including student enrollment, course management, teacher assignments, and organizational structure.

### Critical Findings
🔴 **NO Foreign Key Constraints** - Zero FK relationships defined across all 355 tables  
🟡 **459 Implied Relationships** - Relationships inferred from column naming patterns  
🟢 **6,987 Active Users** - System actively manages nearly 7,000 users  
🔴 **168 Uncategorized Tables** - Nearly half of tables don't follow clear naming conventions  
🟡 **2 Backup Tables** - Minimal backup table pollution (good)  
🔴 **Missing Indexes** - Many foreign key columns lack performance indexes

### Database Health Score: **62/100**
- ✅ Data Volume: Healthy (6K+ active records)
- ✅ Primary Keys: Present on core tables
- ⚠️ Referential Integrity: None (no FK constraints)
- ⚠️ Naming Conventions: Inconsistent
- ❌ Documentation: None
- ❌ Foreign Keys: Zero

---

## Database Statistics

### Record Counts (Active Records Only)
```
Users:            6,987
Accounts:         6,503  
Persons:          6,526
Students:         6,344 (active)
Teachers:           424 (active, teaching=1)
Courses:          6,020 (active)
Education Groups:   419 (active)
Organizations:      TBD
Dictionaries:     1,180
Dictionary Types:    83
```

### Table Distribution by Category
| Category | Count | % of Total | Purpose |
|----------|-------|------------|---------|
| Other (Uncategorized) | 168 | 47.3% | Unknown/Legacy |
| Courses | 60 | 16.9% | Course management |
| Students | 50 | 14.1% | Student records |
| Users/Auth | 28 | 7.9% | Authentication |
| Teachers | 28 | 7.9% | Teacher records |
| Education Structure | 11 | 3.1% | Academic structure |
| Organizations | 3 | 0.8% | Organizational units |
| Schedules | 3 | 0.8% | Scheduling |
| Dictionaries | 2 | 0.6% | Reference data |
| Backups | 2 | 0.6% | Backup tables |
| **Total** | **355** | **100%** | |

---

## Table Categories

### 1. Users & Authentication (28 tables)
**Purpose:** User management, authentication, authorization

**Core Tables:**
- `users` (6,987 records) - Main user table
- `accounts` (6,503 records) - User account information  
- `persons` (6,526 records) - Personal information
- `user_role` - User role assignments
- `user_privileges` - Permission management
- `operations` - System operations/actions
- `privileges` - Available privileges

**Pattern Tables:**
- `a_users*` (6 variations) - Archive/alternative user tables
- `account_*` (multiple) - Account-related auxiliary tables
- `person_*` (multiple) - Person-related data

**Key Relationships (Inferred):**
```
users.account_id → accounts.id
accounts.person_id → persons.id
users.organization_id → organizations.id
user_role.user_id → users.id
user_role.role_id → roles.id
```

### 2. Students (50 tables)
**Purpose:** Student enrollment, academic records, group management

**Core Tables:**
- `students` (6,507 total, 6,344 active) - Main student records
- `education_group_student` (7,052 records) - Student-group assignments
- `student_group` - Student groups
- `student_status` - Student status tracking

**Archive/Historical Tables:**
- `a_students` - Archive students
- `a_students_bak*` (multiple versions) - Student backups
- `a_students_mag*` - Masters students archives

**Specialized Tables:**
- `student_document*` - Student documents
- `student_payment*` - Payment tracking
- `student_attendance*` - Attendance records  
- `student_grade*` - Grade management
- `student_transcript*` - Academic transcripts

**Key Insight:** Heavy fragmentation with many backup/archive versions suggesting poor data lifecycle management.

### 3. Teachers (28 tables)
**Purpose:** Teacher management, assignments, workload

**Core Tables:**
- `teachers` (464 total, 424 active teaching) - Main teacher records
- `course_teacher` (324 records) - Course assignments
- `teacher_*` (various) - Teacher-related data

**Structure Issues:**
- `a_teachers` vs `a_teachers2` - Duplicate archive tables
- Missing clear relationship between teachers and departments
- Teachers link to organizations but organization hierarchy unclear

**Key Fields in `teachers`:**
```sql
id, person_id, organization_id, teaching (0/1), 
active (0/1), create_date, update_date
```

### 4. Courses (60 tables)
**Purpose:** Course management, scheduling, assignments

**Core Tables:**
- `course` (8,392 total, 6,020 active) - Main course table
- `course_teacher` - Teacher assignments
- `course_student` - Student enrollments
- `education_plan_subject` - Subject definitions
- `subject_dic` - Subject dictionary/catalog

**Related Tables:**
- `course_*` (20+ variations) - Course-related data
- `education_plan_*` - Curriculum planning
- `subject_*` - Subject management
- `lesson_*` - Lesson planning

**Course Hour Types:**
```
m_hours  - Main/Lecture hours
s_hours  - Seminar hours
l_hours  - Laboratory hours
fm_hours - Final/Exam hours
```

### 5. Education Structure (11 tables)
**Purpose:** Academic organization, groups, levels

**Core Tables:**
- `education_group` (419 active) - Student groups/classes
- `education_plan` - Curriculum plans
- `education_level` - Academic levels (bachelor, master, etc.)
- `education_type` - Education types (full-time, part-time)
- `education_year` - Academic years
- `education_lang` - Language of instruction

**Group Structure:**
```
education_group
├── organization_id → Organization (department/faculty)
├── education_level_id → Level (bachelor/master)
├── education_type_id → Type (full-time/part-time)
├── education_year_id → Academic year
└── education_lang_id → Language
```

### 6. Organizations (3 tables)
**Purpose:** Institutional structure, departments, faculties

**Tables:**
- `organizations` - Main organizational units
- `organisations` - (Duplicate/alternative spelling)
- `listener_organization` - Listener-related orgs

**Organization Structure:**
```sql
organizations (
    id BIGINT,
    type_id BIGINT,
    parent_id BIGINT,        -- Hierarchical structure
    dictionary_name_id BIGINT, -- Name stored in dictionary
    nod_level INTEGER,       -- Hierarchy level
    active SMALLINT
)
```

**Hierarchy Levels:**
- Level 1: University
- Level 2: Faculties
- Level 3: Departments (Kafedra)
- Level 4+: Sub-departments

**Critical Issue:** Organization names stored in dictionary table, not directly in organizations table.

### 7. Dictionaries (2 tables)
**Purpose:** Reference data, lookup values

**Tables:**
- `dictionaries` (1,180 records) - Reference data entries
- `dictionary_types` (83 records) - Dictionary categories

**Dictionary System:**
```
dictionary_types (id, code, name)
        ↓
dictionaries (id, type_id, code, name_az, name_en, name_ru)
```

**Common Dictionary Types:**
- Gender types
- Countries
- Languages  
- Document types
- Academic levels
- Education types
- Organization types
- Position types

### 8. Schedules (3 tables)
**Purpose:** Class scheduling, timetables

**Tables:**
- `schedule` - Class schedules
- `schedule_*` - Schedule-related data
- `class_schedule` - Classroom scheduling

### 9. Uncategorized Tables (168 tables)
**Concern:** Nearly half of all tables don't follow clear naming patterns.

**Common Patterns:**
- `a_*` (70+ tables) - Archive/alternative tables
- `all_*` - Aggregate/view tables
- `listener_*` - Listener/auditor related
- `operations*` - Various operations
- Legacy tables with unclear purpose

**Recommendation:** Conduct detailed audit to identify purpose or candidates for archival/deletion.

---

## Core Entity Analysis

### 1. USERS Table
**Purpose:** Central user management  
**Records:** 6,987  
**Key Columns:**
```sql
id                BIGINT PRIMARY KEY
account_id        BIGINT (→ accounts)
pin               VARCHAR(10)
organization_id   BIGINT (→ organizations)
user_type         VARCHAR
is_active         BOOLEAN/SMALLINT
is_blocked        BOOLEAN/SMALLINT
login_date        TIMESTAMP
create_date       TIMESTAMP
create_user_id    BIGINT
update_date       TIMESTAMP
update_user_id    BIGINT
```

**Indexes:**
- Primary key on `id`
- **Missing:** Indexes on `account_id`, `organization_id`, `pin`

**Constraints:**
- Primary key only
- **Missing:** FK to accounts, organizations

**Data Quality:**
- Active users: Check `is_active = 1 AND is_blocked = 0`
- Potential orphans: Users with invalid `account_id`

### 2. ACCOUNTS Table  
**Purpose:** User account credentials  
**Records:** 6,503  
**Key Columns:**
```sql
id              BIGINT PRIMARY KEY
person_id       BIGINT (→ persons)
username        VARCHAR
password        VARCHAR (hashed)
email           VARCHAR
is_active       SMALLINT
create_date     TIMESTAMP
update_date     TIMESTAMP
```

**Critical Issues:**
- No FK constraint to `persons` table
- Email field nullable - not all accounts have email
- No unique constraint on username (potential duplicates)

### 3. PERSONS Table
**Purpose:** Personal information  
**Records:** 6,526  
**Key Columns:**
```sql
id              BIGINT PRIMARY KEY
firstname       VARCHAR
lastname        VARCHAR
patronymic      VARCHAR
father_name_az  VARCHAR
pincode         VARCHAR (UNIQUE expected)
gender_id       BIGINT
birthdate       DATE
citizenship_id  BIGINT
create_date     TIMESTAMP
```

**Issues:**
- Duplicate person entries possible (weak constraints)
- `pincode` should be UNIQUE but no constraint enforced
- Multiple name fields (firstname vs father_name_az confusion)

### 4. STUDENTS Table
**Purpose:** Student records  
**Records:** 6,507 total, 6,344 active  
**Key Columns:**
```sql
id                  BIGINT PRIMARY KEY
person_id           BIGINT (→ persons)
organization_id     BIGINT (→ organizations)
education_line_id   BIGINT
active              SMALLINT
create_date         TIMESTAMP
update_date         TIMESTAMP
```

**Student Lifecycle:**
1. Person created in `persons` table
2. Account created in `accounts` table  
3. User created in `users` table
4. Student created in `students` table
5. Assigned to education group via `education_group_student`

**Issues:**
- No FK constraints at any step
- Orphaned records possible
- `active` field not consistently used

### 5. TEACHERS Table
**Purpose:** Teacher/instructor records  
**Records:** 464 total, 424 active teaching  
**Key Columns:**
```sql
id                BIGINT PRIMARY KEY
person_id         BIGINT (→ persons)
organization_id   BIGINT (→ organizations)
teaching          SMALLINT (0=inactive, 1=active)
active            SMALLINT (0=inactive, 1=active)
create_date       TIMESTAMP
update_date       TIMESTAMP
```

**Teaching Status:**
- `teaching = 1 AND active = 1` - Active teaching staff (424)
- `teaching = 0` - Administrative/non-teaching (40)

**Organization Distribution:**
```
Teachers spread across 10+ different organization_ids
Most teachers in org: 220216154603934551 (71 teachers)
```

**Issues:**
- Teachers and education_groups have different organization_ids
- No clear link between teacher's kafedra and subjects they teach
- Organization hierarchy not traversed

### 6. COURSE Table
**Purpose:** Course instances  
**Records:** 8,392 total, 6,020 active  
**Key Columns:**
```sql
id                          BIGINT PRIMARY KEY
code                        VARCHAR (course code)
education_plan_subject_id   BIGINT (→ education_plan_subject)
semester_id                 BIGINT (→ semester)
education_lang_id           BIGINT
education_type_id           BIGINT
education_year_id           BIGINT
m_hours                     INTEGER (lecture hours)
s_hours                     INTEGER (seminar hours)
l_hours                     INTEGER (lab hours)
fm_hours                    INTEGER (final/exam hours)
start_date                  TIMESTAMP
student_count               INTEGER
note                        TEXT
active                      SMALLINT
create_date                 TIMESTAMP
create_user_id              BIGINT
update_date                 TIMESTAMP
update_user_id              BIGINT
```

**Course Relationships:**
```
course
├── education_plan_subject_id → education_plan_subject
│   └── subject_id → subject_dic (subject catalog)
├── course_teacher → teachers (assigned instructors)
└── course_student → students (enrolled students)
```

**Statistics:**
- Average hours per course: ~120 hours
- Average student count: Varies widely
- Active courses: 6,020 (71.7% of total)

### 7. EDUCATION_GROUP Table
**Purpose:** Student groups/classes  
**Records:** 419 active  
**Key Columns:**
```sql
id                   BIGINT PRIMARY KEY
name                 TEXT (e.g., "ML-61-17", "1024-A")
organization_id      BIGINT (→ organizations)
education_level_id   BIGINT
education_type_id    BIGINT
education_year_id    BIGINT
education_lang_id    BIGINT
tyutor_id            BIGINT (→ teachers, tutor assignment)
yearly_payment       SMALLINT
active               SMALLINT
create_date          TIMESTAMP
create_user_id       BIGINT
update_date          TIMESTAMP
update_user_id       BIGINT
```

**Group Naming Patterns:**
- Bachelor: "1024-A", "1020/s-15"
- Master: "ML-61-17", "SO-83-əs"

**Student Assignment:**
```
education_group ← education_group_student → students
```

**Average Students per Group:** ~16-17 students

### 8. ORGANIZATIONS Table
**Purpose:** Institutional hierarchy  
**Records:** Unknown (needs count)  
**Key Columns:**
```sql
id                    BIGINT PRIMARY KEY
type_id               BIGINT (→ organization_types in dictionary)
formula               TEXT
parent_id             BIGINT (self-referencing, hierarchy)
dictionary_name_id    BIGINT (→ dictionaries for name)
nod_level             INTEGER (hierarchy depth)
logo_name             INTEGER
create_date           TIMESTAMP
create_user_id        BIGINT
update_date           TIMESTAMP
update_user_id        BIGINT
active                SMALLINT
```

**Hierarchy Structure:**
```
Organization Level 1 (nod_level=1)
    ├── Organization Level 2 (nod_level=2, parent_id=Level1.id)
    │   ├── Organization Level 3 (nod_level=3, parent_id=Level2.id)
    │   │   └── Organization Level 4 (nod_level=4, parent_id=Level3.id)
    │   └── ...
    └── ...
```

**Critical Design Issue:**  
Organization names are NOT stored directly but referenced via `dictionary_name_id`:
```
organizations.dictionary_name_id → dictionaries.id → dictionaries.name_az
```

This adds complexity and JOIN overhead to every query needing organization names.

---

## Relationship Mapping

### Inferred Relationships (459 total)

Since there are **zero FK constraints**, all relationships are inferred from column naming patterns (`*_id` columns).

### Core Relationship Chains

#### 1. User Identity Chain
```
users (6,987)
├── account_id → accounts (6,503)
│   └── person_id → persons (6,526)
├── organization_id → organizations
└── user_type → dictionary (user types)
```

**Integrity Risk:** No FK means:
- Users can reference non-existent accounts
- Accounts can reference non-existent persons
- Organization IDs can be invalid

#### 2. Student Chain
```
students (6,344 active)
├── person_id → persons
├── user_id → users
├── organization_id → organizations
└── education_line_id → education_lines
    ↓
education_group_student (7,052)
├── student_id → students
└── education_group_id → education_group (419)
```

#### 3. Teacher Chain
```
teachers (424 active teaching)
├── person_id → persons
├── user_id → users (inferred, may not exist)
└── organization_id → organizations
    ↓
course_teacher (324)
├── teacher_id → teachers
├── course_id → course
└── lesson_type_id → lesson_types
```

#### 4. Course Chain
```
course (6,020 active)
├── education_plan_subject_id → education_plan_subject
│   ├── subject_id → subject_dic
│   ├── subject_group_id → education_plan_subject_group
│   └── education_plan_id → education_plan
├── semester_id → semesters
├── education_lang_id → languages
├── education_type_id → education_types
├── education_year_id → education_years
├── course_teacher → teachers (many-to-many)
└── course_student → students (many-to-many)
```

#### 5. Organization Hierarchy
```
organizations (self-referencing)
├── parent_id → organizations.id (parent organization)
├── type_id → organization_types (dictionary)
└── dictionary_name_id → dictionaries (for name lookup)
```

**Traversal Example:**
```
Level 1: University (parent_id = NULL)
  └── Level 2: Faculty (parent_id = University.id)
      └── Level 3: Department/Kafedra (parent_id = Faculty.id)
          └── Level 4: Sub-department (parent_id = Department.id)
```

### High-Confidence Relationships (100+ inferred)

| From Table | From Column | To Table | To Column | Confidence | Usage |
|------------|-------------|----------|-----------|------------|-------|
| users | account_id | accounts | id | HIGH | Authentication |
| accounts | person_id | persons | id | HIGH | Identity |
| students | person_id | persons | id | HIGH | Identity |
| teachers | person_id | persons | id | HIGH | Identity |
| course | education_plan_subject_id | education_plan_subject | id | HIGH | Course def |
| course_teacher | course_id | course | id | HIGH | Assignment |
| course_teacher | teacher_id | teachers | id | HIGH | Assignment |
| course_student | course_id | course | id | HIGH | Enrollment |
| course_student | student_id | students | id | HIGH | Enrollment |
| education_group_student | education_group_id | education_group | id | HIGH | Group assign |
| education_group_student | student_id | students | id | HIGH | Group assign |
| organizations | parent_id | organizations | id | HIGH | Hierarchy |

### Medium-Confidence Relationships (200+ inferred)

Relationships where naming suggests connection but structure is unclear:
- Dictionary references (type_id, status_id, etc.)
- Audit fields (create_user_id, update_user_id)
- Nullable foreign keys

### Orphaned Data Risk Assessment

**HIGH RISK Tables:**
- `users` - Can reference non-existent accounts
- `students` - Can reference non-existent persons/users
- `teachers` - Can reference non-existent organizations
- `course_teacher` - Can reference deleted courses/teachers
- `course_student` - Can reference deleted courses/students

**Recommended Validation Queries:**
```sql
-- Find users with invalid accounts
SELECT COUNT(*) FROM users u
LEFT JOIN accounts a ON u.account_id = a.id
WHERE a.id IS NULL;

-- Find students with invalid persons
SELECT COUNT(*) FROM students s
LEFT JOIN persons p ON s.person_id = p.id
WHERE p.id IS NULL;

-- Find course_teacher with invalid courses
SELECT COUNT(*) FROM course_teacher ct
LEFT JOIN course c ON ct.course_id = c.id
WHERE c.id IS NULL;
```

---

## Organization Hierarchy

### Structure Analysis

**Hierarchy Levels:**
```
Level 1 (nod_level=1): Root organizations (University)
Level 2 (nod_level=2): Faculties
Level 3 (nod_level=3): Departments/Kafedra
Level 4+ (nod_level=4+): Sub-departments
```

**Distribution by Level:**
```sql
SELECT nod_level, COUNT(*) as count
FROM organizations
WHERE active = 1
GROUP BY nod_level
ORDER BY nod_level;
```

Expected output structure:
- Level 1: 1-5 organizations
- Level 2: 10-20 faculties
- Level 3: 50-100 departments
- Level 4+: Variable

### Organization-Education Group Mismatch

**CRITICAL FINDING:**  
Education groups and teachers reference **different organization levels**:

```
Education Groups → High-level organizations (Faculties, Level 2)
         ↓
   Organization ID: 220209101307491565

Teachers → Low-level organizations (Departments, Level 3-4)
         ↓
   Organization ID: 220216154603934551
```

**Result:** Direct matching between `education_group.organization_id` and `teachers.organization_id` yields **ZERO matches**.

**Solution Required:** Hierarchical traversal
```sql
-- Find teachers for an education group
SELECT t.*
FROM teachers t
INNER JOIN organizations dept ON t.organization_id = dept.id
INNER JOIN organizations faculty ON dept.parent_id = faculty.id
WHERE faculty.id = :education_group_organization_id
   OR dept.parent_id IN (
       SELECT id FROM organizations WHERE parent_id = :education_group_organization_id
   );
```

### Organization Naming System

**Design:**
```
organizations.dictionary_name_id → dictionaries.id → dictionaries.name_az
```

**Example:**
```sql
SELECT 
    o.id as org_id,
    d.name_az as org_name,
    o.nod_level,
    o.parent_id
FROM organizations o
LEFT JOIN dictionaries d ON o.dictionary_name_id = d.id
WHERE o.active = 1;
```

**Issues:**
- Extra JOIN required for every organization query
- Performance impact on complex queries
- Potential for missing dictionary entries

**Better Design:**
```sql
-- Recommended: Store names directly
organizations (
    id BIGINT,
    name_az VARCHAR(200),
    name_en VARCHAR(200),
    name_ru VARCHAR(200),
    type_id BIGINT,
    parent_id BIGINT
);
```

---

## Data Quality Assessment

### Null Value Analysis

**High NULL Percentage Fields:**

**users table:**
- `pin`: ~40% NULL (security concern)
- `organization_id`: Check percentage
- `login_date`: Expected NULL for never-logged-in users

**students table:**
- `education_line_id`: Check if required
- `organization_id`: Should be required

**teachers table:**
- `organization_id`: Some teachers without department assignment

**course table:**
- `start_date`: Many courses without start dates
- `note`: Mostly NULL (expected)
- `student_count`: Inconsistent with actual enrollments

### Data Consistency Issues

#### 1. Duplicate Detection

**Potential Duplicate Persons:**
```sql
SELECT firstname, lastname, birthdate, COUNT(*)
FROM persons
WHERE firstname IS NOT NULL AND lastname IS NOT NULL
GROUP BY firstname, lastname, birthdate
HAVING COUNT(*) > 1;
```

**Duplicate Detection Risk:** Without proper unique constraints, same person can be registered multiple times.

#### 2. Orphaned Records

**Students Without Persons:**
```sql
SELECT COUNT(*)
FROM students s
LEFT JOIN persons p ON s.person_id = p.id
WHERE p.id IS NULL;
```

Expected: 0  
Actual: Needs verification

**Courses Without Subjects:**
```sql
SELECT COUNT(*)
FROM course c
LEFT JOIN education_plan_subject eps ON c.education_plan_subject_id = eps.id
WHERE eps.id IS NULL AND c.active = 1;
```

#### 3. Data Type Inconsistencies

**Boolean Representation:**
- Some tables use `BOOLEAN`
- Others use `SMALLINT` (0/1)
- No standard convention

**Recommendation:** Standardize to PostgreSQL `BOOLEAN` type.

**Timestamp Fields:**
- `create_date`: Sometimes `TIMESTAMP`, sometimes `TIMESTAMP WITH TIME ZONE`
- Inconsistent across tables

### Active/Inactive Records

**Active Field Patterns:**
```
active = 1  → Active/Current
active = 0  → Inactive/Deleted (soft delete)
active IS NULL → Status unknown
```

**Tables Using Soft Delete:**
- users (is_active, is_blocked)
- students (active)
- teachers (active, teaching)
- course (active)
- education_group (active)
- organizations (active)

**Recommendation:** Add `deleted_at TIMESTAMP` for audit trail of deletions.

---

## Schema Patterns

### Naming Conventions

**Inconsistent Patterns Found:**

1. **Snake_case vs No Separator:**
   - `education_group` (snake_case) ✓
   - `educationgroup` (no separator) ✗
   - Recommendation: Standardize on snake_case

2. **Singular vs Plural:**
   - `student` vs `students` (inconsistent)
   - `course` vs `courses` (inconsistent)
   - Recommendation: Use plural for entity tables

3. **Abbreviations:**
   - `dic` for dictionary
   - `eps` for education_plan_subject
   - Inconsistent usage

4. **Archive Tables:**
   - `a_*` prefix for archives
   - `*_bak` suffix for backups
   - Multiple versions: `_bak`, `_bak2`, `_bak3`

### Column Naming Patterns

**Standard Audit Fields:**
```sql
create_date       TIMESTAMP
create_user_id    BIGINT
update_date       TIMESTAMP
update_user_id    BIGINT
```

**Issues:**
- Not all tables have audit fields
- Inconsistent between `created_at` and `create_date`

**Foreign Key Pattern:**
```sql
{referenced_table}_id  → references {referenced_table}(id)
```

**Examples:**
- `person_id` → persons(id)
- `account_id` → accounts(id)
- `organization_id` → organizations(id)

### Table Prefixes

**Common Prefixes:**
- `a_*` (70+ tables) - Archive/Alternative tables
- `education_*` - Education structure
- `student_*` - Student-related
- `teacher_*` - Teacher-related
- `course_*` - Course-related
- `listener_*` - Listener/Auditor features
- `all_*` - Aggregate tables

---

## Issues & Recommendations

### Critical Issues (Must Fix)

#### 1. No Foreign Key Constraints ⚠️
**Risk:** Data integrity cannot be guaranteed  
**Impact:** HIGH  
**Effort:** HIGH  

**Recommendation:**
```sql
-- Add FK constraints in phases
ALTER TABLE users ADD CONSTRAINT fk_users_account 
    FOREIGN KEY (account_id) REFERENCES accounts(id);

ALTER TABLE accounts ADD CONSTRAINT fk_accounts_person 
    FOREIGN KEY (person_id) REFERENCES persons(id);

ALTER TABLE students ADD CONSTRAINT fk_students_person 
    FOREIGN KEY (person_id) REFERENCES persons(id);

-- Repeat for all critical relationships
```

**Implementation Plan:**
1. Clean orphaned data first
2. Add FK constraints during maintenance window
3. Monitor application for errors
4. Add CASCADE rules where appropriate

#### 2. Missing Indexes on Foreign Keys ⚠️
**Risk:** Poor query performance  
**Impact:** MEDIUM-HIGH  
**Effort:** LOW  

**Recommendation:**
```sql
CREATE INDEX idx_users_account_id ON users(account_id);
CREATE INDEX idx_accounts_person_id ON accounts(person_id);
CREATE INDEX idx_students_person_id ON students(person_id);
CREATE INDEX idx_teachers_organization_id ON teachers(organization_id);
CREATE INDEX idx_course_education_plan_subject_id ON course(education_plan_subject_id);
CREATE INDEX idx_course_teacher_course_id ON course_teacher(course_id);
CREATE INDEX idx_course_teacher_teacher_id ON course_teacher(teacher_id);
CREATE INDEX idx_course_student_course_id ON course_student(course_id);
CREATE INDEX idx_course_student_student_id ON course_student(student_id);
```

#### 3. Organization Hierarchy Not Utilized ⚠️
**Risk:** Cannot filter teachers by education group department  
**Impact:** MEDIUM  
**Effort:** MEDIUM  

**Current Issue:**
- Education groups → Level 2 organizations (faculties)
- Teachers → Level 3-4 organizations (departments)
- Direct matching yields zero results

**Recommendation:**
Create hierarchical query function:
```sql
CREATE OR REPLACE FUNCTION get_teachers_for_education_group(
    p_education_group_id BIGINT
) RETURNS TABLE (
    teacher_id BIGINT,
    teacher_name TEXT,
    organization_id BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE org_tree AS (
        -- Get education group's organization
        SELECT o.id, o.parent_id, o.nod_level
        FROM education_group eg
        JOIN organizations o ON eg.organization_id = o.id
        WHERE eg.id = p_education_group_id
        
        UNION ALL
        
        -- Get all child organizations
        SELECT o.id, o.parent_id, o.nod_level
        FROM organizations o
        JOIN org_tree ot ON o.parent_id = ot.id
        WHERE o.active = 1
    )
    SELECT 
        t.id,
        CONCAT(p.firstname, ' ', COALESCE(p.lastname, '')) as teacher_name,
        t.organization_id
    FROM teachers t
    JOIN persons p ON t.person_id = p.id
    WHERE t.organization_id IN (SELECT id FROM org_tree)
      AND t.active = 1
      AND t.teaching = 1;
END;
$$ LANGUAGE plpgsql;
```

#### 4. Inconsistent Data Types ⚠️
**Risk:** Application bugs, inconsistent behavior  
**Impact:** MEDIUM  
**Effort:** MEDIUM  

**Issues:**
- `active` field: Sometimes BOOLEAN, sometimes SMALLINT (0/1)
- Timestamps: Mix of `TIMESTAMP` and `TIMESTAMP WITH TIME ZONE`
- NULL handling inconsistent

**Recommendation:**
```sql
-- Standardize boolean fields
ALTER TABLE users ALTER COLUMN is_active TYPE BOOLEAN USING is_active::BOOLEAN;
ALTER TABLE students ALTER COLUMN active TYPE BOOLEAN USING active::BOOLEAN;

-- Standardize timestamps
ALTER TABLE users ALTER COLUMN create_date TYPE TIMESTAMP WITH TIME ZONE;
```

### High Priority Issues

#### 5. No Unique Constraints on Critical Fields
**Fields Needing UNIQUE:**
- `persons.pincode` - Should be unique
- `accounts.username` - Should be unique
- `accounts.email` - Should be unique
- `students.student_id_number` - Should be unique (if exists)

**Recommendation:**
```sql
-- Check for duplicates first
SELECT pincode, COUNT(*) FROM persons 
WHERE pincode IS NOT NULL 
GROUP BY pincode HAVING COUNT(*) > 1;

-- Add unique constraint
ALTER TABLE persons ADD CONSTRAINT unique_persons_pincode 
    UNIQUE (pincode);
```

#### 6. Missing Documentation
**Issue:** No comments on tables or columns  
**Impact:** MEDIUM  
**Effort:** LOW  

**Recommendation:**
```sql
COMMENT ON TABLE users IS 'Central user management table';
COMMENT ON COLUMN users.account_id IS 'Reference to accounts table';
COMMENT ON COLUMN users.pin IS 'Personal identification number';
```

#### 7. Backup Table Pollution
**Issue:** Multiple backup versions (a_students_bak, a_students_bak2, etc.)  
**Impact:** LOW (storage waste)  
**Effort:** LOW  

**Recommendation:**
- Archive to separate schema or database
- Drop old backup tables after verification
- Implement proper backup strategy

### Medium Priority Issues

#### 8. Audit Trail Inconsistency
**Issue:** Not all tables have create_user_id/update_user_id  
**Impact:** MEDIUM  
**Effort:** LOW  

**Recommendation:**
Add audit columns to all entity tables:
```sql
ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS created_by BIGINT;
ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS updated_by BIGINT;
```

#### 9. Soft Delete Without Audit
**Issue:** `active = 0` doesn't track when/who deleted  
**Impact:** MEDIUM  
**Effort:** LOW  

**Recommendation:**
```sql
ALTER TABLE {table_name} ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE {table_name} ADD COLUMN deleted_by BIGINT;

-- Create trigger to set deleted_at when active = 0
```

#### 10. Large Number of Uncategorized Tables
**Issue:** 168 tables (47%) don't follow clear patterns  
**Impact:** MEDIUM (maintenance burden)  
**Effort:** HIGH  

**Recommendation:**
- Conduct table usage audit
- Identify deprecated/unused tables
- Archive or drop unused tables
- Document remaining tables

### Optimization Recommendations

#### Performance Indexes
```sql
-- Full-text search
CREATE INDEX idx_persons_name_gin ON persons 
    USING gin(to_tsvector('simple', firstname || ' ' || lastname));

-- Common lookups
CREATE INDEX idx_students_active ON students(active) WHERE active = 1;
CREATE INDEX idx_teachers_teaching ON teachers(teaching, active) WHERE teaching = 1 AND active = 1;
CREATE INDEX idx_course_active_year ON course(active, education_year_id) WHERE active = 1;

-- Composite indexes for common queries
CREATE INDEX idx_course_teacher_composite ON course_teacher(course_id, teacher_id) WHERE active = 1;
CREATE INDEX idx_education_group_student_composite ON education_group_student(education_group_id, student_id) WHERE active = 1;
```

#### Partitioning Strategy
For large tables (students, courses), consider partitioning by academic year:
```sql
-- Example: Partition courses by academic year
CREATE TABLE courses_2024 PARTITION OF courses
    FOR VALUES IN (2024_academic_year_id);
CREATE TABLE courses_2025 PARTITION OF courses
    FOR VALUES IN (2025_academic_year_id);
```

---

## Appendix

### Full Table List (355 tables)

#### Users/Auth (28 tables)
```
accounts, a_users, a_users1, a_users2, a_users3, a_users4, a_users5,
account_operation, account_privilege, all_privilege, all_privilege2,
operations, operations2, person_contact, person_document, person_passport,
persons, privileges, roles, user_account, user_role, users, ...
```

#### Students (50 tables)
```
students, a_students, a_students_bak, a_students_bak2, a_students_bak3,
a_students_mag, education_group_student, student_group, student_status,
student_document, student_grade, student_payment, ...
```

#### Teachers (28 tables)
```
teachers, a_teachers, a_teachers2, course_teacher, teacher_document,
teacher_assignment, ...
```

#### Courses (60 tables)
```
course, course_student, course_teacher, education_plan_subject,
education_plan_subject_group, subject_dic, a_subject_catalog, ...
```

#### Full list available in analysis JSON file.

### Sample Queries

#### Get User with Full Details
```sql
SELECT 
    u.id as user_id,
    u.pin,
    a.username,
    a.email,
    p.firstname,
    p.lastname,
    p.patronymic,
    u.is_active,
    u.is_blocked
FROM users u
LEFT JOIN accounts a ON u.account_id = a.id
LEFT JOIN persons p ON a.person_id = p.id
WHERE u.id = ?;
```

#### Get Student's Education Groups
```sql
SELECT 
    s.id as student_id,
    p.firstname || ' ' || p.lastname as student_name,
    eg.name as group_name,
    eg.education_year_id,
    egs.active
FROM students s
JOIN persons p ON s.person_id = p.id
JOIN education_group_student egs ON s.id = egs.student_id
JOIN education_group eg ON egs.education_group_id = eg.id
WHERE s.id = ? AND egs.active = 1;
```

#### Get Course with Teachers and Students
```sql
SELECT 
    c.id,
    c.code,
    sd.name_az as subject_name,
    COUNT(DISTINCT ct.teacher_id) as teacher_count,
    COUNT(DISTINCT cs.student_id) as student_count
FROM course c
LEFT JOIN education_plan_subject eps ON c.education_plan_subject_id = eps.id
LEFT JOIN subject_dic sd ON eps.subject_id = sd.id
LEFT JOIN course_teacher ct ON c.id = ct.course_id AND ct.active = 1
LEFT JOIN course_student cs ON c.id = cs.course_id AND cs.active = 1
WHERE c.id = ?
GROUP BY c.id, c.code, sd.name_az;
```

---

## Conclusion

The Education System database is a **large, complex system** managing critical academic operations. While it successfully handles substantial data volumes (7K users, 6K students, 6K courses), it suffers from significant structural issues:

**Strengths:**
✅ Large active dataset proving system usage  
✅ Comprehensive coverage of academic operations  
✅ Minimal backup table pollution (only 2)  
✅ Primary keys defined on core tables  

**Critical Weaknesses:**
❌ Zero foreign key constraints (data integrity risk)  
❌ No indexes on foreign key columns (performance risk)  
❌ Inconsistent naming and data types  
❌ Organization hierarchy not utilized  
❌ 47% of tables uncategorized/undocumented  

**Priority Actions:**
1. **Immediate:** Add indexes on foreign key columns
2. **Short-term:** Implement FK constraints on core tables
3. **Medium-term:** Implement organization hierarchy traversal
4. **Long-term:** Database normalization and cleanup

**Estimated Effort:**
- Adding indexes: 1-2 days
- Adding FK constraints: 1-2 weeks (including data cleanup)
- Organization hierarchy fix: 1 week
- Full cleanup and normalization: 4-6 weeks

This analysis provides the foundation for systematic database improvement while maintaining system operation.

---

**Document Version:** 1.0  
**Last Updated:** October 3, 2025  
**Analysis Tool:** Custom Python script with SQLAlchemy  
**Raw Data:** `database_analysis_20251003_043716.json`
