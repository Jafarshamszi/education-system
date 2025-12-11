# Database Migration Implementation Guide

## Overview
This guide provides the complete step-by-step process for implementing the database migration from the current problematic structure to the improved normalized schema. Follow these phases carefully to ensure zero data loss and minimal downtime.

## Pre-Migration Checklist

### System Requirements
- [ ] PostgreSQL 15+ installed and accessible
- [ ] Sufficient disk space (current database size × 3 for safety)
- [ ] Database admin access with CREATE DATABASE privileges
- [ ] Application services can be stopped during migration window
- [ ] Team coordination for maintenance window scheduling

### Backup Strategy
- [ ] Full database backup created and verified
- [ ] Schema-only backup for reference
- [ ] Data-only backup for comparison
- [ ] Application code backup with current configurations
- [ ] Test restore procedure validated

### Testing Environment
- [ ] Migration scripts tested on database copy
- [ ] Data integrity validation scripts prepared
- [ ] Performance benchmarks established
- [ ] Rollback procedures tested and documented
- [ ] Application connectivity tested with new schema

## Phase 1: Preparation (Days 1-7)

### Day 1-2: Environment Setup
```bash
# Create working directories
mkdir -p /tmp/edu_migration/{backups,exports,logs,scripts}

# Set permissions and environment variables
export PGUSER=postgres
export PGPASSWORD=1111
export PGHOST=localhost
export OLD_DB=edu
export NEW_DB=edu_new
export BACKUP_DIR=/tmp/edu_migration/backups
export LOG_FILE=/tmp/edu_migration/logs/migration_$(date +%Y%m%d_%H%M%S).log

# Create comprehensive backup
pg_dump -h localhost -U postgres -d edu \
    --create --clean --if-exists \
    --format=custom --compress=9 \
    --file="$BACKUP_DIR/edu_full_backup_$(date +%Y%m%d_%H%M%S).backup"

# Verify backup integrity
pg_restore --list "$BACKUP_DIR/edu_full_backup_*.backup" > "$BACKUP_DIR/backup_contents.txt"
```

### Day 3-4: Schema Analysis and Validation
```bash
# Run comprehensive database analysis
cd /path/to/education-system/backend
python comprehensive_db_analysis.py > "$LOG_FILE"

# Analyze current issues
python analyze_critical_issues.py

# Document all existing relationships
python analyze_relationships.py

# Create data quality report
psql -h localhost -U postgres -d edu -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows
FROM pg_stat_user_tables 
ORDER BY n_live_tup DESC;
" > "$BACKUP_DIR/table_statistics.txt"
```

### Day 5-7: Migration Scripts Preparation
```bash
# Copy migration scripts to working directory
cp DATABASE_MIGRATION_SCRIPTS.sql /tmp/edu_migration/scripts/

# Split migration into manageable chunks
split -l 100 /tmp/edu_migration/scripts/DATABASE_MIGRATION_SCRIPTS.sql \
    /tmp/edu_migration/scripts/migration_part_

# Create validation scripts
cat > /tmp/edu_migration/scripts/validate_migration.sql << 'EOF'
-- Pre-migration counts
\c edu
CREATE TEMP TABLE pre_migration_counts AS
SELECT 'persons' as table_name, COUNT(*) as count FROM persons
UNION ALL SELECT 'students', COUNT(*) FROM students  
UNION ALL SELECT 'teachers', COUNT(*) FROM teachers
UNION ALL SELECT 'course', COUNT(*) FROM course
UNION ALL SELECT 'education_group', COUNT(*) FROM education_group;

-- Export for comparison
\copy pre_migration_counts TO '/tmp/edu_migration/exports/pre_migration_counts.csv' CSV HEADER;
EOF
```

## Phase 2: Schema Creation (Days 8-10)

### Day 8: New Database Creation
```bash
# Create new database
psql -h localhost -U postgres -c "
CREATE DATABASE edu_new 
    WITH OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;"

# Enable required extensions
psql -h localhost -U postgres -d edu_new -c "
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";
CREATE EXTENSION IF NOT EXISTS \"unaccent\";"

# Log creation success
echo "$(date): New database 'edu_new' created successfully" >> "$LOG_FILE"
```

