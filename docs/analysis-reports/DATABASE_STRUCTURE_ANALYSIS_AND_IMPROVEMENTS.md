# LMS Database Structure Analysis & Improvement Plan
**Baku Business University - Learning Management System**

**Date:** October 8, 2025  
**Current Database:** lms (PostgreSQL 15+)  
**Analysis Scope:** Structure completeness, not data migration

---

## Executive Summary

The current LMS database has a **solid foundation** with 36 tables, 55 foreign key constraints, and 196 indexes. However, it is **missing critical features** required for a complete Learning Management System. This document identifies gaps and provides a comprehensive improvement roadmap.

### Current State
- ✅ **Strong Foundation:** Core tables for users, courses, assessments, and enrollments exist
- ✅ **Good Relationships:** 55 foreign key constraints ensure data integrity
- ✅ **Well Indexed:** 196 indexes including 63 unique constraints
- ⚠️ **25 Empty Tables:** Many tables created but not utilized
- ❌ **Missing Features:** No financial system, library, transcripts, advanced messaging
- ❌ **Schema Issues:** Some tables need structural improvements

### Priority Improvements Needed
1. **CRITICAL:** Fix academic_programs linkage (table exists but empty, not connected to students)
2. **CRITICAL:** Add transcript and GPA tracking system
3. **HIGH:** Implement financial/payment system
4. **HIGH:** Add library and resources management
5. **MEDIUM:** Enhance messaging and communication
6. **MEDIUM:** Add advanced assessment features (question banks, rubrics)
7. **LOW:** Add student services tables (advising, counseling, etc.)

---

## 1. Current Database Analysis

### 1.1 Existing Tables Overview

| Category | Tables | Status | Data Count |
|----------|--------|--------|------------|
| **User Management** | users, persons, roles, user_roles, permissions, role_permissions, user_sessions, user_preferences | ✅ Created | 6,490 users, 0 in support tables |
| **Academic Structure** | organization_units, academic_programs, academic_terms | ⚠️ Incomplete | 60 units, 0 programs, 0 terms |
| **Student Data** | students, staff_members | ✅ Populated | 5,959 students, 350 staff |
| **Course Management** | courses, course_offerings, course_enrollments, course_instructors, course_materials | ⚠️ Partial | 883 courses, 7,547 offerings, 191K enrollments |
| **Assessment** | assessments, assessment_submissions, grades, grade_appeals | ✅ Populated | 66K assessments, 64K submissions, 195K grades |
| **Scheduling** | class_schedules, rooms, buildings, calendar_events, attendance_records | ⚠️ Created but empty | 0 records |
| **Communication** | announcements, notifications, notification_templates | ⚠️ Created but empty | 0 records |
| **System** | languages, file_uploads, audit_logs, system_settings, system_metrics, page_views | ⚠️ Created but empty | 0 records |

### 1.2 Schema Quality Assessment

**✅ STRENGTHS:**
- UUID primary keys for security and distribution
- JSONB for multilingual content (az, en, ru)
- Proper timestamp tracking (created_at, updated_at, deleted_at)
- Soft delete support
- Good indexing strategy
- Foreign key constraints enforced
- Check constraints for data validation
- Trigger-based updated_at automation

**❌ WEAKNESSES:**
1. **academic_programs table disconnected** - Students table has academic_program_id but table is empty
2. **academic_terms not used** - Course offerings should link to terms
3. **Grades table design** - Requires assessment_id but should also support course-level grades
4. **No GPA tracking** - Students table has gpa field but no calculation system
5. **Missing prerequisite enforcement** - Courses have prerequisites array but no validation
6. **No waitlist management** - Course_enrollments has 'waitlisted' status but no queue system
7. **Limited file management** - file_uploads exists but no versioning or organization

### 1.3 Missing Critical Features

**❌ COMPLETELY MISSING:**
1. **Transcript System** - No transcript generation, requests, or official records
2. **Financial System** - No tuition, payments, scholarships, or billing
3. **Library System** - No library catalog, checkouts, or resources
4. **Messaging System** - Only announcements, no direct messaging or forums
5. **Question Banks** - No exam question repository or randomization
6. **Degree Audit** - No graduation requirements tracking
7. **Course Prerequisites Validation** - Logic not implemented
8. **Schedule Conflict Detection** - No conflict checking system
9. **Peer Review** - No peer assessment capabilities
10. **Digital Credentials** - No badges, certificates, or verification system

---

## 2. Critical Issues & Solutions

### 2.1 CRITICAL: Academic Programs Disconnection

**Problem:**
```sql
-- Students table references academic_programs
students.academic_program_id → academic_programs.id

-- BUT academic_programs table is EMPTY (0 records)
-- This means all 5,959 students have NULL academic_program_id
```

**Solution:**
```sql
-- Step 1: Populate academic_programs from old database
INSERT INTO academic_programs (
    organization_unit_id,
    code,
    name,
    degree_type,
    duration_years,
    total_credits,
    language_of_instruction
)
SELECT DISTINCT
    ou.id,
    ep.code,
    jsonb_build_object(
        'az', ep.name_az,
        'en', ep.name_en,
        'ru', ep.name_ru
    ),
    CASE ep.education_level
        WHEN 'bachelor' THEN 'bachelor'
        WHEN 'master' THEN 'master'
        WHEN 'phd' THEN 'phd'
        ELSE 'bachelor'
    END,
    ep.duration_years,
    ep.total_credits,
    ARRAY['az']
FROM old_edu.education_plan ep
JOIN organization_units ou ON ou.old_unit_id = ep.faculty_id
WHERE ep.active = 1;

-- Step 2: Update students with correct academic_program_id
UPDATE students s
SET academic_program_id = ap.id
FROM academic_programs ap
WHERE s.metadata->>'old_education_plan_id' = ap.metadata->>'old_plan_id';
```

### 2.2 CRITICAL: Academic Terms Missing

**Problem:**
- academic_terms table is empty
- course_offerings don't link to specific terms
- No semester/term management

