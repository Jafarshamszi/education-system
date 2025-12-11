# Complete Database Migration Guide
## Education System: Old Database (edu) → New Database (edu_v2)

**Migration Date:** October 3, 2025  
**Version:** 1.0  
**Status:** Ready for Execution

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Pre-Migration Checklist](#pre-migration-checklist)
3. [Migration Timeline](#migration-timeline)
4. [Step-by-Step Execution](#step-by-step-execution)
5. [Validation Procedures](#validation-procedures)
6. [Rollback Procedures](#rollback-procedures)
7. [Post-Migration Tasks](#post-migration-tasks)
8. [Troubleshooting](#troubleshooting)

---

## Executive Summary

This migration transforms the Baku Business University LMS database from a legacy structure (355 tables, 0 FK constraints) to a modern, normalized schema with:

- **UUID primary keys** for security and distribution
- **Proper foreign key constraints** for data integrity
- **Multilingual support** (Azerbaijani, Russian, English)
- **Row-level security** for access control
- **Comprehensive audit trails**
- **Optimized indexes** for performance

### Migration Scope

| Entity | Old Database | New Database | Transformation |
|--------|--------------|--------------|----------------|
| Users | 6,987 rows | All migrated | Integer ID → UUID |
| Students | 6,344 rows | All migrated | Add academic program link |
| Teachers | 424 rows | All migrated → staff_members | Add position metadata |
| Organizations | 419 rows | All migrated → organization_units | Add hierarchy types |
| Courses | 6,020 rows | Split into courses + offerings | Normalize structure |
| Grades | 3.2M rows | All migrated | Link to assessments |

---

## Pre-Migration Checklist

### 1. System Requirements

- [  ] PostgreSQL 15+ installed and running
- [  ] Python 3.10+ with required packages:
  ```bash
  pip install psycopg2-binary
  ```
- [  ] Minimum 50GB free disk space
- [  ] Database backup tools available

### 2. Database Preparation

#### Create New Database

```bash
# Connect to PostgreSQL
psql -U postgres -h localhost

# Create new database
CREATE DATABASE edu_v2;
\c edu_v2

# Run schema creation script
\i /path/to/new_database_schema.sql
```

#### Backup Old Database

```bash
# Full backup of old database
pg_dump -U postgres -h localhost -Fc edu > edu_backup_$(date +%Y%m%d_%H%M%S).dump

# Also create SQL backup for easy inspection
pg_dump -U postgres -h localhost edu > edu_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 3. Verify Connections

```bash
# Test old database connection
psql -U postgres -h localhost -d edu -c "SELECT COUNT(*) FROM users;"

# Test new database connection
psql -U postgres -h localhost -d edu_v2 -c "SELECT COUNT(*) FROM users;"
```

### 4. Review Documentation

- [  ] Read `OLD_TO_NEW_SCHEMA_MAPPING.md`
- [  ] Review `new_database_schema.sql`
- [  ] Understand rollback procedures
- [  ] Notify stakeholders of migration window

---

## Migration Timeline

### Recommended Schedule

**Total Duration:** 2-3 hours (depending on data volume)

| Phase | Task | Duration | Dependencies |
|-------|------|----------|--------------|
| 0 | Pre-migration setup | 30 min | - |
| 1 | Migrate Users & Persons | 30 min | Phase 0 |
| 2 | Migrate Students & Staff | 30 min | Phase 1 |
| 3 | Migrate Organizations | 20 min | Phase 2 |
| 4 | Migrate Courses | 40 min | Phase 3 |
| 5 | Migrate Enrollments & Grades | 60 min | Phase 4 |
| 6 | Validation & Testing | 30 min | Phase 5 |
| 7 | Application Cutover | 15 min | Phase 6 |

### Maintenance Window

**Recommended Time:** Saturday 2:00 AM - 6:00 AM (low usage period)

---

## Step-by-Step Execution

### Phase 0: Pre-Migration Setup

```bash
# 1. Stop application services
sudo systemctl stop fastapi_service
sudo systemctl stop django_service
sudo systemctl stop nginx

# 2. Set database to read-only mode (optional - for safety)
psql -U postgres -h localhost -d edu -c "ALTER DATABASE edu SET default_transaction_read_only = on;"

# 3. Create migration working directory
mkdir -p /home/axel/Developer/Education-system/backend/migration/logs
cd /home/axel/Developer/Education-system/backend/migration

# 4. Verify backup exists
ls -lh edu_backup_*.dump
```

### Phase 1: Migrate Users & Persons

**Estimated Time:** 30 minutes  
**Data Volume:** ~7,000 users

```bash
# Run Phase 1 migration
python3 migrate_database.py --phase 1

# Expected output:
# ============================================================
# PHASE 1: MIGRATING USERS
# ============================================================
# Found 6987 users to migrate
# ✓ Migrated 6987 users successfully
# 
# MIGRATING PERSONS...
# Found 6987 persons to migrate
# ✓ Migrated 6987 persons successfully
```

#### Validation

```sql
-- Check user counts match
SELECT 'OLD' as db, COUNT(*) FROM edu.users
UNION ALL
SELECT 'NEW' as db, COUNT(*) FROM edu_v2.users;

-- Verify no orphaned persons
SELECT COUNT(*) as orphaned_persons
FROM edu_v2.persons p
LEFT JOIN edu_v2.users u ON p.user_id = u.id
WHERE u.id IS NULL;
-- Expected: 0

-- Sample data check
SELECT 
    u.username,
    u.email,
    p.first_name,
    p.last_name
FROM edu_v2.users u
JOIN edu_v2.persons p ON u.id = p.user_id
LIMIT 10;
```

### Phase 2: Migrate Students & Staff

**Estimated Time:** 30 minutes  
**Data Volume:** ~6,800 records

```bash
# Run Phase 2 migration
python3 migrate_database.py --phase 2

# Expected output:
# ============================================================
# PHASE 2: MIGRATING STUDENTS
# ============================================================
# Found 6344 students to migrate
# ✓ Migrated 6344 students successfully
#
# MIGRATING STAFF (TEACHERS)...
# Found 424 teachers to migrate
# ✓ Migrated 424 staff members successfully
```

#### Validation

```sql
-- Check student counts
SELECT 'OLD' as db, COUNT(*) FROM edu.students
UNION ALL
SELECT 'NEW' as db, COUNT(*) FROM edu_v2.students;

-- Check staff counts
SELECT 'OLD' as db, COUNT(*) FROM edu.teachers
UNION ALL
SELECT 'NEW' as db, COUNT(*) FROM edu_v2.staff_members;

-- Verify student-user linkage
SELECT COUNT(*) as students_with_users
FROM edu_v2.students s
JOIN edu_v2.users u ON s.user_id = u.id;
-- Expected: 6344

-- Sample student data
SELECT 
    s.student_number,
    u.username,
    p.first_name || ' ' || p.last_name as full_name,
    s.status,
    s.gpa
FROM edu_v2.students s
JOIN edu_v2.users u ON s.user_id = u.id
JOIN edu_v2.persons p ON u.id = p.user_id
LIMIT 10;
```

### Phase 3: Migrate Organizations & Academic Structure

**Estimated Time:** 20 minutes  
**Data Volume:** ~450 records

```bash
# Run Phase 3 migration
python3 migrate_database.py --phase 3

# Expected output:
# ============================================================
# PHASE 3: MIGRATING ORGANIZATIONS
# ============================================================
# Found 419 organizations to migrate
# ✓ Migrated 419 organizations successfully
#
# CREATING ACADEMIC TERMS...
# ✓ Created 12 academic terms
```

#### Validation

```sql
-- Check organization counts
SELECT 'OLD' as db, COUNT(*) FROM edu.organizations
UNION ALL
SELECT 'NEW' as db, COUNT(*) FROM edu_v2.organization_units;

-- Verify organization hierarchy
SELECT 
    type,
    COUNT(*) as count
FROM edu_v2.organization_units
GROUP BY type
ORDER BY type;
-- Expected: university, faculty, department, program

-- Check academic terms
SELECT 
    academic_year,
    term_type,
    start_date,
    end_date,
    is_current
FROM edu_v2.academic_terms
ORDER BY start_date;
-- Expected: 12 terms (2020-2025, Fall & Spring)

-- Verify parent-child relationships
SELECT 
    parent.name->>'az' as parent_name,
    child.name->>'az' as child_name,
    child.type
FROM edu_v2.organization_units child
JOIN edu_v2.organization_units parent ON child.parent_id = parent.id
LIMIT 10;
```

### Phase 4: Migrate Courses & Offerings

**Estimated Time:** 40 minutes  
**Data Volume:** ~6,000 courses

```bash
# Run Phase 4 migration
python3 migrate_database.py --phase 4

# Expected output:
# ============================================================
# PHASE 4: MIGRATING COURSES
# ============================================================
# Found 1234 unique courses to migrate
# ✓ Migrated 1234 courses successfully
#
# Found 6020 course offerings to migrate
# ✓ Migrated 6020 course offerings successfully
```

#### Validation

```sql
-- Check course catalog
SELECT COUNT(*) as master_courses FROM edu_v2.courses;

-- Check course offerings
SELECT COUNT(*) as course_instances FROM edu_v2.course_offerings;

-- Verify course-term linkage
SELECT 
    at.academic_year,
    at.term_type,
    COUNT(co.id) as course_count
FROM edu_v2.academic_terms at
LEFT JOIN edu_v2.course_offerings co ON at.id = co.academic_term_id
GROUP BY at.academic_year, at.term_type
ORDER BY at.academic_year, at.term_type;

-- Sample course data
SELECT 
    c.code,
    c.name->>'az' as course_name,
    c.credit_hours,
    co.section_code,
    at.academic_year,
    at.term_type
FROM edu_v2.course_offerings co
JOIN edu_v2.courses c ON co.course_id = c.id
JOIN edu_v2.academic_terms at ON co.academic_term_id = at.id
LIMIT 10;
```

### Phase 5: Migrate Enrollments & Grades

**Estimated Time:** 60 minutes  
**Data Volume:** ~3.2 million grade records

```bash
# Run Phase 5 migration (this will take longest)
python3 migrate_database.py --phase 5

# Expected output:
# ============================================================
# PHASE 5: MIGRATING ENROLLMENTS & GRADES
# ============================================================
# Found 118,477 course enrollments to migrate
# ✓ Migrated 118,477 enrollments successfully
#
# Found 3,209,747 grades to migrate
# ✓ Migrated 3,209,747 grades successfully (this may take 30-45 min)
```

#### Validation

```sql
-- Check enrollment counts
SELECT COUNT(*) as enrollments FROM edu_v2.course_enrollments;

-- Check grade counts
SELECT COUNT(*) as grades FROM edu_v2.grades;

-- Verify enrollment-student linkage
SELECT 
    COUNT(DISTINCT ce.student_id) as students_with_enrollments
FROM edu_v2.course_enrollments ce;

-- Grade distribution
SELECT 
    grade,
    COUNT(*) as count
FROM edu_v2.course_enrollments
WHERE grade IS NOT NULL
GROUP BY grade
ORDER BY grade;

-- Sample enrollment data with grades
SELECT 
    s.student_number,
    c.code as course_code,
    c.name->>'az' as course_name,
    ce.grade,
    ce.enrollment_status
FROM edu_v2.course_enrollments ce
JOIN edu_v2.students s ON ce.student_id = s.id
JOIN edu_v2.course_offerings co ON ce.course_offering_id = co.id
JOIN edu_v2.courses c ON co.course_id = c.id
LIMIT 20;
```

### Phase 6: Comprehensive Validation

**Estimated Time:** 30 minutes

```bash
# Run automated validation
python3 migrate_database.py --validate

# Expected output:
# ============================================================
# VALIDATION RESULTS
# ============================================================
# ✓ PASS | User Count: Old=6987, New=6987
# ✓ PASS | Student Count: Old=6344, New=6344
# ✓ PASS | Staff Count: Old=424, New=424
# ✓ PASS | Organization Count: Old=419, New=419
# ✓ PASS | Course Offering Count: Old=6020, New=6020
# ✓ PASS | Enrollment Count: Old=118477, New=118477
# ✓ PASS | Grade Count: Old=3209747, New=3209747
# ✓ PASS | Orphaned Students: Old=0, New=0
# ✓ PASS | Orphaned Enrollments: Old=0, New=0
```

#### Manual Validation Queries

```sql
-- 1. Data completeness check
SELECT 
    'users' as entity, 
    (SELECT COUNT(*) FROM edu.users) as old_count,
    (SELECT COUNT(*) FROM edu_v2.users) as new_count
UNION ALL
SELECT 
    'students' as entity,
    (SELECT COUNT(*) FROM edu.students),
    (SELECT COUNT(*) FROM edu_v2.students)
UNION ALL
SELECT 
    'teachers' as entity,
    (SELECT COUNT(*) FROM edu.teachers),
    (SELECT COUNT(*) FROM edu_v2.staff_members);

-- 2. Referential integrity check
SELECT 
    'Students without users' as issue,
    COUNT(*) as count
FROM edu_v2.students s
LEFT JOIN edu_v2.users u ON s.user_id = u.id
WHERE u.id IS NULL

UNION ALL

SELECT 
    'Enrollments without students' as issue,
    COUNT(*) as count
FROM edu_v2.course_enrollments ce
LEFT JOIN edu_v2.students s ON ce.student_id = s.id
WHERE s.id IS NULL

UNION ALL

SELECT 
    'Enrollments without courses' as issue,
    COUNT(*) as count
FROM edu_v2.course_enrollments ce
LEFT JOIN edu_v2.course_offerings co ON ce.course_offering_id = co.id
WHERE co.id IS NULL;

-- All should return 0

-- 3. Sample data quality check
SELECT 
    u.username,
    u.email,
    p.first_name,
    p.last_name,
    s.student_number,
    COUNT(ce.id) as enrollment_count
FROM edu_v2.users u
JOIN edu_v2.persons p ON u.id = p.user_id
JOIN edu_v2.students s ON u.id = s.user_id
LEFT JOIN edu_v2.course_enrollments ce ON s.id = ce.student_id
GROUP BY u.username, u.email, p.first_name, p.last_name, s.student_number
LIMIT 10;
```

### Phase 7: Application Cutover

**Estimated Time:** 15 minutes

```bash
# 1. Update application database connection strings
# Edit backend configuration files

# FastAPI (.env file)
DATABASE_URL=postgresql://postgres:1111@localhost:5432/edu_v2

# Django (settings.py)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'edu_v2',
        'USER': 'postgres',
        'PASSWORD': '1111',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# 2. Restart application services
sudo systemctl start fastapi_service
sudo systemctl start django_service
sudo systemctl start nginx

# 3. Test critical endpoints
curl http://localhost:8000/api/v1/users/me
curl http://localhost:8000/api/v1/students/
curl http://localhost:8000/api/v1/courses/

# 4. Monitor logs
tail -f /var/log/fastapi/app.log
tail -f /var/log/django/app.log
```

---

## Validation Procedures

### Automated Validation Script

```bash
# Run complete validation suite
python3 migrate_database.py --validate
```

### Manual Validation Checklist

- [  ] User count matches (6,987)
- [  ] Student count matches (6,344)
- [  ] Staff count matches (424)
- [  ] Organization count matches (419)
- [  ] All foreign key constraints valid
- [  ] No orphaned records
- [  ] Sample data quality verified
- [  ] Application can connect to new database
- [  ] Critical API endpoints functional
- [  ] Authentication works
- [  ] Student dashboard loads
- [  ] Teacher dashboard loads
- [  ] Admin panel accessible

---

## Rollback Procedures

### If Migration Fails During Execution

```bash
# 1. Stop migration script (Ctrl+C)

# 2. Drop new database
psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS edu_v2;"

# 3. Recreate empty new database
psql -U postgres -h localhost -c "CREATE DATABASE edu_v2;"

# 4. Restore schema only
psql -U postgres -h localhost -d edu_v2 -f new_database_schema.sql

# 5. Fix issues and retry migration
```

### If Issues Discovered After Migration

```bash
# 1. Stop application services
sudo systemctl stop fastapi_service
sudo systemctl stop django_service

# 2. Switch back to old database
# Edit .env and settings.py to use 'edu' instead of 'edu_v2'

# 3. Restart services
sudo systemctl start fastapi_service
sudo systemctl start django_service

# 4. Analyze and fix migration issues

# 5. Re-run migration when ready
```

### Complete Rollback with Data Restore

```bash
# 1. Drop new database
psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS edu_v2;"

# 2. Restore from backup (if old database was modified)
pg_restore -U postgres -h localhost -d edu edu_backup_YYYYMMDD_HHMMSS.dump

# 3. Verify old database restored correctly
psql -U postgres -h localhost -d edu -c "SELECT COUNT(*) FROM users;"

# 4. Update application to use old database
# 5. Restart services
```

---

## Post-Migration Tasks

### Immediate (Day 1)

1. **Monitor Application Performance**
   ```bash
   # Check database connection pool
   psql -U postgres -h localhost -d edu_v2 -c "SELECT * FROM pg_stat_activity;"
   
   # Monitor slow queries
   psql -U postgres -h localhost -d edu_v2 -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
   ```

2. **Verify Backups Working**
   ```bash
   # Set up automated backup cron job
   0 2 * * * pg_dump -U postgres -h localhost -Fc edu_v2 > /backups/edu_v2_$(date +\%Y\%m\%d).dump
   ```

3. **Update Documentation**
   - Mark old database as deprecated
   - Update developer onboarding docs
   - Update API documentation

### Short-term (Week 1)

1. **Add Indexes for Performance**
   ```sql
   -- Analyze query patterns
   SELECT * FROM pg_stat_user_tables WHERE schemaname = 'public';
   
   -- Add missing indexes as needed
   CREATE INDEX CONCURRENTLY idx_custom_1 ON table_name(column_name);
   ```

2. **Implement Row-Level Security**
   ```sql
   -- Enable RLS on sensitive tables
   ALTER TABLE students ENABLE ROW LEVEL SECURITY;
   
   -- Create policies
   CREATE POLICY student_own_data ON students
       FOR SELECT
       USING (user_id = current_user_id());
   ```

3. **Set Up Monitoring**
   - Configure pgBadger for query analysis
   - Set up Grafana dashboards
   - Configure alerts for database issues

### Long-term (Month 1)

1. **Decommission Old Database**
   ```bash
   # After 30 days of successful operation
   # Final backup of old database
   pg_dump -U postgres -h localhost -Fc edu > edu_final_backup.dump
   
   # Archive old database
   mv edu_final_backup.dump /archive/
   
   # Drop old database
   psql -U postgres -h localhost -c "DROP DATABASE edu;"
   ```

2. **Optimize Database Configuration**
   ```ini
   # PostgreSQL configuration tuning
   shared_buffers = 4GB
   effective_cache_size = 12GB
   maintenance_work_mem = 1GB
   checkpoint_completion_target = 0.9
   wal_buffers = 16MB
   default_statistics_target = 100
   random_page_cost = 1.1
   effective_io_concurrency = 200
   work_mem = 10MB
   min_wal_size = 2GB
   max_wal_size = 8GB
   ```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Connection refused" error

**Symptom:** Cannot connect to database

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Start if stopped
sudo systemctl start postgresql

# Check port listening
sudo netstat -tulpn | grep 5432
```

#### Issue 2: "Out of memory" during migration

**Symptom:** Python script crashes with memory error

**Solution:**
```bash
# Increase swap space
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Or migrate in smaller batches
python3 migrate_database.py --phase 5 --batch-size 10000
```

#### Issue 3: "Duplicate key violation"

**Symptom:** Migration fails with unique constraint error

**Solution:**
```sql
-- Check for duplicates in old database
SELECT username, COUNT(*) 
FROM edu.users 
GROUP BY username 
HAVING COUNT(*) > 1;

-- Clean up duplicates before migration
-- Then re-run migration
```

#### Issue 4: Foreign key constraint violations

**Symptom:** Cannot insert due to FK constraint

**Solution:**
```sql
-- Temporarily disable FK checks (NOT RECOMMENDED for production)
SET session_replication_role = 'replica';
-- Run migration
SET session_replication_role = 'origin';

-- Better: Fix data first
SELECT * FROM edu.students WHERE person_id NOT IN (SELECT id FROM edu.persons);
```

### Getting Help

**Before reaching out:**
1. Check migration logs: `tail -f migration_*.log`
2. Check PostgreSQL logs: `tail -f /var/log/postgresql/postgresql-15-main.log`
3. Review validation output
4. Document exact error message and stack trace

**Support Channels:**
- Database Team: db-team@bbu.edu.az
- Migration Lead: migration@bbu.edu.az
- Emergency Hotline: +994-XX-XXX-XXXX

---

## Success Criteria

Migration is considered successful when:

- [  ] All data counts match between old and new database
- [  ] No orphaned records exist
- [  ] All foreign key constraints valid
- [  ] Application connects successfully
- [  ] User authentication works
- [  ] Students can view their courses and grades
- [  ] Teachers can view their courses and students
- [  ] Administrators can access all functionality
- [  ] No performance degradation
- [  ] Backups configured and tested

---

**Document Version:** 1.0  
**Last Updated:** October 3, 2025  
**Next Review:** After successful migration

**Migration Team:**
- Database Administrator
- Backend Developers
- QA Team
- DevOps Engineer

**Approval:**
- Technical Lead: _________________ Date: _______
- Project Manager: ________________ Date: _______
- CTO: ___________________________ Date: _______