### Day 9: Reference Tables Creation
```bash
# Create reference and lookup tables first
psql -h localhost -U postgres -d edu_new -f /tmp/edu_migration/scripts/01_reference_tables.sql

# Verify reference tables creation
psql -h localhost -U postgres -d edu_new -c "
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;" > "$BACKUP_DIR/new_tables_reference.txt"
```

### Day 10: Core Schema Creation
```bash
# Create main entity tables
psql -h localhost -U postgres -d edu_new -f /tmp/edu_migration/scripts/02_core_schema.sql

# Create indexes and constraints
psql -h localhost -U postgres -d edu_new -f /tmp/edu_migration/scripts/03_indexes_constraints.sql

# Verify schema creation
psql -h localhost -U postgres -d edu_new -c "
SELECT 
    t.table_name,
    COUNT(c.column_name) as column_count,
    COUNT(tc.constraint_name) as constraint_count
FROM information_schema.tables t
LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
LEFT JOIN information_schema.table_constraints tc ON t.table_name = tc.table_name
WHERE t.table_schema = 'public'
GROUP BY t.table_name
ORDER BY t.table_name;" > "$BACKUP_DIR/new_schema_summary.txt"
```

## Phase 3: Data Migration (Days 11-14)

### Day 11: Reference Data Migration
```bash
# Start data migration log
echo "$(date): Starting data migration phase" >> "$LOG_FILE"

# Export reference data from old database
psql -h localhost -U postgres -d edu -c "
-- Dictionary types export
\copy (SELECT DISTINCT type_id, 'TYPE_' || type_id as code, 'Legacy Type ' || type_id as name_az FROM dictionaries WHERE type_id IS NOT NULL) TO '/tmp/edu_migration/exports/dictionary_types.csv' CSV HEADER;

-- Dictionaries export  
\copy (SELECT id, type_id, code, name_az, name_en, name_ru, parent_id FROM dictionaries WHERE type_id IS NOT NULL) TO '/tmp/edu_migration/exports/dictionaries.csv' CSV HEADER;

-- Organizations export
\copy (SELECT id, name_az, name_en, code, parent_id, type_id, CASE WHEN active = 1 THEN TRUE ELSE FALSE END, create_date, update_date FROM organizations WHERE name_az IS NOT NULL) TO '/tmp/edu_migration/exports/organizations.csv' CSV HEADER;"

# Import reference data to new database
psql -h localhost -U postgres -d edu_new -c "
\copy dictionary_types(id, code, name_az) FROM '/tmp/edu_migration/exports/dictionary_types.csv' CSV HEADER;
\copy dictionaries(id, type_id, code, name_az, name_en, name_ru, parent_id) FROM '/tmp/edu_migration/exports/dictionaries.csv' CSV HEADER;
\copy organizations(id, name_az, name_en, code, parent_id, is_active, created_at, updated_at) FROM '/tmp/edu_migration/exports/organizations.csv' CSV HEADER;

-- Update sequences
SELECT setval('dictionary_types_id_seq', (SELECT MAX(id) FROM dictionary_types));
SELECT setval('dictionaries_id_seq', (SELECT MAX(id) FROM dictionaries));
SELECT setval('organizations_id_seq', (SELECT MAX(id) FROM organizations));"

echo "$(date): Reference data migration completed" >> "$LOG_FILE"
```