**Solution:**
```sql
-- Create academic terms structure
INSERT INTO academic_terms (
    academic_year,
    term_type,
    term_number,
    start_date,
    end_date,
    registration_start,
    registration_end,
    is_current
) VALUES
('2024-2025', 'fall', 1, '2024-09-15', '2025-01-20', '2024-08-01', '2024-09-20', false),
('2024-2025', 'spring', 2, '2025-02-01', '2025-06-15', '2025-01-10', '2025-02-10', true),
('2025-2026', 'fall', 1, '2025-09-15', '2026-01-20', '2025-08-01', '2025-09-20', false);

-- Update course_offerings to link to terms
UPDATE course_offerings co
SET academic_term_id = (
    SELECT id FROM academic_terms 
    WHERE is_current = true 
    LIMIT 1
)
WHERE academic_term_id IS NULL;
```

### 2.3 HIGH: Grades Schema Issue

**Problem:**
- Grades table requires assessment_id (specific exam/assignment)
- Old system has course-level grades (midterm, final, overall)
- Can't migrate historical grades without assessments

**Solution A: Add enrollment_grades table** (RECOMMENDED)
```sql
-- New table for course-level grades
CREATE TABLE enrollment_grades (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id       uuid REFERENCES course_enrollments(id) ON DELETE CASCADE,
    grade_component     text NOT NULL, -- 'midterm', 'final', 'quiz_average', 'participation', 'total'
    marks_obtained      numeric(6,2),
    max_marks           numeric(6,2),
    percentage          numeric(5,2),
    weight_percentage   numeric(5,2),
    letter_grade        text,
    graded_by           uuid REFERENCES users(id),
    graded_at           timestamptz DEFAULT CURRENT_TIMESTAMP,
    is_final            boolean DEFAULT false,
    notes               text,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(enrollment_id, grade_component)
);

CREATE INDEX idx_enrollment_grades_enrollment ON enrollment_grades(enrollment_id);
CREATE INDEX idx_enrollment_grades_component ON enrollment_grades(grade_component);
```

**Solution B: Modify existing grades table** (Alternative)
```sql
-- Make assessment_id nullable and add enrollment_id
ALTER TABLE grades 
    ALTER COLUMN assessment_id DROP NOT NULL,
    ADD COLUMN enrollment_id uuid REFERENCES course_enrollments(id);

ALTER TABLE grades 
    DROP CONSTRAINT grades_assessment_student_unique,
    ADD CONSTRAINT grades_unique_check UNIQUE NULLS NOT DISTINCT (
        assessment_id, student_id, enrollment_id
    );
```

---

## 3. Missing Features Implementation

### 3.1 Transcript & GPA System

**Required Tables:**

```sql
-- Student transcripts (official records)
CREATE TABLE student_transcripts (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          uuid REFERENCES students(id) ON DELETE CASCADE,
    academic_term_id    uuid REFERENCES academic_terms(id),
    transcript_type     text CHECK (transcript_type IN ('official', 'unofficial', 'partial')),
    gpa_term            numeric(3,2),
    gpa_cumulative      numeric(3,2),
    total_credits_earned integer,
    total_credits_attempted integer,
    academic_standing   text CHECK (academic_standing IN ('good', 'probation', 'suspended', 'dismissed', 'graduated')),
    generated_date      timestamptz DEFAULT CURRENT_TIMESTAMP,
    generated_by        uuid REFERENCES users(id),
    file_url            text,
    is_official         boolean DEFAULT false,
    signature_data      jsonb, -- digital signature info
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Transcript requests
CREATE TABLE transcript_requests (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          uuid REFERENCES students(id),
    request_type        text CHECK (request_type IN ('official', 'unofficial', 'verification')),
    delivery_method     text CHECK (delivery_method IN ('email', 'mail', 'pickup', 'digital')),
    delivery_address    jsonb,
    purpose             text,
    copies_requested    integer DEFAULT 1,
    status              text DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
    requested_date      timestamptz DEFAULT CURRENT_TIMESTAMP,
    completed_date      timestamptz,
    fee_amount          numeric(10,2),
    payment_status      text,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- GPA calculation history
CREATE TABLE gpa_calculations (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          uuid REFERENCES students(id) ON DELETE CASCADE,
    academic_term_id    uuid REFERENCES academic_terms(id),
    term_gpa            numeric(3,2),
    cumulative_gpa      numeric(3,2),
    credits_earned_term integer,
    credits_earned_total integer,
    quality_points_term numeric(10,2),
    quality_points_total numeric(10,2),
    calculation_date    timestamptz DEFAULT CURRENT_TIMESTAMP,
    calculated_by       text DEFAULT 'system',
    notes               text,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, academic_term_id)
);

CREATE INDEX idx_transcripts_student ON student_transcripts(student_id);
CREATE INDEX idx_transcript_requests_student ON transcript_requests(student_id);
CREATE INDEX idx_transcript_requests_status ON transcript_requests(status);
CREATE INDEX idx_gpa_calculations_student ON gpa_calculations(student_id);
```

### 3.2 Financial & Payment System

**Required Tables:**

