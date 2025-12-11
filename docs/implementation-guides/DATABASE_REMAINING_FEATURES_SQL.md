# Remaining Database Features - Complete SQL
**All SQL ready to copy and execute**

---

## Financial System (Priority: HIGH)

```sql
-- ==============================================
-- FINANCIAL & PAYMENT SYSTEM
-- ==============================================

BEGIN;

-- Tuition fee structure
CREATE TABLE tuition_fees (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_program_id uuid REFERENCES academic_programs(id),
    academic_term_id uuid REFERENCES academic_terms(id),
    student_type text CHECK (student_type IN ('domestic', 'international', 'exchange')),
    funding_type text CHECK (funding_type IN ('state_funded', 'self_funded', 'contract')),
    base_fee numeric(10,2) NOT NULL,
    per_credit_fee numeric(10,2),
    currency text DEFAULT 'AZN',
    effective_from date NOT NULL,
    effective_until date,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Student fee assignments
CREATE TABLE student_fees (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid REFERENCES students(id) ON DELETE CASCADE,
    academic_term_id uuid REFERENCES academic_terms(id),
    fee_type text NOT NULL,
    amount numeric(10,2) NOT NULL,
    due_date date NOT NULL,
    status text DEFAULT 'pending',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Payment transactions
CREATE TABLE payment_transactions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid REFERENCES students(id),
    amount numeric(10,2) NOT NULL,
    payment_method text,
    transaction_date timestamptz DEFAULT CURRENT_TIMESTAMP,
    status text DEFAULT 'completed',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Scholarships
CREATE TABLE scholarships (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text UNIQUE NOT NULL,
    name jsonb NOT NULL,
    scholarship_type text,
    amount numeric(10,2),
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Student scholarship awards
CREATE TABLE student_scholarships (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid REFERENCES students(id) ON DELETE CASCADE,
    scholarship_id uuid REFERENCES scholarships(id),
    academic_term_id uuid REFERENCES academic_terms(id),
    award_amount numeric(10,2) NOT NULL,
    status text DEFAULT 'active',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tuition_fees_program ON tuition_fees(academic_program_id);
CREATE INDEX idx_student_fees_student ON student_fees(student_id);
CREATE INDEX idx_payment_transactions_student ON payment_transactions(student_id);
CREATE INDEX idx_student_scholarships_student ON student_scholarships(student_id);

COMMIT;
```

---

## Library System (Priority: HIGH)

```sql
-- ==============================================
-- LIBRARY & RESOURCES SYSTEM
-- ==============================================

BEGIN;

-- Library catalog
CREATE TABLE library_resources (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type text,
    title jsonb NOT NULL,
    authors text[],
    isbn text,
    publisher text,
    publication_year integer,
    call_number text UNIQUE,
    total_copies integer DEFAULT 1,
    available_copies integer DEFAULT 1,
    is_available boolean DEFAULT true,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Resource checkouts
CREATE TABLE library_checkouts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id uuid REFERENCES library_resources(id),
    user_id uuid REFERENCES users(id),
    checkout_date timestamptz DEFAULT CURRENT_TIMESTAMP,
    due_date date NOT NULL,
    return_date timestamptz,
    status text DEFAULT 'checked_out',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Resource reservations
CREATE TABLE library_reservations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id uuid REFERENCES library_resources(id),
    user_id uuid REFERENCES users(id),
    reservation_date timestamptz DEFAULT CURRENT_TIMESTAMP,
    status text DEFAULT 'active',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Course reading lists
CREATE TABLE course_reading_lists (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_offering_id uuid REFERENCES course_offerings(id) ON DELETE CASCADE,
    resource_id uuid REFERENCES library_resources(id),
    reading_type text,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_library_checkouts_user ON library_checkouts(user_id);
CREATE INDEX idx_library_checkouts_resource ON library_checkouts(resource_id);
CREATE INDEX idx_course_reading_lists_course ON course_reading_lists(course_offering_id);

COMMIT;
```

---

## Messaging System (Priority: MEDIUM)

```sql
-- ==============================================
-- MESSAGING & COMMUNICATION SYSTEM
-- ==============================================

BEGIN;

-- Message threads
CREATE TABLE message_threads (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject text NOT NULL,
    category text,
    is_group_thread boolean DEFAULT false,
    created_by uuid REFERENCES users(id),
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Messages
CREATE TABLE messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id uuid REFERENCES message_threads(id) ON DELETE CASCADE,
    sender_id uuid REFERENCES users(id),
    content text NOT NULL,
    sent_at timestamptz DEFAULT CURRENT_TIMESTAMP,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Message recipients
CREATE TABLE message_recipients (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id uuid REFERENCES messages(id) ON DELETE CASCADE,
    recipient_id uuid REFERENCES users(id),
    read_at timestamptz,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Discussion forums
CREATE TABLE discussion_forums (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_offering_id uuid REFERENCES course_offerings(id) ON DELETE CASCADE,
    title jsonb NOT NULL,
    forum_type text,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Forum posts
CREATE TABLE forum_posts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    forum_id uuid REFERENCES discussion_forums(id) ON DELETE CASCADE,
    author_id uuid REFERENCES users(id),
    content text NOT NULL,
    posted_at timestamptz DEFAULT CURRENT_TIMESTAMP,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_thread ON messages(thread_id);
CREATE INDEX idx_message_recipients_recipient ON message_recipients(recipient_id);
CREATE INDEX idx_forum_posts_forum ON forum_posts(forum_id);

COMMIT;
```

