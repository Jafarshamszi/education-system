# Comprehensive LMS Database Redesign Documentation
## Baku Business University Learning Management System

---

## Executive Summary

This document provides a complete blueprint for redesigning the Baku Business University LMS database from its current state (355 tables with 0 foreign key relationships) to a modern, scalable, and secure relational database structure. The design supports multilingual operations (Azerbaijani, Russian, English), comprehensive role-based access control, and follows international LMS best practices.

---

## 1. Current System Analysis

### Critical Issues Identified
- **Zero Foreign Key Constraints**: 355 tables without any FK relationships
- **Data Integrity Risks**: No referential integrity enforcement
- **Inconsistent Naming**: Mixed snake_case and camelCase conventions
- **Redundant Tables**: 41 backup/duplicate tables
- **Missing Indexes**: No indexes on foreign key columns
- **Security Vulnerabilities**: Personal data stored without proper access control

### Core Data Statistics
- Users: 6,990
- Students: 6,507
- Teachers: 464
- Courses: 8,392
- Education Groups: 419

---

## 2. Proposed Database Architecture

### 2.1 Core Design Principles

#### Normalization Strategy
- **3NF (Third Normal Form)** for transactional data
- **Selective denormalization** for reporting tables
- **Temporal data** for audit trails and historical records

#### Naming Conventions
```sql
-- Strict snake_case convention
-- Table names: plural, lowercase
-- Primary keys: id (uuid)
-- Foreign keys: [referenced_table_singular]_id
-- Timestamps: created_at, updated_at, deleted_at
-- Boolean fields: is_[state], has_[property], can_[action]
```

#### Data Types Standards
- **UUIDs** for primary keys (security and distribution)
- **JSONB** for flexible metadata and settings
- **TEXT** for variable-length strings (no VARCHAR limits)
- **TIMESTAMPTZ** for all datetime fields
- **ENUM** types for fixed value sets

### 2.2 Security Architecture

#### Encryption Strategy
- **At-rest encryption** for entire database
- **Column-level encryption** for sensitive data (SSN, passport numbers)
- **Hashed passwords** using bcrypt with salt rounds >= 12

#### Access Control
- **Row-Level Security (RLS)** policies
- **Role-based permissions** at database level
- **Audit logging** for all data modifications

---

## 3. Database Schema Design

### 3.1 Core Module Structure

```
┌─────────────────────────────────────────────────┐
│                  CORE MODULES                    │
├─────────────────────────────────────────────────┤
│ 1. Identity & Access Management (IAM)           │
│ 2. Academic Structure                           │
│ 3. Course Management                             │
│ 4. Assessment & Grading                         │
│ 5. Scheduling & Calendar                        │
│ 6. Communication & Notifications                │
│ 7. Reporting & Analytics                        │
│ 8. System Configuration                         │
└─────────────────────────────────────────────────┘
```

### 3.2 Detailed Schema Design

#### Module 1: Identity & Access Management