```sql
-- Tuition fee structure
CREATE TABLE tuition_fees (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_program_id uuid REFERENCES academic_programs(id),
    academic_term_id    uuid REFERENCES academic_terms(id),
    student_type        text CHECK (student_type IN ('domestic', 'international', 'exchange')),
    funding_type        text CHECK (funding_type IN ('state_funded', 'self_funded', 'contract')),
    base_fee            numeric(10,2) NOT NULL,
    per_credit_fee      numeric(10,2),
    lab_fee             numeric(10,2) DEFAULT 0,
    technology_fee      numeric(10,2) DEFAULT 0,
    library_fee         numeric(10,2) DEFAULT 0,
    other_fees          jsonb,
    currency            text DEFAULT 'AZN',
    effective_from      date NOT NULL,
    effective_until     date,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Student fee assignments
CREATE TABLE student_fees (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          uuid REFERENCES students(id) ON DELETE CASCADE,
    academic_term_id    uuid REFERENCES academic_terms(id),
    fee_type            text NOT NULL, -- 'tuition', 'housing', 'meal_plan', 'lab', 'library', 'late_fee', 'other'
    amount              numeric(10,2) NOT NULL,
    currency            text DEFAULT 'AZN',
    due_date            date NOT NULL,
    description         jsonb, -- multilingual
    status              text DEFAULT 'pending' CHECK (status IN ('pending', 'partial', 'paid', 'waived', 'cancelled')),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Payment transactions
CREATE TABLE payment_transactions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          uuid REFERENCES students(id),
    transaction_type    text CHECK (transaction_type IN ('payment', 'refund', 'adjustment', 'waiver')),
    amount              numeric(10,2) NOT NULL,
    currency            text DEFAULT 'AZN',
    payment_method      text CHECK (payment_method IN ('cash', 'card', 'bank_transfer', 'online', 'check')),
    payment_reference   text, -- external payment system reference
    transaction_date    timestamptz DEFAULT CURRENT_TIMESTAMP,
    academic_term_id    uuid REFERENCES academic_terms(id),
    description         text,
    processed_by        uuid REFERENCES users(id),
    receipt_url         text,
    status              text DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'reversed')),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Fee payment mapping
CREATE TABLE fee_payments (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_fee_id      uuid REFERENCES student_fees(id) ON DELETE CASCADE,
    payment_transaction_id uuid REFERENCES payment_transactions(id),
    amount_applied      numeric(10,2) NOT NULL,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_fee_id, payment_transaction_id)
);

-- Scholarships
CREATE TABLE scholarships (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                text UNIQUE NOT NULL,
    name                jsonb NOT NULL, -- multilingual
    description         jsonb,
    scholarship_type    text CHECK (scholarship_type IN ('academic', 'athletic', 'need_based', 'merit', 'diversity', 'research')),
    amount_type         text CHECK (amount_type IN ('full_tuition', 'partial_tuition', 'fixed_amount', 'percentage')),
    amount              numeric(10,2),
    percentage          numeric(5,2),
    max_recipients      integer,
    eligibility_criteria jsonb,
    renewable           boolean DEFAULT false,
    renewable_conditions jsonb,
    sponsor             text,
    is_active           boolean DEFAULT true,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Student scholarship awards
CREATE TABLE student_scholarships (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          uuid REFERENCES students(id) ON DELETE CASCADE,
    scholarship_id      uuid REFERENCES scholarships(id),
    academic_term_id    uuid REFERENCES academic_terms(id),
    award_amount        numeric(10,2) NOT NULL,
    award_date          date NOT NULL,
    status              text DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'terminated', 'completed')),
    start_term_id       uuid REFERENCES academic_terms(id),
    end_term_id         uuid REFERENCES academic_terms(id),
    conditions          jsonb, -- GPA requirements, etc.
    awarded_by          uuid REFERENCES users(id),
    notes               text,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tuition_fees_program ON tuition_fees(academic_program_id);
CREATE INDEX idx_student_fees_student ON student_fees(student_id);
CREATE INDEX idx_student_fees_term ON student_fees(academic_term_id);
CREATE INDEX idx_payment_transactions_student ON payment_transactions(student_id);
CREATE INDEX idx_student_scholarships_student ON student_scholarships(student_id);
```

### 3.3 Library & Resources Management

**Required Tables:**

```sql
-- Library catalog
CREATE TABLE library_resources (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type       text CHECK (resource_type IN ('book', 'journal', 'magazine', 'ebook', 'article', 'thesis', 'multimedia', 'database')),
    title               jsonb NOT NULL, -- multilingual
    subtitle            jsonb,
    authors             text[], -- array of author names
    isbn                text,
    issn                text,
    publisher           text,
    publication_year    integer,
    edition             text,
    language            text,
    pages               integer,
    subjects            text[], -- array of subject categories
    keywords            text[],
    abstract            jsonb, -- multilingual
    call_number         text UNIQUE,
    location            text, -- shelf location
    total_copies        integer DEFAULT 1,
    available_copies    integer DEFAULT 1,
    digital_url         text, -- for digital resources
    cover_image_url     text,
    is_reference_only   boolean DEFAULT false,
    is_available        boolean DEFAULT true,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Resource checkouts
CREATE TABLE library_checkouts (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id         uuid REFERENCES library_resources(id),
    user_id             uuid REFERENCES users(id),
    checkout_date       timestamptz DEFAULT CURRENT_TIMESTAMP,
    due_date            date NOT NULL,
    return_date         timestamptz,
    renewed_count       integer DEFAULT 0,
    status              text DEFAULT 'checked_out' CHECK (status IN ('checked_out', 'returned', 'overdue', 'lost', 'damaged')),
    checkout_type       text CHECK (checkout_type IN ('standard', 'reserve', 'reference', 'digital')),
    fine_amount         numeric(10,2) DEFAULT 0,
    notes               text,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Resource reservations
CREATE TABLE library_reservations (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id         uuid REFERENCES library_resources(id),
    user_id             uuid REFERENCES users(id),
    reservation_date    timestamptz DEFAULT CURRENT_TIMESTAMP,
    expiry_date         timestamptz NOT NULL,
    status              text DEFAULT 'active' CHECK (status IN ('active', 'fulfilled', 'expired', 'cancelled')),
    position_in_queue   integer,
    notified_date       timestamptz,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Course reading lists
CREATE TABLE course_reading_lists (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_offering_id  uuid REFERENCES course_offerings(id) ON DELETE CASCADE,
    resource_id         uuid REFERENCES library_resources(id),
    reading_type        text CHECK (reading_type IN ('required', 'recommended', 'supplementary')),
    chapter_pages       text, -- e.g., "Ch 1-3, pp. 15-45"
    sequence_order      integer,
    notes               jsonb, -- multilingual notes
    added_by            uuid REFERENCES users(id),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_library_resources_type ON library_resources(resource_type);
CREATE INDEX idx_library_resources_title ON library_resources USING gin(title);
CREATE INDEX idx_library_checkouts_user ON library_checkouts(user_id);
CREATE INDEX idx_library_checkouts_resource ON library_checkouts(resource_id);
CREATE INDEX idx_library_checkouts_status ON library_checkouts(status);
CREATE INDEX idx_library_reservations_user ON library_reservations(user_id);
CREATE INDEX idx_course_reading_lists_course ON course_reading_lists(course_offering_id);
```

### 3.4 Messaging & Communication System

