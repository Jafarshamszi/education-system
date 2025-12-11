#!/bin/bash
#
# Database Migration Test Script
# ==============================
# This script creates a test database and runs the full migration
# to validate everything works before production execution
#

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Education System - Migration Test Script                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Database credentials
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"
OLD_DB="edu"
TEST_DB="edu_test"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Creating Test Database"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Drop test database if exists
echo -e "${YELLOW}→ Dropping existing test database (if any)...${NC}"
psql -U $DB_USER -h $DB_HOST -c "DROP DATABASE IF EXISTS $TEST_DB;" 2>/dev/null || true

# Create test database
echo -e "${GREEN}→ Creating test database: $TEST_DB${NC}"
psql -U $DB_USER -h $DB_HOST -c "CREATE DATABASE $TEST_DB;"

# Deploy schema to test database
echo -e "${GREEN}→ Deploying schema to test database...${NC}"
psql -U $DB_USER -h $DB_HOST -d $TEST_DB -f new_database_schema.sql

echo -e "${GREEN}✓ Test database created and schema deployed${NC}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Running Migration - Phase 1 (Users & Persons)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Update migration script to use test database
cat > temp_migrate_config.py << EOF
OLD_DB_CONFIG = {
    'host': '$DB_HOST',
    'port': $DB_PORT,
    'database': '$OLD_DB',
    'user': '$DB_USER',
    'password': '1111'
}

NEW_DB_CONFIG = {
    'host': '$DB_HOST',
    'port': $DB_PORT,
    'database': '$TEST_DB',
    'user': '$DB_USER',
    'password': '1111'
}
EOF

# Backup original config
cp migrate_database.py migrate_database_backup.py

# Replace config in migration script temporarily
sed -i "s/database': 'lms'/database': '$TEST_DB'/g" migrate_database.py

echo -e "${GREEN}→ Migrating users and persons...${NC}"
python3 migrate_database.py --phase 1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Running Migration - Phase 2 (Students & Staff)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${GREEN}→ Migrating students and staff...${NC}"
python3 migrate_database.py --phase 2

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: Running Migration - Phase 3 (Organizations & Terms)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${GREEN}→ Migrating organizations and academic terms...${NC}"
python3 migrate_database.py --phase 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 5: Running Migration - Phase 4 (Courses & Offerings)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${GREEN}→ Migrating courses, offerings, and instructors...${NC}"
python3 migrate_database.py --phase 4

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 6: Running Migration - Phase 5 (Enrollments & Grades)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${YELLOW}⚠  This may take 60-90 minutes (3.2M grade records)${NC}"
echo -e "${GREEN}→ Migrating enrollments, assessments, and grades...${NC}"
python3 migrate_database.py --phase 5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 7: Running Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${GREEN}→ Validating migration...${NC}"
python3 migrate_database.py --validate

# Restore original migration script
mv migrate_database_backup.py migrate_database.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 8: Manual Validation Queries"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${GREEN}→ Running detailed validation queries...${NC}"
echo ""

# Row count comparison
echo "📊 ROW COUNT COMPARISON:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
psql -U $DB_USER -h $DB_HOST -d $TEST_DB -c "
SELECT 
    'users' as table_name,
    (SELECT COUNT(*) FROM $OLD_DB.users) as old_count,
    (SELECT COUNT(*) FROM $TEST_DB.users) as new_count,
    CASE WHEN (SELECT COUNT(*) FROM $OLD_DB.users) = (SELECT COUNT(*) FROM $TEST_DB.users) 
        THEN '✓' ELSE '✗' END as match

UNION ALL

SELECT 
    'students',
    (SELECT COUNT(*) FROM $OLD_DB.students),
    (SELECT COUNT(*) FROM $TEST_DB.students),
    CASE WHEN (SELECT COUNT(*) FROM $OLD_DB.students) = (SELECT COUNT(*) FROM $TEST_DB.students)
        THEN '✓' ELSE '✗' END

UNION ALL

SELECT 
    'courses (catalog)',
    (SELECT COUNT(*) FROM $OLD_DB.subject_catalog WHERE active = 1),
    (SELECT COUNT(*) FROM $TEST_DB.courses),
    CASE WHEN (SELECT COUNT(*) FROM $OLD_DB.subject_catalog WHERE active = 1) <= (SELECT COUNT(*) FROM $TEST_DB.courses)
        THEN '✓' ELSE '✗' END