### Day 12: Person and Account Migration
```bash
# Export cleaned person data
psql -h localhost -U postgres -d edu -c "
-- Clean persons export with deduplication
\copy (
  SELECT DISTINCT ON (COALESCE(pincode, firstname||lastname||birthdate::text))
    id, firstname, lastname, patronymic, gender_id, birthdate, pincode, 
    citizenship_id, create_date, update_date
  FROM persons 
  WHERE firstname IS NOT NULL AND lastname IS NOT NULL
  ORDER BY COALESCE(pincode, firstname||lastname||birthdate::text), id
) TO '/tmp/edu_migration/exports/persons_clean.csv' CSV HEADER;

-- Clean accounts export
\copy (
  SELECT DISTINCT ON (username)
    a.id, a.person_id, a.username, a.email, a.password,
    CASE WHEN a.activity_status = 1 THEN TRUE ELSE FALSE END,
    a.create_date, a.update_date
  FROM accounts a
  INNER JOIN persons p ON a.person_id = p.id
  WHERE a.username IS NOT NULL
  ORDER BY username, a.id
) TO '/tmp/edu_migration/exports/accounts_clean.csv' CSV HEADER;

-- Clean users export  
\copy (
  SELECT u.id, u.account_id, u.organization_id,
    CASE WHEN u.user_type = 1 THEN 'student'
         WHEN u.user_type = 2 THEN 'teacher'
         WHEN u.user_type = 3 THEN 'admin'
         ELSE 'staff' END,
    CASE WHEN u.is_blocked = 1 THEN TRUE ELSE FALSE END,
    u.create_date, u.update_date
  FROM users u
  INNER JOIN accounts a ON u.account_id = a.id
  INNER JOIN persons p ON a.person_id = p.id
) TO '/tmp/edu_migration/exports/users_clean.csv' CSV HEADER;"

# Import person and account data
psql -h localhost -U postgres -d edu_new -c "
\copy persons(id, firstname, lastname, patronymic, gender_id, birthdate, pincode, citizenship_id, created_at, updated_at) FROM '/tmp/edu_migration/exports/persons_clean.csv' CSV HEADER;
\copy accounts(id, person_id, username, email, password_hash, is_active, created_at, updated_at) FROM '/tmp/edu_migration/exports/accounts_clean.csv' CSV HEADER;  
\copy users(id, account_id, organization_id, user_type, is_blocked, created_at, updated_at) FROM '/tmp/edu_migration/exports/users_clean.csv' CSV HEADER;

-- Update sequences
SELECT setval('persons_id_seq', (SELECT MAX(id) FROM persons));
SELECT setval('accounts_id_seq', (SELECT MAX(id) FROM accounts));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));"

echo "$(date): Person and account migration completed" >> "$LOG_FILE"
```

### Day 13: Academic Entity Migration
```bash
# Export students and teachers
psql -h localhost -U postgres -d edu -c "
-- Students export
\copy (
  SELECT s.id, s.person_id, s.user_id, 
    COALESCE(s.card_number, 'STU' || s.id::text),
    s.org_id, EXTRACT(YEAR FROM s.in_order_date::date),
    CASE WHEN s.active = 1 THEN 'active' ELSE 'graduated' END,
    s.create_date, s.update_date
  FROM students s
  INNER JOIN persons p ON s.person_id = p.id
) TO '/tmp/edu_migration/exports/students_clean.csv' CSV HEADER;

-- Teachers export
\copy (
  SELECT t.id, t.person_id, t.user_id, t.card_number, t.organization_id,
    t.position_id, t.in_action_date::date,
    CASE WHEN t.active = 1 THEN 'active' ELSE 'terminated' END,
    t.create_date, t.update_date
  FROM teachers t  
  INNER JOIN persons p ON t.person_id = p.id
) TO '/tmp/edu_migration/exports/teachers_clean.csv' CSV HEADER;

-- Education groups export
\copy (
  SELECT eg.id, eg.name, eg.organization_id, 
    COALESCE(eg.education_year_id, 1),
    eg.education_level_id, eg.education_type_id, eg.education_lang_id,
    eg.tyutor_id, CASE WHEN eg.active = 1 THEN TRUE ELSE FALSE END,
    eg.create_date, eg.update_date
  FROM education_group eg
  WHERE eg.name IS NOT NULL
) TO '/tmp/edu_migration/exports/education_groups.csv' CSV HEADER;"

# Insert academic years first
psql -h localhost -U postgres -d edu_new -c "
INSERT INTO academic_years (id, name, start_date, end_date, is_current) VALUES 
(1, '2024/2025', '2024-09-01', '2025-06-30', TRUE),
(2, '2023/2024', '2023-09-01', '2024-06-30', FALSE),
(3, '2025/2026', '2025-09-01', '2026-06-30', FALSE);"

# Import academic entities
psql -h localhost -U postgres -d edu_new -c "
\copy students(id, person_id, user_id, student_id_number, organization_id, admission_year, status, created_at, updated_at) FROM '/tmp/edu_migration/exports/students_clean.csv' CSV HEADER;
\copy teachers(id, person_id, user_id, employee_id, organization_id, position_id, hire_date, status, created_at, updated_at) FROM '/tmp/edu_migration/exports/teachers_clean.csv' CSV HEADER;
\copy education_groups(id, name, organization_id, academic_year_id, education_level_id, education_type_id, language_id, tutor_id, is_active, created_at, updated_at) FROM '/tmp/edu_migration/exports/education_groups.csv' CSV HEADER;

-- Update sequences
SELECT setval('students_id_seq', (SELECT MAX(id) FROM students));
SELECT setval('teachers_id_seq', (SELECT MAX(id) FROM teachers));
SELECT setval('education_groups_id_seq', (SELECT MAX(id) FROM education_groups));"

echo "$(date): Academic entity migration completed" >> "$LOG_FILE"
```