**Required Tables:**

```sql
-- Message threads
CREATE TABLE message_threads (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject             text NOT NULL,
    category            text CHECK (category IN ('academic', 'administrative', 'personal', 'group', 'announcement')),
    is_group_thread     boolean DEFAULT false,
    course_offering_id  uuid REFERENCES course_offerings(id), -- if course-related
    created_by          uuid REFERENCES users(id),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    last_message_at     timestamptz DEFAULT CURRENT_TIMESTAMP,
    is_locked           boolean DEFAULT false,
    locked_by           uuid REFERENCES users(id),
    locked_at           timestamptz
);

-- Messages
CREATE TABLE messages (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id           uuid REFERENCES message_threads(id) ON DELETE CASCADE,
    parent_message_id   uuid REFERENCES messages(id), -- for replies
    sender_id           uuid REFERENCES users(id),
    content             text NOT NULL,
    content_html        text, -- rich text version
    attachments         jsonb, -- array of file references
    is_system_message   boolean DEFAULT false,
    is_draft            boolean DEFAULT false,
    priority            text DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    sent_at             timestamptz DEFAULT CURRENT_TIMESTAMP,
    edited_at           timestamptz,
    deleted_at          timestamptz,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Message recipients
CREATE TABLE message_recipients (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id          uuid REFERENCES messages(id) ON DELETE CASCADE,
    thread_id           uuid REFERENCES message_threads(id) ON DELETE CASCADE,
    recipient_id        uuid REFERENCES users(id),
    recipient_type      text DEFAULT 'to' CHECK (recipient_type IN ('to', 'cc', 'bcc')),
    read_at             timestamptz,
    deleted_at          timestamptz,
    starred             boolean DEFAULT false,
    archived            boolean DEFAULT false,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id, recipient_id)
);

-- Discussion forums
CREATE TABLE discussion_forums (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_offering_id  uuid REFERENCES course_offerings(id) ON DELETE CASCADE,
    title               jsonb NOT NULL, -- multilingual
    description         jsonb,
    forum_type          text CHECK (forum_type IN ('general', 'q_and_a', 'announcement', 'group_work')),
    is_moderated        boolean DEFAULT false,
    moderator_ids       uuid[], -- array of user ids
    allow_anonymous     boolean DEFAULT false,
    is_locked           boolean DEFAULT false,
    display_order       integer,
    created_by          uuid REFERENCES users(id),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Forum posts
CREATE TABLE forum_posts (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    forum_id            uuid REFERENCES discussion_forums(id) ON DELETE CASCADE,
    parent_post_id      uuid REFERENCES forum_posts(id), -- for threaded discussions
    author_id           uuid REFERENCES users(id),
    title               text,
    content             text NOT NULL,
    content_html        text,
    attachments         jsonb,
    is_pinned           boolean DEFAULT false,
    is_answer           boolean DEFAULT false, -- for Q&A forums
    is_anonymous        boolean DEFAULT false,
    view_count          integer DEFAULT 0,
    like_count          integer DEFAULT 0,
    posted_at           timestamptz DEFAULT CURRENT_TIMESTAMP,
    edited_at           timestamptz,
    deleted_at          timestamptz,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Post reactions/likes
CREATE TABLE forum_post_reactions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id             uuid REFERENCES forum_posts(id) ON DELETE CASCADE,
    user_id             uuid REFERENCES users(id),
    reaction_type       text CHECK (reaction_type IN ('like', 'helpful', 'insightful', 'thanks')),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, user_id, reaction_type)
);

CREATE INDEX idx_message_threads_course ON message_threads(course_offering_id);
CREATE INDEX idx_message_threads_created_by ON message_threads(created_by);
CREATE INDEX idx_messages_thread ON messages(thread_id);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_message_recipients_recipient ON message_recipients(recipient_id);
CREATE INDEX idx_message_recipients_thread ON message_recipients(thread_id);
CREATE INDEX idx_discussion_forums_course ON discussion_forums(course_offering_id);
CREATE INDEX idx_forum_posts_forum ON forum_posts(forum_id);
CREATE INDEX idx_forum_posts_author ON forum_posts(author_id);
```

### 3.5 Advanced Assessment Features

**Required Tables:**