---

## Question Banks (Priority: MEDIUM)

```sql
-- ==============================================
-- QUESTION BANKS & ADVANCED ASSESSMENT
-- ==============================================

BEGIN;

-- Question banks
CREATE TABLE question_banks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id uuid REFERENCES courses(id),
    name jsonb NOT NULL,
    created_by uuid REFERENCES users(id),
    is_shared boolean DEFAULT false,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Questions
CREATE TABLE questions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_bank_id uuid REFERENCES question_banks(id) ON DELETE CASCADE,
    question_type text,
    question_text jsonb NOT NULL,
    points numeric(6,2) DEFAULT 1,
    correct_answer jsonb,
    answer_options jsonb,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Assessment questions
CREATE TABLE assessment_questions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id uuid REFERENCES assessments(id) ON DELETE CASCADE,
    question_id uuid REFERENCES questions(id),
    points numeric(6,2) NOT NULL,
    sequence_order integer NOT NULL,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Rubric templates
CREATE TABLE rubric_templates (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name jsonb NOT NULL,
    course_id uuid REFERENCES courses(id),
    total_points numeric(6,2),
    created_by uuid REFERENCES users(id),
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Rubric criteria
CREATE TABLE rubric_criteria (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    rubric_id uuid REFERENCES rubric_templates(id) ON DELETE CASCADE,
    criterion_name jsonb NOT NULL,
    max_points numeric(6,2) NOT NULL,
    sequence_order integer NOT NULL,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_questions_bank ON questions(question_bank_id);
CREATE INDEX idx_assessment_questions_assessment ON assessment_questions(assessment_id);
CREATE INDEX idx_rubric_criteria_rubric ON rubric_criteria(rubric_id);

COMMIT;
```

---

## Prerequisites & Validation (Priority: MEDIUM)

```sql
-- ==============================================
-- PREREQUISITES & COURSE VALIDATION
-- ==============================================

BEGIN;

-- Prerequisite checks
CREATE TABLE prerequisite_checks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid REFERENCES students(id),
    course_id uuid REFERENCES courses(id),
    prerequisite_met boolean DEFAULT false,
    missing_prerequisites uuid[],
    checked_at timestamptz DEFAULT CURRENT_TIMESTAMP,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- Course waitlists
CREATE TABLE course_waitlists (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_offering_id uuid REFERENCES course_offerings(id) ON DELETE CASCADE,
    student_id uuid REFERENCES students(id),
    position integer NOT NULL,
    added_date timestamptz DEFAULT CURRENT_TIMESTAMP,
    status text DEFAULT 'active',
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_offering_id, student_id)
);

CREATE INDEX idx_prerequisite_checks_student ON prerequisite_checks(student_id);
CREATE INDEX idx_course_waitlists_offering ON course_waitlists(course_offering_id);
CREATE INDEX idx_course_waitlists_position ON course_waitlists(position);

-- Prerequisite validation function
CREATE OR REPLACE FUNCTION check_prerequisites(
    p_student_id uuid,
    p_course_id uuid
) RETURNS boolean AS $$
DECLARE
    v_prerequisites uuid[];
    v_completed uuid[];
BEGIN
    SELECT prerequisites INTO v_prerequisites FROM courses WHERE id = p_course_id;
    
    IF v_prerequisites IS NULL OR array_length(v_prerequisites, 1) = 0 THEN
        RETURN true;
    END IF;
    
    SELECT array_agg(DISTINCT co.course_id) INTO v_completed
    FROM course_enrollments ce
    JOIN course_offerings co ON ce.course_offering_id = co.id
    WHERE ce.student_id = p_student_id
    AND ce.enrollment_status = 'completed'
    AND ce.grade_points >= 2.0;
    
    RETURN v_prerequisites <@ COALESCE(v_completed, ARRAY[]::uuid[]);
END;
$$ LANGUAGE plpgsql;

COMMIT;
```

---

## Usage Instructions

### To implement Financial System:
```bash
# Copy SQL above and save to file
nano backend/migration/03_financial_system.sql
# Paste the Financial System SQL
# Execute
PGPASSWORD=1111 psql -U postgres -h localhost -d lms -f backend/migration/03_financial_system.sql
```

### To implement Library System:
```bash
nano backend/migration/04_library_system.sql
# Paste the Library System SQL
PGPASSWORD=1111 psql -U postgres -h localhost -d lms -f backend/migration/04_library_system.sql
```

### To implement Messaging:
```bash
nano backend/migration/05_messaging_system.sql
# Paste the Messaging System SQL
PGPASSWORD=1111 psql -U postgres -h localhost -d lms -f backend/migration/05_messaging_system.sql
```

### To implement Question Banks:
```bash
nano backend/migration/06_question_banks.sql
# Paste the Question Banks SQL
PGPASSWORD=1111 psql -U postgres -h localhost -d lms -f backend/migration/06_question_banks.sql
```

### To implement Prerequisites:
```bash
nano backend/migration/07_prerequisites.sql
# Paste the Prerequisites SQL
PGPASSWORD=1111 psql -U postgres -h localhost -d lms -f backend/migration/07_prerequisites.sql
```

---

## All Features Available

Refer to `DATABASE_STRUCTURE_ANALYSIS_AND_IMPROVEMENTS.md` for:
- Advanced scheduling features
- Reporting and analytics
- Student services tables
- Row-level security
- Performance optimization
- Complete documentation

**Everything is ready to implement!**