### Day 14: Course and Relationship Migration
```bash
# Export courses and relationships
psql -h localhost -U postgres -d edu -c "
-- Subjects export
\copy (
  SELECT DISTINCT eps.subject_id, 
    COALESCE(eps.code, 'SUBJ' || eps.subject_id::text),
    eps.name_az, eps.name_en, eps.name_ru, COALESCE(eps.credits, 0)
  FROM education_plan_subject eps
  WHERE eps.subject_id IS NOT NULL AND eps.name_az IS NOT NULL
) TO '/tmp/edu_migration/exports/subjects.csv' CSV HEADER;

-- Courses export
\copy (
  SELECT c.id, c.education_plan_subject_id, c.code, c.semester_id,
    COALESCE(c.education_year_id, 1), c.education_lang_id,
    COALESCE(c.m_hours, 0), COALESCE(c.s_hours, 0), 
    COALESCE(c.l_hours, 0), COALESCE(c.fm_hours, 0),
    c.start_date::date, c.student_count,
    CASE WHEN c.active = 1 THEN 'active' ELSE 'planned' END,
    c.create_date, c.update_date
  FROM course c WHERE c.code IS NOT NULL
) TO '/tmp/edu_migration/exports/courses.csv' CSV HEADER;

-- Course relationships
\copy (SELECT ct.id, ct.course_id, ct.teacher_id, 'instructor', ct.create_date FROM course_teacher ct) TO '/tmp/edu_migration/exports/course_teachers.csv' CSV HEADER;
\copy (SELECT cs.id, cs.course_id, cs.student_id, cs.create_date, CASE WHEN cs.active = 1 THEN 'enrolled' ELSE 'completed' END FROM course_student cs) TO '/tmp/edu_migration/exports/course_students.csv' CSV HEADER;
\copy (SELECT egs.id, egs.education_group_id, egs.student_id, egs.create_date, CASE WHEN egs.active = 1 THEN 'active' ELSE 'transferred' END FROM education_group_student egs) TO '/tmp/edu_migration/exports/group_students.csv' CSV HEADER;"

# Import courses and relationships
psql -h localhost -U postgres -d edu_new -c "
\copy subjects(id, code, name_az, name_en, name_ru, credits) FROM '/tmp/edu_migration/exports/subjects.csv' CSV HEADER;
\copy courses(id, subject_id, code, semester_id, academic_year_id, language_id, lecture_hours, seminar_hours, lab_hours, practice_hours, start_date, max_students, status, created_at, updated_at) FROM '/tmp/edu_migration/exports/courses.csv' CSV HEADER;
\copy course_teachers(id, course_id, teacher_id, role, assigned_at) FROM '/tmp/edu_migration/exports/course_teachers.csv' CSV HEADER;
\copy course_students(id, course_id, student_id, enrolled_at, status) FROM '/tmp/edu_migration/exports/course_students.csv' CSV HEADER;
\copy education_group_students(id, education_group_id, student_id, joined_at, status) FROM '/tmp/edu_migration/exports/group_students.csv' CSV HEADER;

-- Update all remaining sequences
SELECT setval('subjects_id_seq', (SELECT MAX(id) FROM subjects));
SELECT setval('courses_id_seq', (SELECT MAX(id) FROM courses));
SELECT setval('course_teachers_id_seq', (SELECT MAX(id) FROM course_teachers));
SELECT setval('course_students_id_seq', (SELECT MAX(id) FROM course_students));
SELECT setval('education_group_students_id_seq', (SELECT MAX(id) FROM education_group_students));"

echo "$(date): Course and relationship migration completed" >> "$LOG_FILE"
```