```sql
-- Question banks
CREATE TABLE question_banks (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id           uuid REFERENCES courses(id),
    organization_unit_id uuid REFERENCES organization_units(id),
    name                jsonb NOT NULL, -- multilingual
    description         jsonb,
    subject_area        text,
    difficulty_level    text CHECK (difficulty_level IN ('easy', 'medium', 'hard', 'expert')),
    created_by          uuid REFERENCES users(id),
    is_shared           boolean DEFAULT false,
    shared_with_units   uuid[], -- array of organization_unit ids
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Questions
CREATE TABLE questions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_bank_id    uuid REFERENCES question_banks(id) ON DELETE CASCADE,
    question_type       text CHECK (question_type IN ('multiple_choice', 'true_false', 'short_answer', 'essay', 'matching', 'fill_blank', 'coding')),
    question_text       jsonb NOT NULL, -- multilingual
    question_html       jsonb, -- rich text version
    points              numeric(6,2) DEFAULT 1,
    difficulty_level    text CHECK (difficulty_level IN ('easy', 'medium', 'hard', 'expert')),
    bloom_taxonomy_level text CHECK (bloom_taxonomy_level IN ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create')),
    learning_outcome    text,
    correct_answer      jsonb, -- structure depends on question_type
    answer_options      jsonb, -- for multiple choice, matching, etc.
    answer_explanation  jsonb, -- multilingual explanation
    tags                text[],
    usage_count         integer DEFAULT 0,
    avg_score           numeric(5,2),
    created_by          uuid REFERENCES users(id),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Assessment question mapping (for building exams from question banks)
CREATE TABLE assessment_questions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id       uuid REFERENCES assessments(id) ON DELETE CASCADE,
    question_id         uuid REFERENCES questions(id),
    points              numeric(6,2) NOT NULL,
    sequence_order      integer NOT NULL,
    is_required         boolean DEFAULT true,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(assessment_id, sequence_order)
);

-- Student answers
CREATE TABLE question_responses (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id       uuid REFERENCES assessment_submissions(id) ON DELETE CASCADE,
    question_id         uuid REFERENCES questions(id),
    student_answer      jsonb, -- structure depends on question_type
    is_correct          boolean,
    points_earned       numeric(6,2),
    auto_graded         boolean DEFAULT false,
    grader_feedback     text,
    time_spent_seconds  integer,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Rubrics (detailed grading criteria)
CREATE TABLE rubric_templates (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name                jsonb NOT NULL, -- multilingual
    description         jsonb,
    course_id           uuid REFERENCES courses(id),
    rubric_type         text CHECK (rubric_type IN ('holistic', 'analytic', 'checklist')),
    total_points        numeric(6,2),
    created_by          uuid REFERENCES users(id),
    is_shared           boolean DEFAULT false,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Rubric criteria
CREATE TABLE rubric_criteria (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    rubric_id           uuid REFERENCES rubric_templates(id) ON DELETE CASCADE,
    criterion_name      jsonb NOT NULL, -- multilingual
    description         jsonb,
    max_points          numeric(6,2) NOT NULL,
    sequence_order      integer NOT NULL,
    weight_percentage   numeric(5,2),
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Rubric performance levels
CREATE TABLE rubric_levels (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    criterion_id        uuid REFERENCES rubric_criteria(id) ON DELETE CASCADE,
    level_name          jsonb NOT NULL, -- multilingual (e.g., "Excellent", "Good", "Fair", "Poor")
    description         jsonb, -- what qualifies for this level
    points              numeric(6,2) NOT NULL,
    sequence_order      integer NOT NULL,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Peer review assignments
CREATE TABLE peer_reviews (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id       uuid REFERENCES assessments(id) ON DELETE CASCADE,
    submission_id       uuid REFERENCES assessment_submissions(id),
    reviewer_id         uuid REFERENCES students(id),
    rubric_id           uuid REFERENCES rubric_templates(id),
    review_score        numeric(6,2),
    review_feedback     text,
    rubric_scores       jsonb, -- scores for each criterion
    status              text DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'skipped')),
    submitted_at        timestamptz,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_question_banks_course ON question_banks(course_id);
CREATE INDEX idx_questions_bank ON questions(question_bank_id);
CREATE INDEX idx_questions_type ON questions(question_type);
CREATE INDEX idx_assessment_questions_assessment ON assessment_questions(assessment_id);
CREATE INDEX idx_question_responses_submission ON question_responses(submission_id);
CREATE INDEX idx_rubric_criteria_rubric ON rubric_criteria(rubric_id);
CREATE INDEX idx_peer_reviews_assessment ON peer_reviews(assessment_id);
```

### 3.6 Degree Audit & Prerequisites

**Required Tables:**

```sql
-- Degree requirements
CREATE TABLE degree_requirements (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_program_id uuid REFERENCES academic_programs(id) ON DELETE CASCADE,
    requirement_type    text CHECK (requirement_type IN ('core', 'major', 'minor', 'elective', 'general_education', 'capstone')),
    requirement_name    jsonb NOT NULL, -- multilingual
    description         jsonb,
    required_credits    integer NOT NULL,
    minimum_gpa         numeric(3,2),
    course_list         uuid[], -- array of required course ids
    course_category     text, -- if any course from a category satisfies
    sequence_order      integer,
    is_mandatory        boolean DEFAULT true,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Student degree progress
CREATE TABLE degree_audit_progress (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          uuid REFERENCES students(id) ON DELETE CASCADE,
    requirement_id      uuid REFERENCES degree_requirements(id),
    credits_completed   integer DEFAULT 0,
    credits_required    integer NOT NULL,
    status              text DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'waived')),
    completed_courses   uuid[], -- array of completed course_enrollment ids
    gpa                 numeric(3,2),
    last_updated        timestamptz DEFAULT CURRENT_TIMESTAMP,
    notes               text,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, requirement_id)
);

-- Course prerequisite validations
CREATE TABLE prerequisite_checks (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          uuid REFERENCES students(id),
    course_id           uuid REFERENCES courses(id),
    enrollment_id       uuid REFERENCES course_enrollments(id),
    prerequisite_met    boolean DEFAULT false,
    missing_prerequisites uuid[], -- array of course ids not completed
    override_by         uuid REFERENCES users(id),
    override_reason     text,
    override_date       timestamptz,
    checked_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Course waitlists
CREATE TABLE course_waitlists (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_offering_id  uuid REFERENCES course_offerings(id) ON DELETE CASCADE,
    student_id          uuid REFERENCES students(id),
    position            integer NOT NULL,
    added_date          timestamptz DEFAULT CURRENT_TIMESTAMP,
    notified_date       timestamptz,
    status              text DEFAULT 'active' CHECK (status IN ('active', 'enrolled', 'removed', 'expired')),
    expiry_date         timestamptz,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_offering_id, student_id)
);

CREATE INDEX idx_degree_requirements_program ON degree_requirements(academic_program_id);
CREATE INDEX idx_degree_audit_student ON degree_audit_progress(student_id);
CREATE INDEX idx_prerequisite_checks_student ON prerequisite_checks(student_id);
CREATE INDEX idx_course_waitlists_offering ON course_waitlists(course_offering_id);
CREATE INDEX idx_course_waitlists_position ON course_waitlists(position);
```

---

## 4. Database Functions & Procedures

### 4.1 GPA Calculation Function

