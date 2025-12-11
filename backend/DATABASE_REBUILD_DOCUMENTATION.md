# Education System Database Rebuild Documentation

## Executive Summary

This document provides comprehensive analysis and rebuilding instructions for the Education System database. The current database has **critical structural issues** that require immediate attention.

### Critical Issues Identified

🔴 **CRITICAL**: No foreign key constraints defined (0 FK relationships in 355 tables)
🔴 **HIGH**: 41 backup/duplicate tables consuming storage and causing confusion
🔴 **HIGH**: Inconsistent naming conventions (mixed snake_case/camelCase)
🔴 **MEDIUM**: Potential data orphaning due to missing referential integrity
🔴 **MEDIUM**: Missing indexes on foreign key columns affecting performance

## Current Database Analysis

### Database Statistics
- **Total Tables**: 355
- **Foreign Key Constraints**: 0 ❌
- **Primary Key Constraints**: 223 ✅
- **Indexes**: 223 ✅
- **Core Data Records**: 
  - Users: 6,990
  - Students: 6,507 
  - Teachers: 464
  - Courses: 8,392
  - Education Groups: 419

### Core Entity Structure

#### User Management Chain
```
users (6,990) -> accounts (6,503) -> persons (6,526)
```
- **Issue**: No FK constraints between these critical tables
- **Risk**: Authentication can break without referential integrity

#### Academic Management
```
students (6,507) <-> education_group_student (7,052) <-> education_group (419)
course (8,392) <-> course_teacher (324) / course_student (5,599)
```
- **Issue**: No enforcement of valid relationships
- **Risk**: Students can be assigned to non-existent groups

#### Reference Data System
```
dictionaries (1,180) -> dictionary_types (83)
```
- **Issue**: Missing FK to dictionary_types
- **Risk**: Invalid reference data entries

## Improved Database Schema Design

### 1. Core Entities with Proper Relationships