```sql
-- Core user table (single source of truth)
users (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username            text UNIQUE NOT NULL,
    email               text UNIQUE NOT NULL,
    email_verified      boolean DEFAULT false,
    password_hash       text NOT NULL,
    mfa_secret          text, -- encrypted
    mfa_enabled         boolean DEFAULT false,
    is_active           boolean DEFAULT true,
    is_locked           boolean DEFAULT false,
    failed_login_count  integer DEFAULT 0,
    last_login_at       timestamptz,
    password_changed_at timestamptz,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    deleted_at          timestamptz, -- soft delete
    metadata            jsonb DEFAULT '{}'::jsonb
)

-- Personal information (encrypted sensitive fields)
persons (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    first_name          text NOT NULL,
    last_name           text NOT NULL,
    middle_name         text,
    first_name_az       text, -- Azerbaijani
    last_name_az        text,
    first_name_ru       text, -- Russian
    last_name_ru        text,
    date_of_birth       date,
    gender              text CHECK (gender IN ('male', 'female', 'other', 'prefer_not_to_say')),
    nationality         text,
    national_id         text, -- encrypted
    passport_number     text, -- encrypted
    phone_primary       text,
    phone_secondary     text,
    address             jsonb, -- structured address data
    emergency_contact   jsonb, -- encrypted
    photo_url           text,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Role definitions
roles (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                text UNIQUE NOT NULL, -- RECTOR, DEAN, TEACHER, STUDENT, etc.
    name                jsonb NOT NULL, -- {"az": "Rektor", "en": "Rector", "ru": "Ректор"}
    description         jsonb,
    level               integer NOT NULL, -- hierarchy level
    is_system           boolean DEFAULT false, -- cannot be deleted
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- User role assignments with temporal validity
user_roles (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid REFERENCES users(id) ON DELETE CASCADE,
    role_id             uuid REFERENCES roles(id) ON DELETE RESTRICT,
    organization_unit_id uuid REFERENCES organization_units(id),
    valid_from          timestamptz DEFAULT CURRENT_TIMESTAMP,
    valid_until         timestamptz,
    assigned_by         uuid REFERENCES users(id),
    reason              text,
    is_primary          boolean DEFAULT false,
    UNIQUE(user_id, role_id, organization_unit_id) WHERE valid_until IS NULL
)

-- Granular permissions
permissions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    resource            text NOT NULL, -- grades, courses, users, etc.
    action              text NOT NULL, -- create, read, update, delete, approve
    scope               text, -- own, department, faculty, university
    conditions          jsonb, -- additional conditions
    UNIQUE(resource, action, scope)
)

-- Role-permission mappings
role_permissions (
    role_id             uuid REFERENCES roles(id) ON DELETE CASCADE,
    permission_id       uuid REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
)
```

#### Module 2: Academic Structure

```sql
-- University organizational structure
organization_units (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id           uuid REFERENCES organization_units(id),
    type                text NOT NULL CHECK (type IN ('university', 'school', 'faculty', 'department', 'program', 'center')),
    code                text UNIQUE NOT NULL,
    name                jsonb NOT NULL, -- multilingual
    description         jsonb,
    established_date    date,
    head_user_id        uuid REFERENCES users(id),
    deputy_user_ids     uuid[], -- array of deputy heads
    contact_info        jsonb,
    settings            jsonb DEFAULT '{}'::jsonb,
    is_active           boolean DEFAULT true,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Academic programs (Bachelor's, Master's, PhD)
academic_programs (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_unit_id uuid REFERENCES organization_units(id),
    code                text UNIQUE NOT NULL,
    name                jsonb NOT NULL, -- multilingual
    degree_type         text NOT NULL CHECK (degree_type IN ('bachelor', 'master', 'phd', 'certificate')),
    duration_years      numeric(2,1),
    total_credits       integer NOT NULL,
    language_of_instruction text[], -- ['az', 'en', 'ru']
    accreditation_info  jsonb,
    curriculum          jsonb, -- structured curriculum data
    admission_requirements jsonb,
    is_active           boolean DEFAULT true,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Academic terms/semesters
academic_terms (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_year       text NOT NULL, -- "2024-2025"
    term_type           text NOT NULL CHECK (term_type IN ('fall', 'spring', 'summer', 'winter')),
    term_number         integer NOT NULL,
    start_date          date NOT NULL,
    end_date            date NOT NULL,
    registration_start  date,
    registration_end    date,
    add_drop_deadline   date,
    withdrawal_deadline date,
    grade_submission_deadline date,
    is_current          boolean DEFAULT false,
    settings            jsonb DEFAULT '{}'::jsonb,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(academic_year, term_type)
)

-- Student enrollments
students (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    student_number      text UNIQUE NOT NULL,
    academic_program_id uuid REFERENCES academic_programs(id),
    enrollment_date     date NOT NULL,
    expected_graduation_date date,
    actual_graduation_date date,
    status              text NOT NULL CHECK (status IN ('active', 'inactive', 'suspended', 'graduated', 'withdrawn', 'expelled')),
    study_mode          text CHECK (study_mode IN ('full_time', 'part_time', 'distance', 'hybrid')),
    funding_type        text CHECK (funding_type IN ('state_funded', 'self_funded', 'scholarship', 'sponsored')),
    gpa                 numeric(3,2),
    total_credits_earned integer DEFAULT 0,
    academic_advisor_id uuid REFERENCES users(id),
    thesis_advisor_id   uuid REFERENCES users(id),
    notes               text,
    metadata            jsonb DEFAULT '{}'::jsonb,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Faculty/Staff members
staff_members (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    employee_number     text UNIQUE NOT NULL,
    organization_unit_id uuid REFERENCES organization_units(id),
    position_title      jsonb NOT NULL, -- multilingual
    employment_type     text CHECK (employment_type IN ('full_time', 'part_time', 'contract', 'visiting')),
    hire_date           date NOT NULL,
    contract_end_date   date,
    academic_rank       text, -- professor, associate_professor, assistant_professor, lecturer
    administrative_role text, -- rector, vice_rector, dean, vice_dean, head_of_department
    office_location     text,
    office_hours        jsonb, -- structured schedule
    research_interests  text[],
    qualifications      jsonb,
    is_active           boolean DEFAULT true,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)
```