```sql
-- Function to calculate GPA
CREATE OR REPLACE FUNCTION calculate_student_gpa(
    p_student_id uuid,
    p_academic_term_id uuid DEFAULT NULL
)
RETURNS TABLE (
    term_gpa numeric(3,2),
    cumulative_gpa numeric(3,2),
    credits_earned integer,
    quality_points numeric(10,2)
) AS $$
DECLARE
    v_grade_points numeric(10,2);
    v_credits integer;
BEGIN
    -- Calculate term GPA if term specified
    IF p_academic_term_id IS NOT NULL THEN
        SELECT 
            ROUND(SUM(ce.grade_points * c.credit_hours) / NULLIF(SUM(c.credit_hours), 0), 2),
            SUM(c.credit_hours)
        INTO term_gpa, v_credits
        FROM course_enrollments ce
        JOIN course_offerings co ON ce.course_offering_id = co.id
        JOIN courses c ON co.course_id = c.id
        WHERE ce.student_id = p_student_id
        AND co.academic_term_id = p_academic_term_id
        AND ce.enrollment_status = 'completed'
        AND ce.grade_points IS NOT NULL;
    END IF;
    
    -- Calculate cumulative GPA
    SELECT 
        ROUND(SUM(ce.grade_points * c.credit_hours) / NULLIF(SUM(c.credit_hours), 0), 2),
        SUM(c.credit_hours),
        SUM(ce.grade_points * c.credit_hours)
    INTO cumulative_gpa, credits_earned, quality_points
    FROM course_enrollments ce
    JOIN course_offerings co ON ce.course_offering_id = co.id
    JOIN courses c ON co.course_id = c.id
    WHERE ce.student_id = p_student_id
    AND ce.enrollment_status = 'completed'
    AND ce.grade_points IS NOT NULL;
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;
```

### 4.2 Prerequisite Validation Function

```sql
-- Function to check if student has met prerequisites
CREATE OR REPLACE FUNCTION check_prerequisites(
    p_student_id uuid,
    p_course_id uuid
)
RETURNS TABLE (
    prerequisites_met boolean,
    missing_courses uuid[]
) AS $$
DECLARE
    v_prerequisites uuid[];
    v_completed uuid[];
    v_missing uuid[];
BEGIN
    -- Get course prerequisites
    SELECT prerequisites INTO v_prerequisites
    FROM courses
    WHERE id = p_course_id;
    
    -- If no prerequisites, return true
    IF v_prerequisites IS NULL OR array_length(v_prerequisites, 1) = 0 THEN
        prerequisites_met := true;
        missing_courses := ARRAY[]::uuid[];
        RETURN NEXT;
        RETURN;
    END IF;
    
    -- Get completed courses
    SELECT array_agg(DISTINCT co.course_id)
    INTO v_completed
    FROM course_enrollments ce
    JOIN course_offerings co ON ce.course_offering_id = co.id
    WHERE ce.student_id = p_student_id
    AND ce.enrollment_status = 'completed'
    AND ce.grade_points >= 2.0; -- minimum passing grade
    
    -- Find missing prerequisites
    SELECT array_agg(prereq)
    INTO v_missing
    FROM unnest(v_prerequisites) AS prereq
    WHERE prereq != ALL(COALESCE(v_completed, ARRAY[]::uuid[]));
    
    prerequisites_met := (v_missing IS NULL OR array_length(v_missing, 1) = 0);
    missing_courses := COALESCE(v_missing, ARRAY[]::uuid[]);
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;
```

### 4.3 Schedule Conflict Detection

```sql
-- Function to detect schedule conflicts
CREATE OR REPLACE FUNCTION check_schedule_conflicts(
    p_student_id uuid,
    p_course_offering_id uuid
)
RETURNS TABLE (
    has_conflict boolean,
    conflicting_courses jsonb
) AS $$
DECLARE
    v_conflicts jsonb;
BEGIN
    SELECT jsonb_agg(
        jsonb_build_object(
            'course_offering_id', cs2.course_offering_id,
            'course_code', c.code,
            'course_name', c.name,
            'day', cs2.day_of_week,
            'time', cs2.start_time || ' - ' || cs2.end_time
        )
    )
    INTO v_conflicts
    FROM course_enrollments ce
    JOIN class_schedules cs2 ON cs2.course_offering_id = ce.course_offering_id
    JOIN course_offerings co2 ON ce.course_offering_id = co2.id
    JOIN courses c ON co2.course_id = c.id
    WHERE ce.student_id = p_student_id
    AND ce.enrollment_status = 'enrolled'
    AND EXISTS (
        SELECT 1
        FROM class_schedules cs1
        WHERE cs1.course_offering_id = p_course_offering_id
        AND cs1.day_of_week = cs2.day_of_week
        AND (
            (cs1.start_time >= cs2.start_time AND cs1.start_time < cs2.end_time)
            OR (cs1.end_time > cs2.start_time AND cs1.end_time <= cs2.end_time)
            OR (cs1.start_time <= cs2.start_time AND cs1.end_time >= cs2.end_time)
        )
    );
    
    has_conflict := (v_conflicts IS NOT NULL AND jsonb_array_length(v_conflicts) > 0);
    conflicting_courses := COALESCE(v_conflicts, '[]'::jsonb);
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;
```

---

## 5. Implementation Priority & Timeline

### Phase 1: CRITICAL (Week 1-2)
**Must have for basic operations**

1. ✅ **Fix Academic Programs** (Day 1-2)
   - Populate academic_programs table
   - Link students to programs
   - Test: 2 hours

2. ✅ **Fix Academic Terms** (Day 3-4)
   - Create current and upcoming terms
   - Link course offerings to terms
   - Test: 2 hours

3. ✅ **Add Enrollment Grades Table** (Day 5-7)
   - Create enrollment_grades table
   - Migrate historical grades from old DB
   - Update GPA calculation logic
   - Test: 4 hours

4. ✅ **Populate Empty Core Tables** (Week 2)
   - Add languages (az, en, ru)
   - Add roles and permissions
   - Add system settings
   - Test: 4 hours

**Deliverable:** Working LMS with proper academic structure

### Phase 2: HIGH PRIORITY (Week 3-4)
**Essential for student operations**

5. ✅ **Transcript System** (Week 3)
   - Create transcript tables
   - Implement GPA calculation function
   - Build transcript generation
   - Test: 8 hours

6. ✅ **Prerequisites & Degree Audit** (Week 4)
   - Create degree requirements tables
   - Implement prerequisite checking
   - Build degree progress tracking
   - Test: 8 hours

**Deliverable:** Academic records and validation working

### Phase 3: MEDIUM PRIORITY (Week 5-8)
**Important for full LMS functionality**

7. ✅ **Financial System** (Week 5-6)
   - Create fee and payment tables
   - Implement scholarship system
   - Build payment processing
   - Test: 12 hours