UNION ALL

SELECT 
    'course_offerings',
    (SELECT COUNT(*) FROM $OLD_DB.course WHERE active IN (0,1)),
    (SELECT COUNT(*) FROM $TEST_DB.course_offerings),
    CASE WHEN (SELECT COUNT(*) FROM $OLD_DB.course WHERE active IN (0,1)) <= (SELECT COUNT(*) FROM $TEST_DB.course_offerings)
        THEN '✓' ELSE '✗' END

UNION ALL

SELECT 
    'enrollments',
    (SELECT COUNT(*) FROM $OLD_DB.course_student WHERE active = 1),
    (SELECT COUNT(*) FROM $TEST_DB.course_enrollments),
    CASE WHEN (SELECT COUNT(*) FROM $OLD_DB.course_student WHERE active = 1) <= (SELECT COUNT(*) FROM $TEST_DB.course_enrollments)
        THEN '✓' ELSE '✗' END

UNION ALL

SELECT 
    'grades',
    (SELECT COUNT(*) FROM $OLD_DB.journal_details WHERE active = 1),
    (SELECT COUNT(*) FROM $TEST_DB.grades),
    CASE WHEN (SELECT COUNT(*) FROM $OLD_DB.journal_details WHERE active = 1) <= (SELECT COUNT(*) FROM $TEST_DB.grades)
        THEN '✓' ELSE '✗' END;
"

echo ""
echo "🔗 REFERENTIAL INTEGRITY CHECK:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
psql -U $DB_USER -h $DB_HOST -d $TEST_DB -c "
SELECT 'students → users' as check_name, COUNT(*) as orphaned_records
FROM students s LEFT JOIN users u ON s.user_id = u.id WHERE u.id IS NULL

UNION ALL

SELECT 'staff_members → users', COUNT(*)
FROM staff_members sm LEFT JOIN users u ON sm.user_id = u.id WHERE u.id IS NULL

UNION ALL

SELECT 'course_offerings → courses', COUNT(*)
FROM course_offerings co LEFT JOIN courses c ON co.course_id = c.id WHERE c.id IS NULL

UNION ALL

SELECT 'course_enrollments → offerings', COUNT(*)
FROM course_enrollments ce LEFT JOIN course_offerings co ON ce.course_offering_id = co.id WHERE co.id IS NULL

UNION ALL

SELECT 'grades → assessments', COUNT(*)
FROM grades g LEFT JOIN assessments a ON g.assessment_id = a.id WHERE a.id IS NULL

UNION ALL

SELECT 'grades → students', COUNT(*)
FROM grades g LEFT JOIN students s ON g.student_id = s.id WHERE s.id IS NULL;
"

echo ""
echo "📈 SAMPLE DATA QUALITY CHECK:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
psql -U $DB_USER -h $DB_HOST -d $TEST_DB -c "
-- Check multilingual course names
SELECT 'Multilingual course names' as check_type, COUNT(*) as count
FROM courses WHERE (name->>'az') IS NOT NULL;
" -t

psql -U $DB_USER -h $DB_HOST -d $TEST_DB -c "
-- Check UUID format
SELECT 'Valid UUIDs' as check_type, COUNT(*) as count
FROM users WHERE id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
" -t

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              MIGRATION TEST COMPLETED                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✓ Test database migration successful!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review migration logs in: migration_*.log"
echo "  2. Inspect test database: psql -U $DB_USER -d $TEST_DB"
echo "  3. If all looks good, run production migration:"
echo "     - Create backup: pg_dump -U postgres -Fc edu > edu_backup.dump"
echo "     - Create lms: createdb -U postgres lms"
echo "     - Deploy schema: psql -U postgres -d lms -f new_database_schema.sql"
echo "     - Run migration: python3 migrate_database.py --phase all"
echo "     - Validate: python3 migrate_database.py --validate"
echo ""
echo "  4. To clean up test database:"
echo "     dropdb -U $DB_USER $TEST_DB"
echo ""