## Phase 4: Validation and Testing (Days 15-17)

### Day 15: Data Integrity Validation
```bash
# Run comprehensive data integrity checks
psql -h localhost -U postgres -d edu_new -f /tmp/edu_migration/scripts/validation_checks.sql > "$BACKUP_DIR/validation_results.txt"

# Check for orphaned records
psql -h localhost -U postgres -d edu_new -c "
-- Orphaned records check (all should return 0)
SELECT 'orphaned_accounts' as check_name, COUNT(*) as count
FROM accounts a LEFT JOIN persons p ON a.person_id = p.id WHERE p.id IS NULL
UNION ALL
SELECT 'orphaned_users', COUNT(*) 
FROM users u LEFT JOIN accounts a ON u.account_id = a.id WHERE a.id IS NULL
UNION ALL
SELECT 'orphaned_students', COUNT(*)
FROM students s LEFT JOIN persons p ON s.person_id = p.id WHERE p.id IS NULL
UNION ALL  
SELECT 'orphaned_teachers', COUNT(*)
FROM teachers t LEFT JOIN persons p ON t.person_id = p.id WHERE p.id IS NULL
UNION ALL
SELECT 'orphaned_group_students', COUNT(*)
FROM education_group_students egs 
LEFT JOIN education_groups eg ON egs.education_group_id = eg.id
LEFT JOIN students s ON egs.student_id = s.id  
WHERE eg.id IS NULL OR s.id IS NULL;" > "$BACKUP_DIR/orphaned_records_check.txt"

# Verify record counts match
cat > /tmp/edu_migration/scripts/count_comparison.sql << 'EOF'
-- Old database counts
\c edu  
\copy (SELECT 'OLD_persons', COUNT(*) FROM persons) TO '/tmp/edu_migration/exports/old_counts.csv' CSV;
\copy (SELECT 'OLD_students', COUNT(*) FROM students) TO '/tmp/edu_migration/exports/old_counts.csv' CSV APPEND;
\copy (SELECT 'OLD_teachers', COUNT(*) FROM teachers) TO '/tmp/edu_migration/exports/old_counts.csv' CSV APPEND;

-- New database counts
\c edu_new
\copy (SELECT 'NEW_persons', COUNT(*) FROM persons) TO '/tmp/edu_migration/exports/new_counts.csv' CSV;  
\copy (SELECT 'NEW_students', COUNT(*) FROM students) TO '/tmp/edu_migration/exports/new_counts.csv' CSV APPEND;
\copy (SELECT 'NEW_teachers', COUNT(*) FROM teachers) TO '/tmp/edu_migration/exports/new_counts.csv' CSV APPEND;
EOF

psql -h localhost -U postgres -f /tmp/edu_migration/scripts/count_comparison.sql
```

### Day 16: Functional Testing
```bash
# Test key relationships and queries
psql -h localhost -U postgres -d edu_new -c "
-- Test student-person relationship
SELECT 'Student-Person Join Test', COUNT(*) 
FROM students s JOIN persons p ON s.person_id = p.id;

-- Test teacher-person relationship  
SELECT 'Teacher-Person Join Test', COUNT(*)
FROM teachers t JOIN persons p ON t.person_id = p.id;

-- Test user-account-person chain
SELECT 'User-Account-Person Chain Test', COUNT(*)
FROM users u 
JOIN accounts a ON u.account_id = a.id
JOIN persons p ON a.person_id = p.id;

-- Test education group memberships
SELECT 'Active Group Memberships Test', COUNT(*)
FROM education_group_students egs
JOIN education_groups eg ON egs.education_group_id = eg.id  
JOIN students s ON egs.student_id = s.id
WHERE egs.status = 'active';

-- Test course enrollments
SELECT 'Course Enrollments Test', COUNT(*)
FROM course_students cs
JOIN courses c ON cs.course_id = c.id
JOIN students s ON cs.student_id = s.id;" > "$BACKUP_DIR/functional_test_results.txt"

echo "$(date): Functional testing completed" >> "$LOG_FILE"
```