8. ✅ **Library System** (Week 7)
   - Create library catalog
   - Implement checkout system
   - Build course reading lists
   - Test: 8 hours

9. ✅ **Messaging System** (Week 8)
   - Create messaging tables
   - Implement discussion forums
   - Build notification system
   - Test: 8 hours

**Deliverable:** Complete student services platform

### Phase 4: ENHANCEMENTS (Week 9-12)
**Advanced features**

10. ✅ **Advanced Assessments** (Week 9-10)
    - Create question banks
    - Implement rubrics
    - Build peer review
    - Test: 12 hours

11. ✅ **Analytics & Reporting** (Week 11-12)
    - Create reporting tables
    - Build custom reports
    - Implement dashboards
    - Test: 8 hours

**Deliverable:** Full-featured modern LMS

### Phase 5: OPTIMIZATION (Week 13-14)
**Performance and security**

12. ✅ **Row-Level Security** (Week 13)
    - Implement RLS policies
    - Test access control
    - Document permissions
    - Test: 8 hours

13. ✅ **Performance Optimization** (Week 14)
    - Add missing indexes
    - Create materialized views
    - Optimize queries
    - Test: 8 hours

14. ✅ **Documentation** (Week 14)
    - Generate ERD diagrams
    - Write API documentation
    - Create admin guide
    - Test: 4 hours

**Deliverable:** Production-ready optimized LMS

---

## 6. SQL Migration Scripts

### 6.1 Critical Fixes (Execute First)

```sql
-- ==============================================
-- CRITICAL FIX 1: Populate Academic Programs
-- ==============================================

-- Insert academic programs (customize based on your institution)
INSERT INTO academic_programs (
    organization_unit_id,
    code,
    name,
    degree_type,
    duration_years,
    total_credits,
    language_of_instruction,
    is_active
) VALUES
(
    (SELECT id FROM organization_units WHERE code = 'CS' LIMIT 1),
    'CS-BS',
    '{"az": "Kompüter Elmləri", "en": "Computer Science", "ru": "Компьютерные науки"}'::jsonb,
    'bachelor',
    4,
    240,
    ARRAY['az', 'en'],
    true
),
(
    (SELECT id FROM organization_units WHERE code = 'ECON' LIMIT 1),
    'ECON-BS',
    '{"az": "İqtisadiyyat", "en": "Economics", "ru": "Экономика"}'::jsonb,
    'bachelor',
    4,
    240,
    ARRAY['az', 'en', 'ru'],
    true
);

-- Update students with academic_program_id
-- (This requires knowing which program each student belongs to)
UPDATE students s
SET academic_program_id = ap.id
FROM academic_programs ap
WHERE s.metadata->>'program_code' = ap.code;

-- ==============================================
-- CRITICAL FIX 2: Create Academic Terms
-- ==============================================

INSERT INTO academic_terms (
    academic_year,
    term_type,
    term_number,
    start_date,
    end_date,
    registration_start,
    registration_end,
    add_drop_deadline,
    withdrawal_deadline,
    grade_submission_deadline,
    is_current
) VALUES
('2024-2025', 'fall', 1, '2024-09-15', '2025-01-20', '2024-08-01', '2024-09-20', '2024-09-30', '2024-11-30', '2025-01-25', false),
('2024-2025', 'spring', 2, '2025-02-01', '2025-06-15', '2025-01-10', '2025-02-10', '2025-02-20', '2025-04-30', '2025-06-20', true),
('2025-2026', 'fall', 1, '2025-09-15', '2026-01-20', '2025-08-01', '2025-09-20', '2025-09-30', '2025-11-30', '2026-01-25', false);

-- Link course offerings to current term
UPDATE course_offerings
SET academic_term_id = (SELECT id FROM academic_terms WHERE is_current = true LIMIT 1)
WHERE academic_term_id IS NULL;

-- ==============================================
-- CRITICAL FIX 3: Add Enrollment Grades Table
-- ==============================================

CREATE TABLE enrollment_grades (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id       uuid REFERENCES course_enrollments(id) ON DELETE CASCADE,
    grade_component     text NOT NULL, -- 'midterm', 'final', 'quiz', 'assignment', 'participation', 'total'
    marks_obtained      numeric(6,2),
    max_marks           numeric(6,2),
    percentage          numeric(5,2),
    weight_percentage   numeric(5,2),
    letter_grade        text,
    grade_points        numeric(3,2),
    graded_by           uuid REFERENCES users(id),
    graded_at           timestamptz DEFAULT CURRENT_TIMESTAMP,
    is_final            boolean DEFAULT false,
    notes               text,
    created_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamptz DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT enrollment_grades_percentage_valid CHECK (percentage IS NULL OR percentage >= 0 AND percentage <= 100),
    CONSTRAINT enrollment_grades_grade_points_valid CHECK (grade_points IS NULL OR grade_points >= 0 AND grade_points <= 4),
    UNIQUE(enrollment_id, grade_component)
);

CREATE INDEX idx_enrollment_grades_enrollment ON enrollment_grades(enrollment_id);
CREATE INDEX idx_enrollment_grades_component ON enrollment_grades(grade_component);
CREATE INDEX idx_enrollment_grades_graded_by ON enrollment_grades(graded_by);

-- Add trigger for updated_at
CREATE TRIGGER trigger_update_enrollment_grades_updated_at
    BEFORE UPDATE ON enrollment_grades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==============================================
-- CRITICAL FIX 4: Populate Base Languages
-- ==============================================

INSERT INTO languages (code, name, native_name, direction, is_active, is_default) VALUES
('az', 'Azerbaijani', 'Azərbaycan dili', 'ltr', true, true),
('en', 'English', 'English', 'ltr', true, false),
('ru', 'Russian', 'Русский', 'ltr', true, false);

-- ==============================================
-- CRITICAL FIX 5: Create Base Roles
-- ==============================================

INSERT INTO roles (code, name, description, level, is_system) VALUES
('STUDENT', '{"az": "Tələbə", "en": "Student", "ru": "Студент"}'::jsonb, 
    '{"az": "Tələbə rolu", "en": "Student role", "ru": "Роль студента"}'::jsonb, 10, true),
('TEACHER', '{"az": "Müəllim", "en": "Teacher", "ru": "Преподаватель"}'::jsonb,
    '{"az": "Müəllim rolu", "en": "Teacher role", "ru": "Роль преподавателя"}'::jsonb, 5, true),
('ADMIN', '{"az": "Administrator", "en": "Administrator", "ru": "Администратор"}'::jsonb,
    '{"az": "Administrator rolu", "en": "Administrator role", "ru": "Роль администратора"}'::jsonb, 1, true),
('DEAN', '{"az": "Dekan", "en": "Dean", "ru": "Декан"}'::jsonb,
    '{"az": "Dekan rolu", "en": "Dean role", "ru": "Роль декана"}'::jsonb, 2, true),
('HEAD_OF_DEPT', '{"az": "Kafedra müdiri", "en": "Head of Department", "ru": "Заведующий кафедрой"}'::jsonb,
    '{"az": "Kafedra müdiri rolu", "en": "Head of Department role", "ru": "Роль заведующего кафедрой"}'::jsonb, 3, true);
```