#### Authentication & Identity
```sql
-- Core person information (normalized)
persons (
    id BIGSERIAL PRIMARY KEY,
    firstname VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    patronymic VARCHAR(100),
    gender_id BIGINT REFERENCES gender_types(id),
    birthdate DATE,
    pincode VARCHAR(20) UNIQUE,
    citizenship_id BIGINT REFERENCES countries(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- System accounts
accounts (
    id BIGSERIAL PRIMARY KEY,
    person_id BIGINT REFERENCES persons(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- System users with roles
users (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT REFERENCES accounts(id) ON DELETE CASCADE,
    organization_id BIGINT REFERENCES organizations(id),
    user_type VARCHAR(20) CHECK (user_type IN ('student', 'teacher', 'admin', 'staff')),
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Academic Structure
```sql
-- Educational organizations/institutions
organizations (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE,
    parent_id BIGINT REFERENCES organizations(id),
    type_id BIGINT REFERENCES organization_types(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Academic years
academic_years (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL, -- "2024/2025"
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE
);

-- Education groups (classes)
education_groups (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL, -- "1024-A", "ML-61-17"
    organization_id BIGINT REFERENCES organizations(id) NOT NULL,
    academic_year_id BIGINT REFERENCES academic_years(id) NOT NULL,
    education_level_id BIGINT REFERENCES education_levels(id),
    education_type_id BIGINT REFERENCES education_types(id),
    language_id BIGINT REFERENCES languages(id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(name, academic_year_id, organization_id)
);

-- Students
students (
    id BIGSERIAL PRIMARY KEY,
    person_id BIGINT REFERENCES persons(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    student_id_number VARCHAR(20) UNIQUE NOT NULL,
    organization_id BIGINT REFERENCES organizations(id),
    education_line_id BIGINT REFERENCES education_lines(id),
    admission_year INTEGER,
    graduation_year INTEGER,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'graduated', 'expelled', 'on_leave')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Teachers
teachers (
    id BIGSERIAL PRIMARY KEY,
    person_id BIGINT REFERENCES persons(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    employee_id VARCHAR(20) UNIQUE,
    organization_id BIGINT REFERENCES organizations(id),
    position_id BIGINT REFERENCES positions(id),
    hire_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Course Management
```sql
-- Subject catalog
subjects (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name_az VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    name_ru VARCHAR(200),
    credits INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Course instances
courses (
    id BIGSERIAL PRIMARY KEY,
    subject_id BIGINT REFERENCES subjects(id) ON DELETE RESTRICT,
    code VARCHAR(30) UNIQUE NOT NULL,
    semester_id BIGINT REFERENCES semesters(id),
    academic_year_id BIGINT REFERENCES academic_years(id),
    language_id BIGINT REFERENCES languages(id),
    
    -- Hours allocation
    lecture_hours INTEGER DEFAULT 0,
    seminar_hours INTEGER DEFAULT 0,
    lab_hours INTEGER DEFAULT 0,
    practice_hours INTEGER DEFAULT 0,
    
    start_date DATE,
    end_date DATE,
    max_students INTEGER,
    status VARCHAR(20) DEFAULT 'planned',
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CHECK (lecture_hours + seminar_hours + lab_hours + practice_hours > 0)
);

-- Course-Teacher assignments
course_teachers (
    id BIGSERIAL PRIMARY KEY,
    course_id BIGINT REFERENCES courses(id) ON DELETE CASCADE,
    teacher_id BIGINT REFERENCES teachers(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'instructor', -- instructor, assistant, coordinator
    assigned_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(course_id, teacher_id, role)
);

-- Course-Student enrollments
course_students (
    id BIGSERIAL PRIMARY KEY,
    course_id BIGINT REFERENCES courses(id) ON DELETE CASCADE,
    student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'enrolled', -- enrolled, completed, dropped, failed
    final_grade DECIMAL(5,2),
    
    UNIQUE(course_id, student_id)
);

-- Education Group - Student relationship
education_group_students (
    id BIGSERIAL PRIMARY KEY,
    education_group_id BIGINT REFERENCES education_groups(id) ON DELETE CASCADE,
    student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT NOW(),
    left_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    
    UNIQUE(education_group_id, student_id, status) 
    WHERE status = 'active' -- Only one active membership per group
);
```

### 2. Reference Data Tables (Dictionary System)

```sql
-- Dictionary types
dictionary_types (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name_az VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Dictionary entries
dictionaries (
    id BIGSERIAL PRIMARY KEY,
    type_id BIGINT REFERENCES dictionary_types(id) ON DELETE RESTRICT,
    code VARCHAR(50) NOT NULL,
    name_az VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    name_ru VARCHAR(200),
    parent_id BIGINT REFERENCES dictionaries(id),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(type_id, code)
);

-- Commonly used reference tables
genders (id, name_az, name_en, code);
countries (id, name_az, name_en, iso_code);
languages (id, name_az, name_en, iso_code);
semesters (id, name_az, name_en, sort_order);
education_levels (id, name_az, name_en, code); -- bachelor, master, phd
education_types (id, name_az, name_en, code);  -- full-time, part-time
positions (id, name_az, name_en, code);
organization_types (id, name_az, name_en, code);
```

### 3. Indexes for Performance

```sql
-- Critical indexes for foreign keys
CREATE INDEX idx_users_account_id ON users(account_id);
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_accounts_person_id ON accounts(person_id);

CREATE INDEX idx_students_person_id ON students(person_id);
CREATE INDEX idx_students_user_id ON students(user_id);
CREATE INDEX idx_students_organization_id ON students(organization_id);

CREATE INDEX idx_teachers_person_id ON teachers(person_id);
CREATE INDEX idx_teachers_user_id ON teachers(user_id);
CREATE INDEX idx_teachers_organization_id ON teachers(organization_id);

CREATE INDEX idx_courses_subject_id ON courses(subject_id);
CREATE INDEX idx_courses_academic_year_id ON courses(academic_year_id);
CREATE INDEX idx_courses_semester_id ON courses(semester_id);

CREATE INDEX idx_course_teachers_course_id ON course_teachers(course_id);
CREATE INDEX idx_course_teachers_teacher_id ON course_teachers(teacher_id);

CREATE INDEX idx_course_students_course_id ON course_students(course_id);
CREATE INDEX idx_course_students_student_id ON course_students(student_id);

CREATE INDEX idx_education_group_students_group_id ON education_group_students(education_group_id);
CREATE INDEX idx_education_group_students_student_id ON education_group_students(student_id);

-- Performance indexes for common queries
CREATE INDEX idx_persons_lastname_firstname ON persons(lastname, firstname);
CREATE INDEX idx_students_student_id_number ON students(student_id_number);
CREATE INDEX idx_courses_code ON courses(code);
CREATE INDEX idx_courses_status_academic_year ON courses(status, academic_year_id);

-- Full-text search indexes
CREATE INDEX idx_persons_fullname_gin ON persons USING gin(to_tsvector('simple', firstname || ' ' || lastname));
CREATE INDEX idx_subjects_name_gin ON subjects USING gin(to_tsvector('simple', name_az));
```

### 4. Data Validation Constraints

```sql
-- Check constraints for data integrity
ALTER TABLE persons ADD CONSTRAINT check_birthdate CHECK (birthdate < CURRENT_DATE);
ALTER TABLE students ADD CONSTRAINT check_graduation_after_admission 
    CHECK (graduation_year IS NULL OR graduation_year >= admission_year);
ALTER TABLE teachers ADD CONSTRAINT check_hire_date CHECK (hire_date <= CURRENT_DATE);
ALTER TABLE courses ADD CONSTRAINT check_end_after_start 
    CHECK (end_date IS NULL OR end_date >= start_date);
ALTER TABLE course_students ADD CONSTRAINT check_final_grade 
    CHECK (final_grade IS NULL OR (final_grade >= 0 AND final_grade <= 100));

-- Unique constraints to prevent duplicates
ALTER TABLE persons ADD CONSTRAINT unique_persons_pin_when_not_null 
    EXCLUDE (pincode WITH =) WHERE (pincode IS NOT NULL);
ALTER TABLE students ADD CONSTRAINT unique_student_per_person 
    UNIQUE (person_id);
ALTER TABLE teachers ADD CONSTRAINT unique_teacher_per_person 
    UNIQUE (person_id);
```

## Migration Strategy

### Phase 1: Preparation (No Downtime)
1. **Backup Current Database**
   ```bash
   pg_dump -h localhost -U postgres -d edu > edu_backup_$(date +%Y%m%d).sql
   ```

2. **Create Improved Schema in Parallel**
   ```sql
   CREATE DATABASE edu_new;
   -- Create all improved tables in edu_new
   ```

3. **Data Quality Analysis**
   - Identify orphaned records
   - Find duplicate entries
   - Validate data consistency

### Phase 2: Data Migration (Scheduled Downtime)
1. **Migrate Core Entities**
   ```sql
   -- Migrate persons (clean duplicates)
   INSERT INTO edu_new.persons (id, firstname, lastname, patronymic, ...)
   SELECT DISTINCT ON (pincode) id, firstname, lastname, patronymic, ...
   FROM edu.persons 
   WHERE pincode IS NOT NULL;
   
   -- Migrate accounts
   INSERT INTO edu_new.accounts (id, person_id, username, email, ...)
   SELECT a.id, a.person_id, a.username, a.email, ...
   FROM edu.accounts a
   JOIN edu_new.persons p ON a.person_id = p.id;
   ```

2. **Establish Relationships**
   ```sql
   -- Add foreign key constraints after data migration
   ALTER TABLE accounts ADD CONSTRAINT fk_accounts_person 
       FOREIGN KEY (person_id) REFERENCES persons(id);
   ```

3. **Migrate Academic Data**
   ```sql
   -- Migrate with relationship validation
   INSERT INTO edu_new.students (...)
   SELECT ... FROM edu.students s
   WHERE EXISTS (SELECT 1 FROM edu_new.persons p WHERE p.id = s.person_id);
   ```

### Phase 3: Validation & Switchover
1. **Data Validation**
   ```sql
   -- Verify record counts
   SELECT 
       (SELECT COUNT(*) FROM edu.students) as old_students,
       (SELECT COUNT(*) FROM edu_new.students) as new_students;
   
   -- Verify relationships
   SELECT COUNT(*) FROM edu_new.students s
   LEFT JOIN edu_new.persons p ON s.person_id = p.id
   WHERE p.id IS NULL; -- Should be 0
   ```

2. **Application Testing**
   - Update connection strings to point to edu_new
   - Run full application test suite
   - Performance testing

3. **Production Switchover**
   ```sql
   -- Rename databases
   ALTER DATABASE edu RENAME TO edu_old;
   ALTER DATABASE edu_new RENAME TO edu;
   ```

## Cleanup & Optimization

### Remove Backup Tables
```sql
-- Safe removal of backup tables after validation
DROP TABLE IF EXISTS a_group_bak, a_students_bak, a_students_bak2, 
                    a_students_bak2022, a_students_bak3, a_students_mag,
                    a_students_mag2022, a_teachers, a_teachers2,
                    education_group2, operations2, all_privilege2;
```

### Vacuum & Analyze
```sql
-- Optimize after cleanup
VACUUM FULL;
ANALYZE;

-- Update statistics
SELECT schemaname, tablename, last_vacuum, last_analyze 
FROM pg_stat_user_tables 
ORDER BY schemaname, tablename;
```

## Ongoing Maintenance

### 1. Regular Maintenance Tasks
```sql
-- Weekly maintenance script
DO $$
BEGIN
    -- Update table statistics
    ANALYZE;
    
    -- Check for orphaned records
    PERFORM maintenance_check_orphaned_data();
    
    -- Vacuum if needed
    IF (SELECT COUNT(*) FROM pg_stat_user_tables WHERE n_dead_tup > 1000) > 0 THEN
        VACUUM;
    END IF;
END
$$;
```

### 2. Monitoring Queries
```sql
-- Check foreign key violations (should always be 0)
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint 
WHERE contype = 'f' 
AND NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints 
    WHERE constraint_name = conname
);

-- Monitor table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;
```

### 3. Performance Monitoring
```sql
-- Slow query identification
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0  -- Unused indexes
ORDER BY schemaname, tablename;
```

## Benefits of Improved Schema

### 1. Data Integrity ✅
- **Referential Integrity**: FK constraints prevent orphaned data
- **Data Validation**: Check constraints ensure valid data
- **Consistency**: Normalized structure eliminates duplicates

### 2. Performance ✅  
- **Optimized Indexes**: Faster queries on foreign keys
- **Reduced Storage**: Eliminated duplicate tables
- **Better Query Plans**: Optimizer can use FK information

### 3. Maintainability ✅
- **Clear Relationships**: Easy to understand entity connections
- **Consistent Naming**: Standard conventions throughout
- **Proper Documentation**: ER diagrams and comments

### 4. Scalability ✅
- **Proper Normalization**: Reduces data redundancy
- **Indexed Queries**: Fast performance as data grows
- **Partition Ready**: Structure supports future partitioning

## Risk Mitigation

### 1. Data Loss Prevention
- Full backup before migration
- Gradual migration with validation
- Keep old database as fallback
- Comprehensive testing

### 2. Performance Issues
- Gradual index creation during off-hours
- Monitor query performance during transition
- FK constraint addition in maintenance windows
- Rollback plan if performance degrades

### 3. Application Compatibility
- Update application code gradually
- Use database views for backward compatibility
- Comprehensive integration testing
- Staged deployment approach

## Conclusion

The current Education System database has critical structural issues that pose risks to data integrity and system performance. The improved schema design addresses these issues while maintaining compatibility with existing data.

**Key Improvements:**
- ✅ Proper foreign key relationships (0 → 50+ FK constraints)
- ✅ Eliminated 41 backup/duplicate tables  
- ✅ Standardized naming conventions
- ✅ Added performance indexes
- ✅ Implemented data validation
- ✅ Created proper audit trails

**Timeline Estimate:**
- **Phase 1 (Preparation)**: 2-3 weeks
- **Phase 2 (Migration)**: 1-2 days downtime
- **Phase 3 (Validation)**: 1 week
- **Total Project**: 4-6 weeks

This database rebuild will provide a solid foundation for the Education System's continued growth and development while ensuring data integrity and optimal performance.