#### Module 3: Course Management

```sql
-- Course catalog (master course definitions)
courses (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                text UNIQUE NOT NULL,
    name                jsonb NOT NULL, -- multilingual
    description         jsonb, -- multilingual
    organization_unit_id uuid REFERENCES organization_units(id),
    credit_hours        integer NOT NULL,
    lecture_hours       integer,
    lab_hours           integer,
    tutorial_hours      integer,
    course_level        text CHECK (course_level IN ('undergraduate', 'graduate', 'doctoral')),
    prerequisites       uuid[], -- array of course ids
    corequisites        uuid[],
    syllabus_template   jsonb,
    learning_outcomes   jsonb, -- multilingual
    assessment_methods  jsonb,
    is_active           boolean DEFAULT true,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Course offerings (instances per term)
course_offerings (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id           uuid REFERENCES courses(id),
    academic_term_id    uuid REFERENCES academic_terms(id),
    section_code        text NOT NULL,
    language_of_instruction text NOT NULL CHECK (language_of_instruction IN ('az', 'en', 'ru')),
    max_enrollment      integer NOT NULL,
    current_enrollment  integer DEFAULT 0,
    waitlist_capacity   integer DEFAULT 0,
    delivery_mode       text CHECK (delivery_mode IN ('in_person', 'online', 'hybrid', 'recorded')),
    syllabus            jsonb,
    grading_scheme      jsonb,
    is_published        boolean DEFAULT false,
    enrollment_status   text DEFAULT 'open' CHECK (enrollment_status IN ('open', 'closed', 'waitlist', 'cancelled')),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id, academic_term_id, section_code)
)

-- Teaching assignments
course_instructors (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_offering_id  uuid REFERENCES course_offerings(id) ON DELETE CASCADE,
    instructor_id       uuid REFERENCES users(id),
    role                text DEFAULT 'primary' CHECK (role IN ('primary', 'secondary', 'assistant', 'lab_instructor')),
    assigned_date       timestamptz DEFAULT CURRENT_TIMESTAMP,
    assigned_by         uuid REFERENCES users(id),
    PRIMARY KEY (course_offering_id, instructor_id)
)

-- Student course registrations
course_enrollments (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_offering_id  uuid REFERENCES course_offerings(id),
    student_id          uuid REFERENCES students(id),
    enrollment_date     timestamptz DEFAULT CURRENT_TIMESTAMP,
    enrollment_status   text NOT NULL CHECK (enrollment_status IN ('enrolled', 'waitlisted', 'dropped', 'withdrawn', 'completed')),
    status_changed_date timestamptz,
    grade               text,
    grade_points        numeric(3,2),
    attendance_percentage numeric(5,2),
    is_retake           boolean DEFAULT false,
    notes               text,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_offering_id, student_id) WHERE enrollment_status = 'enrolled'
)

-- Course materials and resources
course_materials (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_offering_id  uuid REFERENCES course_offerings(id) ON DELETE CASCADE,
    title               jsonb NOT NULL, -- multilingual
    description         jsonb,
    material_type       text CHECK (material_type IN ('lecture', 'assignment', 'reading', 'video', 'quiz', 'project', 'other')),
    file_url            text,
    external_url        text,
    is_mandatory        boolean DEFAULT false,
    available_from      timestamptz,
    available_until     timestamptz,
    sequence_order      integer,
    metadata            jsonb DEFAULT '{}'::jsonb,
    uploaded_by         uuid REFERENCES users(id),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)
```