### Day 17: Performance Testing
```bash
# Create performance test queries
cat > /tmp/edu_migration/scripts/performance_tests.sql << 'EOF'
-- Time key queries to establish baseline
\timing on

-- Query 1: Student lookup with details
EXPLAIN ANALYZE
SELECT p.firstname, p.lastname, s.student_id_number, eg.name as group_name
FROM students s
JOIN persons p ON s.person_id = p.id  
LEFT JOIN education_group_students egs ON s.id = egs.student_id AND egs.status = 'active'
LEFT JOIN education_groups eg ON egs.education_group_id = eg.id
WHERE s.status = 'active'
LIMIT 100;

-- Query 2: Course enrollment summary  
EXPLAIN ANALYZE
SELECT c.code, subj.name_az, COUNT(cs.student_id) as enrolled_count
FROM courses c
JOIN subjects subj ON c.subject_id = subj.id
LEFT JOIN course_students cs ON c.id = cs.course_id AND cs.status = 'enrolled'  
WHERE c.status = 'active'
GROUP BY c.code, subj.name_az
ORDER BY enrolled_count DESC
LIMIT 50;

-- Query 3: Teacher workload
EXPLAIN ANALYZE  
SELECT p.firstname, p.lastname, COUNT(ct.course_id) as course_count
FROM teachers t
JOIN persons p ON t.person_id = p.id
LEFT JOIN course_teachers ct ON t.id = ct.teacher_id
WHERE t.status = 'active'
GROUP BY t.id, p.firstname, p.lastname
ORDER BY course_count DESC
LIMIT 20;
EOF

psql -h localhost -U postgres -d edu_new -f /tmp/edu_migration/scripts/performance_tests.sql > "$BACKUP_DIR/performance_results.txt"

echo "$(date): Performance testing completed" >> "$LOG_FILE"
```

## Phase 5: Application Integration (Days 18-21)

### Day 18-19: Backend Integration
```bash
# Update FastAPI database connection
cd /path/to/education-system/backend
cp app/core/database.py app/core/database.py.backup

# Modify database connection to use new database
sed -i 's/database=edu/database=edu_new/g' app/core/database.py

# Test backend API endpoints
python -m pytest tests/ -v > "$BACKUP_DIR/api_test_results.txt"

# Test specific endpoints with real data
curl -X GET "http://localhost:8000/teachers" > "$BACKUP_DIR/teachers_api_test.json"
curl -X GET "http://localhost:8000/education-groups" > "$BACKUP_DIR/groups_api_test.json"
curl -X GET "http://localhost:8000/courses" > "$BACKUP_DIR/courses_api_test.json"

echo "$(date): Backend integration testing completed" >> "$LOG_FILE"
```

### Day 20-21: Frontend Integration  
```bash
# Update frontend API calls if needed
cd /path/to/education-system/frontend

# Test frontend connectivity
bun run build
bun run start &
FRONTEND_PID=$!

# Test key frontend functionality
curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000" > "$BACKUP_DIR/frontend_status.txt"

# Stop test frontend
kill $FRONTEND_PID

echo "$(date): Frontend integration testing completed" >> "$LOG_FILE"
```

## Phase 6: Production Deployment (Days 22-28)

### Day 22-24: Final Preparation
```bash
# Create production deployment checklist
cat > /tmp/edu_migration/DEPLOYMENT_CHECKLIST.md << 'EOF'
# Production Deployment Checklist

## Pre-Deployment
- [ ] All tests passing in staging environment
- [ ] Database backup verified and tested
- [ ] Migration scripts tested on production-size dataset
- [ ] Rollback procedures documented and tested
- [ ] Team notification sent for maintenance window
- [ ] Monitoring alerts configured for migration

## During Deployment  
- [ ] Maintenance mode enabled
- [ ] Application services stopped
- [ ] Final database backup created
- [ ] Migration executed successfully
- [ ] Data validation passed
- [ ] Application services restarted with new database
- [ ] Basic functionality verified

## Post-Deployment
- [ ] Full functional testing completed
- [ ] Performance monitoring active
- [ ] User acceptance testing passed
- [ ] Old database archived
- [ ] Documentation updated
- [ ] Team notification sent for completion
EOF

# Final validation run
echo "$(date): Starting final validation" >> "$LOG_FILE"
psql -h localhost -U postgres -d edu_new -f /tmp/edu_migration/scripts/final_validation.sql > "$BACKUP_DIR/final_validation.txt"
```