### 6.2 Complete Schema Creation Script

Save this as `/backend/migration/schema_improvements.sql`:

```sql
-- ==============================================
-- LMS DATABASE SCHEMA IMPROVEMENTS
-- Execute after critical fixes
-- ==============================================

BEGIN;

-- ... (All the table creation statements from sections 3.1 through 3.6)

COMMIT;
```

---

## 7. Testing & Validation Plan

### 7.1 Schema Validation Tests

```sql
-- Test 1: Check all students have academic programs
SELECT 
    COUNT(*) as students_without_program
FROM students 
WHERE academic_program_id IS NULL;
-- Expected: 0

-- Test 2: Check all course offerings have academic terms
SELECT 
    COUNT(*) as offerings_without_term
FROM course_offerings
WHERE academic_term_id IS NULL;
-- Expected: 0

-- Test 3: Verify foreign key constraints
SELECT 
    COUNT(*) as broken_fk_constraints
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
AND constraint_schema = 'public'
AND NOT EXISTS (
    SELECT 1 FROM information_schema.referential_constraints rc
    WHERE rc.constraint_name = table_constraints.constraint_name
);
-- Expected: 0

-- Test 4: Check for orphaned records
SELECT 
    'course_enrollments' as table_name,
    COUNT(*) as orphaned_records
FROM course_enrollments ce
WHERE NOT EXISTS (SELECT 1 FROM students WHERE id = ce.student_id)
   OR NOT EXISTS (SELECT 1 FROM course_offerings WHERE id = ce.course_offering_id)
UNION ALL
SELECT 
    'grades',
    COUNT(*)
FROM grades g
WHERE NOT EXISTS (SELECT 1 FROM students WHERE id = g.student_id);
-- Expected: 0 for all
```

### 7.2 Performance Tests

```sql
-- Test query performance (should be < 100ms)
EXPLAIN ANALYZE
SELECT 
    s.student_number,
    p.first_name,
    p.last_name,
    c.code,
    c.name->>'en' as course_name,
    ce.grade,
    ce.grade_points
FROM course_enrollments ce
JOIN students s ON ce.student_id = s.id
JOIN persons p ON s.user_id = p.user_id
JOIN course_offerings co ON ce.course_offering_id = co.id
JOIN courses c ON co.course_id = c.id
WHERE s.student_number = 'STU001'
ORDER BY co.academic_term_id DESC;
```

---

## 8. Documentation Requirements

### 8.1 ERD Diagram Generation

```bash
# Install postgresql-autodoc
sudo apt-get install postgresql-autodoc

# Generate ERD
postgresql_autodoc -d lms -u postgres -h localhost --password=1111 -t dot

# Convert to PDF
dot -Tpdf lms.dot -o LMS_Database_ERD.pdf
```

### 8.2 Data Dictionary

Create comprehensive table documentation:

```sql
-- Generate data dictionary
SELECT 
    t.table_name,
    c.column_name,
    c.data_type,
    c.character_maximum_length,
    c.is_nullable,
    c.column_default,
    pgd.description
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
LEFT JOIN pg_catalog.pg_statio_all_tables st ON st.relname = t.table_name
LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid = st.relid
WHERE t.table_schema = 'public'
AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name, c.ordinal_position;
```

---

## 9. Next Steps & Recommendations

### Immediate Actions (This Week)
1. ✅ Review and approve this improvement plan
2. ✅ Execute critical fixes (Section 6.1)
3. ✅ Test all existing functionality still works
4. ✅ Backup database before major changes

### Short-term (Next 2 Weeks)
5. ✅ Implement Phase 1 improvements (academic structure)
6. ✅ Implement Phase 2 improvements (transcripts, prerequisites)
7. ✅ Test with real user scenarios
8. ✅ Document API changes for frontend team

### Medium-term (Next Month)
9. ✅ Implement Phase 3 improvements (financial, library, messaging)
10. ✅ Performance testing and optimization
11. ✅ Security audit and RLS implementation
12. ✅ User acceptance testing

### Long-term (Next Quarter)
13. ✅ Complete Phase 4 and 5 enhancements
14. ✅ Full system documentation
15. ✅ Training materials for administrators
16. ✅ Production deployment plan

---

## 10. Conclusion

The current LMS database has a **solid foundation** but requires **significant enhancements** to be a complete system. The most critical issues are:

1. **Academic programs disconnection** - MUST fix immediately
2. **Missing GPA/transcript system** - Essential for student records
3. **No financial system** - Required for tuition management
4. **Limited assessment features** - Need question banks and rubrics

Following this implementation plan will result in a **world-class LMS database** that supports:
- ✅ Complete academic lifecycle management
- ✅ Financial and payment processing
- ✅ Advanced assessment and grading
- ✅ Library and resource management
- ✅ Comprehensive communication tools
- ✅ Robust reporting and analytics

**Estimated Total Effort:** 14 weeks (280-320 hours)

**Priority:** Execute Critical Fixes first (Week 1), then proceed with phased implementation.

---

**Document Version:** 1.0  
**Last Updated:** October 8, 2025  
**Prepared By:** Senior Full-Stack Developer  
**Status:** Ready for Implementation