#### Module 4: Assessment & Grading

```sql
-- Assessment definitions
assessments (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_offering_id  uuid REFERENCES course_offerings(id) ON DELETE CASCADE,
    title               jsonb NOT NULL, -- multilingual
    description         jsonb,
    assessment_type     text CHECK (assessment_type IN ('exam', 'quiz', 'assignment', 'project', 'presentation', 'participation', 'lab', 'other')),
    weight_percentage   numeric(5,2) NOT NULL,
    total_marks         numeric(6,2),
    passing_marks       numeric(6,2),
    due_date            timestamptz,
    duration_minutes    integer,
    instructions        jsonb, -- multilingual
    submission_type     text CHECK (submission_type IN ('online', 'in_person', 'paper', 'presentation')),
    allows_late_submission boolean DEFAULT false,
    late_penalty_per_day numeric(5,2),
    max_attempts        integer DEFAULT 1,
    is_group_work       boolean DEFAULT false,
    rubric              jsonb,
    created_by          uuid REFERENCES users(id),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Student submissions
assessment_submissions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id       uuid REFERENCES assessments(id) ON DELETE CASCADE,
    student_id          uuid REFERENCES students(id),
    group_id            uuid, -- for group submissions
    attempt_number      integer DEFAULT 1,
    submission_date     timestamptz DEFAULT CURRENT_TIMESTAMP,
    file_urls           text[],
    submission_text     text,
    is_late             boolean DEFAULT false,
    late_days           integer DEFAULT 0,
    status              text CHECK (status IN ('draft', 'submitted', 'in_review', 'graded', 'returned')),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(assessment_id, student_id, attempt_number)
)

-- Grades and feedback
grades (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id       uuid REFERENCES assessment_submissions(id),
    graded_by           uuid REFERENCES users(id),
    marks_obtained      numeric(6,2),
    percentage          numeric(5,2),
    letter_grade        text,
    feedback            text,
    rubric_scores       jsonb,
    is_final            boolean DEFAULT false,
    graded_at           timestamptz DEFAULT CURRENT_TIMESTAMP,
    approved_by         uuid REFERENCES users(id),
    approved_at         timestamptz,
    grade_history       jsonb[], -- array of previous grades
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Grade appeals
grade_appeals (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    grade_id            uuid REFERENCES grades(id),
    student_id          uuid REFERENCES students(id),
    reason              text NOT NULL,
    supporting_documents text[],
    status              text CHECK (status IN ('pending', 'under_review', 'approved', 'rejected', 'resolved')),
    reviewer_id         uuid REFERENCES users(id),
    review_notes        text,
    original_grade      jsonb,
    revised_grade       jsonb,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    resolved_at         timestamptz
)
```

#### Module 5: Scheduling & Calendar