### Day 25-26: Production Migration
```bash
# Production migration day
echo "$(date): PRODUCTION MIGRATION STARTED" >> "$LOG_FILE"

# Enable maintenance mode (application-specific)
# touch /var/www/education-system/maintenance.flag

# Stop application services
# systemctl stop education-backend
# systemctl stop education-frontend

# Create final production backup
pg_dump -h localhost -U postgres -d edu \
    --create --clean --if-exists \
    --format=custom --compress=9 \
    --file="$BACKUP_DIR/edu_production_backup_$(date +%Y%m%d_%H%M%S).backup"

# Execute migration (this may take several hours)
time psql -h localhost -U postgres -f DATABASE_MIGRATION_SCRIPTS.sql > "$LOG_FILE.migration" 2>&1

# Verify migration success
if [ $? -eq 0 ]; then
    echo "$(date): Migration completed successfully" >> "$LOG_FILE"
    
    # Rename databases
    psql -h localhost -U postgres -c "ALTER DATABASE edu RENAME TO edu_legacy;"
    psql -h localhost -U postgres -c "ALTER DATABASE edu_new RENAME TO edu;"
    
    # Update application configuration to use 'edu' database
    sed -i 's/database=edu_new/database=edu/g' /path/to/education-system/backend/app/core/database.py
    
    # Restart services
    # systemctl start education-backend
    # systemctl start education-frontend
    
    # Disable maintenance mode
    # rm /var/www/education-system/maintenance.flag
    
    echo "$(date): PRODUCTION MIGRATION COMPLETED SUCCESSFULLY" >> "$LOG_FILE"
else
    echo "$(date): Migration failed - initiating rollback" >> "$LOG_FILE"
    # Rollback procedure would go here
fi
```

### Day 27-28: Post-Migration Validation
```bash
# Monitor application health
for i in {1..24}; do
    echo "$(date): Health check #$i" >> "$LOG_FILE"
    
    # Check database connectivity
    psql -h localhost -U postgres -d edu -c "SELECT 1;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Database: OK" >> "$LOG_FILE"
    else  
        echo "Database: FAILED" >> "$LOG_FILE"
    fi
    
    # Check API health
    curl -s -f "http://localhost:8000/health" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "API: OK" >> "$LOG_FILE"  
    else
        echo "API: FAILED" >> "$LOG_FILE"
    fi
    
    # Check frontend health
    curl -s -f "http://localhost:3000" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Frontend: OK" >> "$LOG_FILE"
    else
        echo "Frontend: FAILED" >> "$LOG_FILE"
    fi
    
    sleep 3600  # Wait 1 hour between checks
done

echo "$(date): Migration implementation completed successfully" >> "$LOG_FILE"
```

## Rollback Procedures

### Emergency Rollback (if migration fails)
```bash
# Stop all services immediately
# systemctl stop education-backend education-frontend

# Restore from backup
pg_restore -h localhost -U postgres -d postgres \
    --clean --create --if-exists \
    "$BACKUP_DIR/edu_production_backup_*.backup"

# Revert application configuration  
sed -i 's/database=edu_new/database=edu/g' /path/to/education-system/backend/app/core/database.py

# Restart services
# systemctl start education-backend education-frontend

# Verify rollback success
psql -h localhost -U postgres -d edu -c "SELECT COUNT(*) FROM persons;"

echo "$(date): Emergency rollback completed" >> "$LOG_FILE"
```

### Success Criteria
The migration is considered successful when:
- [ ] All data integrity checks pass with 0 orphaned records
- [ ] Record counts match between old and new databases
- [ ] All API endpoints return expected data
- [ ] Frontend displays data correctly
- [ ] Performance meets or exceeds baseline
- [ ] No errors in application logs for 24 hours post-migration

### Timeline Summary
- **Total Duration**: 28 days
- **Preparation Phase**: 14 days (50%)  
- **Migration Execution**: 4 days (14%)
- **Testing and Integration**: 7 days (25%)
- **Production Deployment**: 3 days (11%)

This comprehensive implementation guide ensures a structured, safe, and verifiable migration process from the current problematic database to the improved normalized schema.