```sql
-- Class schedules
class_schedules (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_offering_id  uuid REFERENCES course_offerings(id) ON DELETE CASCADE,
    day_of_week         integer CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Sunday
    start_time          time NOT NULL,
    end_time            time NOT NULL,
    room_id             uuid REFERENCES rooms(id),
    schedule_type       text CHECK (schedule_type IN ('lecture', 'lab', 'tutorial', 'seminar')),
    instructor_id       uuid REFERENCES users(id),
    effective_from      date,
    effective_until     date,
    is_recurring        boolean DEFAULT true,
    recurrence_pattern  jsonb, -- for complex patterns
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Rooms and facilities
rooms (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id         uuid REFERENCES buildings(id),
    room_number         text NOT NULL,
    room_type           text CHECK (room_type IN ('classroom', 'lecture_hall', 'lab', 'computer_lab', 'meeting_room', 'auditorium')),
    capacity            integer NOT NULL,
    equipment           text[],
    features            jsonb,
    is_available        boolean DEFAULT true,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(building_id, room_number)
)

-- Buildings
buildings (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                text UNIQUE NOT NULL,
    name                jsonb NOT NULL, -- multilingual
    address             jsonb,
    floors              integer,
    coordinates         point, -- PostgreSQL geographic type
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Academic calendar events
calendar_events (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_term_id    uuid REFERENCES academic_terms(id),
    event_type          text CHECK (event_type IN ('holiday', 'exam', 'registration', 'deadline', 'academic', 'social', 'other')),
    title               jsonb NOT NULL, -- multilingual
    description         jsonb,
    start_datetime      timestamptz NOT NULL,
    end_datetime        timestamptz,
    location            text,
    is_mandatory        boolean DEFAULT false,
    target_audience     text[], -- ['all', 'students', 'faculty', 'staff', specific program codes]
    created_by          uuid REFERENCES users(id),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Attendance tracking
attendance_records (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    class_schedule_id   uuid REFERENCES class_schedules(id),
    student_id          uuid REFERENCES students(id),
    attendance_date     date NOT NULL,
    status              text CHECK (status IN ('present', 'absent', 'late', 'excused', 'sick')),
    check_in_time       timestamptz,
    check_out_time      timestamptz,
    notes               text,
    marked_by           uuid REFERENCES users(id),
    marked_at           timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_schedule_id, student_id, attendance_date)
)
```

#### Module 6: Communication & Notifications

```sql
-- Notification templates
notification_templates (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                text UNIQUE NOT NULL,
    name                text NOT NULL,
    description         text,
    category            text CHECK (category IN ('academic', 'administrative', 'system', 'reminder', 'alert')),
    channels            text[] DEFAULT '{email}', -- email, sms, push, in_app
    subject_template    jsonb, -- multilingual with variables
    body_template       jsonb, -- multilingual with variables
    variables           jsonb, -- expected variables definition
    is_active           boolean DEFAULT true,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Notifications queue
notifications (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id         uuid REFERENCES notification_templates(id),
    recipient_id        uuid REFERENCES users(id),
    channel             text NOT NULL,
    language            text DEFAULT 'az',
    subject             text,
    body                text,
    data                jsonb, -- additional data
    status              text DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'cancelled')),
    priority            integer DEFAULT 5, -- 1=highest, 10=lowest
    scheduled_for       timestamptz,
    sent_at             timestamptz,
    delivered_at        timestamptz,
    read_at             timestamptz,
    error_message       text,
    retry_count         integer DEFAULT 0,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Announcements
announcements (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title               jsonb NOT NULL, -- multilingual
    content             jsonb NOT NULL, -- multilingual
    announcement_type   text CHECK (announcement_type IN ('general', 'urgent', 'academic', 'event', 'maintenance')),
    target_audience     text[], -- role codes or 'all'
    target_units        uuid[], -- organization unit ids
    priority            text DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    publish_date        timestamptz DEFAULT CURRENT_TIMESTAMP,
    expire_date         timestamptz,
    author_id           uuid REFERENCES users(id),
    attachments         text[],
    is_published        boolean DEFAULT true,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Message threads (internal messaging)
message_threads (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject             text NOT NULL,
    category            text CHECK (category IN ('academic', 'administrative', 'personal', 'group')),
    is_group_thread     boolean DEFAULT false,
    created_by          uuid REFERENCES users(id),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    last_message_at     timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Messages
messages (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id           uuid REFERENCES message_threads(id) ON DELETE CASCADE,
    sender_id           uuid REFERENCES users(id),
    content             text NOT NULL,
    attachments         text[],
    is_system_message   boolean DEFAULT false,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    edited_at           timestamptz,
    deleted_at          timestamptz
)

-- Message recipients
message_recipients (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id          uuid REFERENCES messages(id) ON DELETE CASCADE,
    recipient_id        uuid REFERENCES users(id),
    read_at             timestamptz,
    deleted_at          timestamptz,
    PRIMARY KEY (message_id, recipient_id)
)
```

#### Module 7: Reporting & Analytics

```sql
-- Report definitions
report_definitions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                text UNIQUE NOT NULL,
    name                jsonb NOT NULL, -- multilingual
    description         jsonb,
    category            text,
    sql_query           text, -- parameterized query
    parameters          jsonb, -- parameter definitions
    columns             jsonb, -- column definitions
    permissions         text[], -- required permissions
    is_scheduled        boolean DEFAULT false,
    schedule            jsonb, -- cron expression
    output_formats      text[] DEFAULT '{pdf,excel,csv}',
    created_by          uuid REFERENCES users(id),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Generated reports
generated_reports (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    definition_id       uuid REFERENCES report_definitions(id),
    generated_by        uuid REFERENCES users(id),
    parameters_used     jsonb,
    file_url            text,
    format              text,
    row_count           integer,
    generation_time_ms  integer,
    status              text CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message       text,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Audit logs
audit_logs (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid REFERENCES users(id),
    action              text NOT NULL, -- create, update, delete, view, login, logout
    resource_type       text NOT NULL, -- table name
    resource_id         uuid,
    old_values          jsonb,
    new_values          jsonb,
    ip_address          inet,
    user_agent          text,
    session_id          text,
    success             boolean DEFAULT true,
    error_message       text,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- System metrics
system_metrics (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name         text NOT NULL,
    metric_value        numeric,
    metric_unit         text,
    tags                jsonb,
    recorded_at         timestamptz DEFAULT CURRENT_TIMESTAMP
)
```

#### Module 8: System Configuration

```sql
-- Multi-language support
languages (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                text UNIQUE NOT NULL, -- 'az', 'en', 'ru'
    name                text NOT NULL,
    native_name         text NOT NULL,
    direction           text DEFAULT 'ltr' CHECK (direction IN ('ltr', 'rtl')),
    is_active           boolean DEFAULT true,
    is_default          boolean DEFAULT false,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- Translations for system labels
translations (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    key                 text NOT NULL,
    language_code       text REFERENCES languages(code),
    value               text NOT NULL,
    context             text, -- where this translation is used
    is_verified         boolean DEFAULT false,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(key, language_code, context)
)

-- System settings
system_settings (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    category            text NOT NULL,
    key                 text NOT NULL,
    value               jsonb NOT NULL,
    value_type          text CHECK (value_type IN ('string', 'number', 'boolean', 'json', 'array')),
    description         text,
    is_public           boolean DEFAULT false,
    is_editable         boolean DEFAULT true,
    updated_by          uuid REFERENCES users(id),
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, key)
)

-- File uploads tracking
file_uploads (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    original_name       text NOT NULL,
    stored_name         text NOT NULL,
    file_path           text NOT NULL,
    file_size           bigint NOT NULL,
    mime_type           text NOT NULL,
    checksum            text, -- SHA-256
    uploaded_by         uuid REFERENCES users(id),
    resource_type       text,
    resource_id         uuid,
    is_public           boolean DEFAULT false,
    metadata            jsonb,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
)

-- User preferences
user_preferences (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_