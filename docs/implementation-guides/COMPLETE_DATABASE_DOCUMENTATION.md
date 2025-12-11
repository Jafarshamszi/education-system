# COMPREHENSIVE DATABASE DOCUMENTATION
## New LMS Database vs Old EDU Database

**Date:** October 10, 2025  
**New Database:** `lms` (PostgreSQL)  
**Old Database:** `edu` (PostgreSQL)  

---

## EXECUTIVE SUMMARY

The education system has been migrated from the old `edu` database (356 tables) to a new, modern `lms` database (55 tables). This document explains the complete structure, differences, role system, and how everything works together.

### Key Statistics

| Metric | Old Database (edu) | New Database (lms) |
|--------|-------------------|-------------------|
| **Total Tables** | 356 tables | 55 tables |
| **Total Users** | 6,525 accounts | 6,492 users |
| **Active Students** | 6,105 students | 5,959 students |
| **Active Staff** | 382 teachers | 190 staff members |
| **Role System** | No formal roles | 11 hierarchical roles |
| **Permissions** | URL-based (all_privilege) | 35 resource-action-scope permissions |
| **Audit System** | action_logs (basic) | Comprehensive audit_logs with triggers |

---

## TABLE OF CONTENTS

1. [Database Architecture Comparison](#1-database-architecture-comparison)
2. [Complete Table Listing](#2-complete-table-listing)
3. [Entity Relationships](#3-entity-relationships)
4. [Role & Permission System](#4-role--permission-system)
5. [Security Features](#5-security-features)
6. [Migration Summary](#6-migration-summary)
7. [What Changed](#7-what-changed)
8. [What Stayed the Same](#8-what-stayed-the-same)
9. [What Was Removed](#9-what-was-removed)
10. [How to Use the New Database](#10-how-to-use-the-new-database)

---

## 1. DATABASE ARCHITECTURE COMPARISON

### Old Database (edu) - 356 Tables

**Structure:** Monolithic, accumulated over years with many legacy tables

**Characteristics:**
- Mixed naming conventions (a_*, archive_*, bak*)
- Many backup/archive tables (a_students_bak, a_students_bak2, a_students_bak2022, etc.)
- Duplicate functionality (a_teachers, a_teachers2, excel_teacher, teachers)
- No formal relationship enforcement
- Minimal constraints
- BigInt IDs (sequential)

**Main Tables:**
- `accounts` - User authentication (6,525 users)
- `persons` - Personal information
- `students` - Student records (6,105 students)
- `teachers` - Staff records (382 teachers)
- `course`, `course_*` - Course-related (70+ tables)
- `all_privilege`, `all_privilege2` - Basic permission system

### New Database (lms) - 55 Tables

**Structure:** Modern, normalized, well-designed schema

**Characteristics:**
- Consistent naming conventions (snake_case)
- UUID primary keys (better for distributed systems)
- Comprehensive foreign key constraints
- Check constraints for data integrity
- JSONB for flexible multilingual data
- Indexed for performance
- Row-Level Security (RLS) policies

**Main Table Categories:**
1. **Core Identity** (5 tables): users, persons, students, staff_members, user_sessions
2. **Organization** (3 tables): organization_units, organization_unit_hierarchy, program_departments
3. **Academic Programs** (8 tables): academic_programs, degree_requirements, courses, course_prerequisites, etc.
4. **Enrollment & Scheduling** (10 tables): course_offerings, course_enrollments, class_schedules, etc.
5. **Assessment & Grading** (8 tables): assessments, grades, enrollment_grades, grade_appeals, etc.
6. **Security & Audit** (8 tables): roles, permissions, user_roles, role_permissions, audit_logs, etc.
7. **Student Services** (8 tables): student_holds, graduation_applications, academic_honors, etc.
8. **Miscellaneous** (5 tables): announcements, notifications, file_uploads, calendar_events, page_views

---

## 2. COMPLETE TABLE LISTING

### New Database (lms) - All 55 Tables

#### Core Identity & Authentication (5 tables)
1. **users** - User accounts (username, email, password, MFA)
2. **persons** - Personal information (names, contact, demographics)
3. **students** - Student-specific data (enrollment status, advisor, GPA)
4. **staff_members** - Staff/faculty data (position, rank, department)
5. **user_sessions** - Active user sessions

#### Organization Structure (3 tables)
6. **organization_units** - Departments, faculties, programs, university
7. **organization_unit_hierarchy** - Hierarchical relationships
8. **program_departments** - Program-department mappings

#### Academic Programs & Courses (8 tables)
9. **academic_programs** - Degree programs (Bachelor, Master, PhD)
10. **degree_requirements** - Program requirements
11. **courses** - Course catalog
12. **course_prerequisites** - Course dependencies
13. **course_equivalencies** - Transfer credit mapping
14. **course_offerings** - Semester course instances
15. **course_instructors** - Teaching assignments
16. **course_materials** - Syllabus, readings, resources

#### Enrollment & Scheduling (10 tables)
17. **course_enrollments** - Student course registrations
18. **enrollment_grades** - Individual assignment grades
19. **class_schedules** - Timetable/calendar
20. **academic_terms** - Semesters, academic years
21. **academic_calendars** - Important dates
22. **schedule_conflicts** - Conflict detection
23. **student_groups** - Class groups, sections
24. **student_group_members** - Group membership
25. **course_waitlist** - Waitlist for full courses
26. **degree_audit_progress** - Degree completion tracking

#### Assessment & Grading (8 tables)
27. **assessments** - Exams, assignments, projects
28. **grades** - Final course grades
29. **grade_change_history** - Audit trail for grade changes
30. **grade_appeals** - Student grade disputes
31. **gpa_calculations** - GPA history
32. **grading_scales** - Grade point mappings
33. **attendance_records** - Class attendance
34. **academic_standing_history** - Probation, dean's list, etc.

#### Security, Roles & Permissions (8 tables)
35. **roles** - System roles (SUPER_ADMIN, ADMIN, RECTOR, DEAN, TEACHER, STUDENT, etc.)
36. **permissions** - Granular permissions (resource.action.scope)
37. **role_permissions** - Role-permission mappings
38. **user_roles** - User-role assignments
39. **audit_logs** - Comprehensive activity logging
40. **user_preferences** - User settings
41. **notifications** - System notifications
42. **page_views** - Analytics

#### Student Services (8 tables)
43. **student_holds** - Registration/transcript holds
44. **student_transcripts** - Official transcripts
45. **transcript_requests** - Transcript requests
46. **graduation_applications** - Graduation petitions
47. **academic_honors** - Awards, honors, scholarships
48. **transfer_credits** - Transfer credit evaluation

#### Miscellaneous (5 tables)
49. **announcements** - System announcements
50. **calendar_events** - Events, deadlines
51. **file_uploads** - Document storage metadata
52. **academic_schedule** - Master schedule template
53. **academic_schedule_details** - Schedule details

#### Materialized Views (3)
54. **mv_student_statistics** - Aggregated student stats
55. **mv_course_offering_statistics** - Course enrollment stats
56. **mv_faculty_workload** - Faculty teaching load

---

## 3. ENTITY RELATIONSHIPS

### Core Relationship Map

```
users (authentication root)
  ├─> persons (1:1) - Personal info
  ├─> students (1:1) - Student data
  │     ├─> course_enrollments (1:N) - Registered courses
  │     │     ├─> grades (1:N) - Course grades
  │     │     ├─> enrollment_grades (1:N) - Assignment grades
  │     │     └─> attendance_records (1:N) - Attendance
  │     ├─> student_holds (1:N) - Active holds
  │     ├─> gpa_calculations (1:N) - GPA history
  │     └─> graduation_applications (1:N) - Graduation requests
  │
  ├─> staff_members (1:1) - Faculty/staff data
  │     ├─> course_instructors (1:N) - Teaching assignments
  │     │     └─> course_offerings (N:1) - Courses taught
  │     └─> organization_units (N:1) - Department assignment
  │
  └─> user_roles (1:N) - Role assignments
        └─> roles (N:1) - System roles
              └─> role_permissions (1:N) - Permissions
                    └─> permissions (N:1) - Resources

organization_units (departments, programs)
  ├─> organization_unit_hierarchy (self-referencing tree)
  ├─> academic_programs (1:N) - Programs in unit
  ├─> staff_members (1:N) - Staff in unit
  └─> student_groups (1:N) - Classes in unit

academic_programs (degree programs)
  ├─> students (1:N) - Enrolled students
  ├─> degree_requirements (1:N) - Required courses
  └─> course_offerings (1:N) - Program courses

courses (course catalog)
  ├─> course_prerequisites (1:N) - Required prerequisites
  ├─> course_equivalencies (1:N) - Transfer equivalents
  └─> course_offerings (1:N) - Semester instances
        ├─> course_instructors (1:N) - Instructors
        ├─> course_enrollments (1:N) - Enrolled students
        ├─> class_schedules (1:N) - Meeting times
        └─> course_materials (1:N) - Resources
```

### Foreign Key Constraints (150+ total)

Every relationship is enforced by foreign keys with appropriate cascade rules:
- `ON DELETE CASCADE` - Deleting parent deletes children (e.g., user → user_roles)
- `ON DELETE SET NULL` - Deleting parent nullifies reference (e.g., graded_by → users)
- `ON DELETE RESTRICT` - Prevent deletion if children exist (e.g., role → role_permissions)

---

## 4. ROLE & PERMISSION SYSTEM

### Role Hierarchy (11 Roles)

| Level | Code | Name | Description | Users | Permissions |
|-------|------|------|-------------|-------|-------------|
| **-1** | **SUPER_ADMIN** | Super Administrator | Highest system privileges | 0 | 33 (all) |
| **0** | **ADMIN** | Administrator | System administration | 1 | 33 (all) |
| 1 | **RECTOR** | Rector | University rector | 1 | 33 (all) |
| 2 | VICE_RECTOR | Vice Rector | Deputy rector | 0 | 0 |
| 3 | DEAN | Dean | Faculty dean | 1 | 33 (most) |
| 3 | HEAD_OF_DEPT | Head of Department | Department lead | 0 | 0 |
| 4 | VICE_DEAN | Vice Dean | Deputy dean | 0 | 0 |
| 5 | DEPT_HEAD | Department Head | Department manager | 0 | 0 |
| 6 | **TEACHER** | Teacher | Faculty member | 190 | 9 |
| 6 | ADVISOR | Academic Advisor | Student advisor | 0 | 0 |
| **7** | **STUDENT** | Student | Enrolled student | 5,959 | 5 |

**Current Assignments:**
- **RECTOR:** İbad Abbasov (18JKDR3)
- **DEAN:** Şahin Musayev (1BJ7R3G)
- **ADMIN:** admin user
- **TEACHER:** 190 active staff (+ 160 expired for inactive staff)
- **STUDENT:** 5,959 active students

### Permission System (35 Permissions)

Format: `resource.action.scope`

#### Student Permissions (5)
1. `attendance.read.own` - View own attendance
2. `courses.read.university` - Browse courses
3. `enrollments.create.own` - Register for courses
4. `enrollments.read.own` - View registrations
5. `grades.read.own` - View own grades

#### Teacher Permissions (9)
1. `students.read.department` - View department students
2. `enrollments.read.department` - View department enrollments
3. `attendance.create.department` - Mark attendance
4. `grades.create.department` - Assign grades
5. `grades.read.department` - View grades
6. `grades.update.department` - Modify grades
7. `grades.approve.department` - Approve final grades
8. `assessments.create.department` - Create assessments
9. `courses.read.university` - Browse all courses

#### Administrator Permissions (33)
All permissions across all resources with `system` or `university` scope.

### Permission Scopes

- **own** - User's own data only
- **department** - Department/unit level access
- **faculty** - Faculty-wide access
- **university** - University-wide access
- **system** - Full system access

### Role Assignment Rules

**WHO CAN ASSIGN WHAT:**

1. **SUPER_ADMIN** can assign:
   - Any role including ADMIN
   - Unrestricted system access

2. **ADMIN** can assign:
   - RECTOR, DEAN, VICE_RECTOR, HEAD_OF_DEPT, DEPT_HEAD, VICE_DEAN
   - TEACHER, ADVISOR, STUDENT
   - **CANNOT assign:** SUPER_ADMIN or ADMIN (security restriction)

3. **RECTOR** can assign:
   - DEAN, VICE_DEAN, DEPT_HEAD, TEACHER, STUDENT

4. **DEAN** can assign:
   - VICE_DEAN, DEPT_HEAD, TEACHER, STUDENT (within faculty)

5. **Others:** Cannot assign roles

---

## 5. SECURITY FEATURES

### Row-Level Security (RLS) - 4 Policies

1. **students_own_data**
   - Students can only SELECT their own student record
   - Enforces privacy between students

2. **grades_student_access**
   - Students can only view their own grades
   - Prevents grade snooping

3. **grades_instructor_access**
   - Teachers can view/modify grades for courses they teach
   - Department-scoped access

4. **enrollments_student_access**
   - Students can only view their own course enrollments
   - Prevents enrollment data leakage

### Audit Logging (30 Triggers on 10 Tables)

**Tables with Audit Triggers:**
1. users - Account changes
2. students - Student data modifications
3. staff_members - Staff data changes
4. grades - Grade creation/modification/deletion
5. attendance_records - Attendance marking
6. course_enrollments - Enrollment changes
7. user_roles - Role assignments
8. role_permissions - Permission changes
9. academic_programs - Program modifications
10. courses - Course catalog changes

**What Gets Logged:**
- Action type (INSERT, UPDATE, DELETE)
- User who performed action (from session context)
- Resource type (table name)
- Resource ID (record UUID if exists)
- Old values (JSONB - before change)
- New values (JSONB - after change)
- IP address (from session)
- Session ID
- Timestamp

**Audit Functions:**
- `log_data_change()` - Automatic trigger function
- `log_user_login(user_id, ip, user_agent, session_id)` - Manual login tracking
- `log_user_logout(user_id, session_id, duration)` - Manual logout tracking

### Data Integrity Constraints

**Check Constraints (50+):**
- Email format validation
- Username minimum length (3 chars)
- Date range validations (e.g., contract_end > hire_date)
- Enum validations (employment_type, academic_rank, etc.)
- JSONB required keys (e.g., position_title must have 'az')

**Unique Constraints (30+):**
- users.username, users.email
- students.student_id
- staff_members.employee_number
- Composite uniques for preventing duplicates

**Foreign Keys (150+):**
- All relationships enforced
- Cascade rules prevent orphaned records
- ON DELETE policies preserve data integrity

---

## 6. MIGRATION SUMMARY

### What Was Migrated

**Successfully Migrated:**
- ✅ 6,492 user accounts (from 6,525)
- ✅ 5,959 students (from 6,105)
- ✅ 190 active staff (from 382 active teachers)
- ✅ Personal information (names, contacts)
- ✅ Academic programs
- ✅ Course catalog
- ✅ Organization structure (60 units, 13 departments)

**Not Migrated (Old Database Only):**
- ❌ Historical backup tables (a_students_bak*, etc.)
- ❌ Legacy competition system (competition_*)
- ❌ Old conference system (confrance_*)
- ❌ Conversation/messaging (conversation_*)
- ❌ Archive tables (archive_*, *_archive)
- ❌ Incomplete/test data

### Migration Statistics

| Metric | Result |
|--------|--------|
| **Users Migrated** | 99.5% (6,492/6,525) |
| **Students Migrated** | 97.6% (5,959/6,105) |
| **Active Staff** | 49.7% (190/382) |
| **Tables Reduced** | 84.5% (from 356 to 55) |
| **Data Normalized** | 100% |
| **Relationships Enforced** | 100% |

**Why fewer staff?**
- Old database had 382 "active" teachers
- Many were duplicates or historical records
- New database has 190 truly active + 160 inactive (properly tracked)
- Total staff records: 350 (closer to old 382)

---

## 7. WHAT CHANGED

### Major Improvements

**1. Data Model:**
- UUID instead of BigInt IDs
- JSONB for multilingual content
- Normalized structure (no redundancy)
- Comprehensive constraints

**2. Security:**
- Role-based access control (11 roles)
- Granular permissions (35)
- Row-level security (4 policies)
- Comprehensive audit logging

**3. Organization:**
- Formal role hierarchy
- Department assignments for all teachers (100%)
- Clear organizational structure

**4. Performance:**
- Proper indexing (100+ indexes)
- Materialized views for statistics
- Optimized foreign keys

**5. Maintainability:**
- Consistent naming
- Self-documenting structure
- No legacy/backup tables
- Modern PostgreSQL features

### Breaking Changes

**⚠️ IMPORTANT - NOT BACKWARD COMPATIBLE:**

1. **Primary Keys:**
   - Old: `bigint` IDs (e.g., `220209055404181687`)
   - New: `uuid` IDs (e.g., `529a5428-ac22-41e4-a35a-12733bec563d`)
   - **Impact:** All foreign key references need UUID conversion

2. **Table Names:**
   - Old: `accounts`, `teachers`, `students`
   - New: `users`, `staff_members`, `students`
   - **Impact:** All queries need table name updates

3. **Column Names:**
   - Old: `person_id`, `firstname`, `lastname`
   - New: `user_id`, `first_name`, `last_name`
   - **Impact:** All column references need updates

4. **Authentication:**
   - Old: `accounts.username`, `accounts.password`
   - New: `users.username`, `users.password_hash`
   - **Impact:** Auth logic needs rewrite

5. **Permissions:**
   - Old: URL-based (`all_privilege.url`)
   - New: Resource-action-scope (`permissions.resource`, `action`, `scope`)
   - **Impact:** Permission checks need complete rewrite

---

## 8. WHAT STAYED THE SAME

### Preserved Concepts

1. **Core Entities:**
   - Users/accounts still exist
   - Students still have student records
   - Teachers/staff still tracked
   - Courses and enrollments preserved

2. **Business Logic:**
   - Student enrollment process
   - Grade assignment workflow
   - Course scheduling
   - Academic calendar

3. **Data Values:**
   - Usernames preserved (e.g., `18JKDR3`, `1BJ7R3G`)
   - Names and personal info intact
   - Historical data preserved where relevant

4. **Organization:**
   - Departments still exist (60 units)
   - Programs still defined
   - Hierarchy maintained

---

## 9. WHAT WAS REMOVED

### Removed from Old Database

**Tables Not Migrated (301 tables removed):**

1. **Backup/Archive Tables (50+):**
   - a_students_bak, a_students_bak2, a_students_bak2022, etc.
   - action_logs_archive
   - common_action_log_archive
   - archive_students

2. **Legacy Systems (100+):**
   - competition_* (15 tables) - Old competition system
   - confrance_* (12 tables) - Old conference system
   - conversation_* (6 tables) - Old messaging
   - listener_* (20+ tables) - Non-credit students (deprecated)
   - other_course_* - Miscellaneous old features

3. **Duplicate/Test Tables:**
   - a_teachers, a_teachers2, excel_teacher (kept one: teachers → staff_members)
   - all_privilege, all_privilege2 (replaced with permissions)

4. **Temporary/Work Tables:**
   - a_sub_correction
   - a_naa_exam_integration
   - Various *_temp tables

**Why Removed?**
- Not used in current system
- Superseded by new functionality
- Data quality issues
- No business value

---

## 10. HOW TO USE THE NEW DATABASE

### For Backend Developers

**Connection String:**
```python
DATABASE_URL = "postgresql://postgres:1111@localhost:5432/lms"
```

**Essential Queries:**

```sql
-- Get user with roles
SELECT 
    u.id, u.username, u.email,
    array_agg(r.code) as roles
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id 
    AND (ur.valid_until IS NULL OR ur.valid_until > CURRENT_TIMESTAMP)
LEFT JOIN roles r ON ur.role_id = r.id
WHERE u.username = '18JKDR3'
GROUP BY u.id;

-- Check user permission
SELECT EXISTS (
    SELECT 1 
    FROM user_roles ur
    JOIN role_permissions rp ON ur.role_id = rp.role_id
    JOIN permissions p ON rp.permission_id = p.id
    WHERE ur.user_id = 'user-uuid-here'
    AND p.resource = 'students'
    AND p.action = 'read'
    AND p.scope IN ('department', 'university')
) as has_permission;

-- Get student with program
SELECT 
    s.student_id,
    p.first_name || ' ' || p.last_name as full_name,
    ap.name->>'en' as program,
    s.enrollment_status,
    s.cumulative_gpa
FROM students s
JOIN persons p ON s.user_id = p.user_id
JOIN academic_programs ap ON s.program_id = ap.id
WHERE s.student_id = 'STU123456';

-- Get teacher courses
SELECT 
    c.code || ' - ' || c.name->>'en' as course,
    co.academic_term_id,
    COUNT(ce.id) as enrolled_students
FROM course_instructors ci
JOIN course_offerings co ON ci.course_offering_id = co.id
JOIN courses c ON co.course_id = c.id
LEFT JOIN course_enrollments ce ON co.id = ce.course_offering_id
WHERE ci.instructor_id = 'teacher-user-uuid'
GROUP BY c.code, c.name, co.id, co.academic_term_id;
```

### For Frontend Developers

**API Endpoint Changes:**

Old:
```
GET /api/account/login
GET /api/student/info
GET /api/teacher/courses
```

New:
```
POST /api/v1/auth/login
GET /api/v1/students/me
GET /api/v1/staff/courses
```

**Role-Based UI:**

```javascript
// Check if user has role
const hasRole = (user, roleCode) => {
    return user.roles.includes(roleCode);
};

// Check permission
const hasPermission = (user, resource, action, scope) => {
    return user.permissions.some(p => 
        p.resource === resource && 
        p.action === action && 
        (p.scope === scope || p.scope === 'system')
    );
};

// Example usage
if (hasRole(user, 'TEACHER')) {
    showTeacherDashboard();
} else if (hasRole(user, 'STUDENT')) {
    showStudentDashboard();
}

if (hasPermission(user, 'students', 'read', 'department')) {
    showStudentList();
}
```

### For Database Administrators

**Daily Maintenance:**

```sql
-- Analyze query performance
ANALYZE;

-- Refresh materialized views (weekly)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_student_statistics;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_course_offering_statistics;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_faculty_workload;

-- Check audit log growth
SELECT 
    COUNT(*) as total_logs,
    COUNT(*) FILTER (WHERE created_at > CURRENT_DATE - INTERVAL '7 days') as last_week,
    pg_size_pretty(pg_total_relation_size('audit_logs')) as table_size
FROM audit_logs;

-- Archive old audit logs (monthly)
DELETE FROM audit_logs 
WHERE created_at < CURRENT_DATE - INTERVAL '1 year';

-- Vacuum large tables (weekly)
VACUUM ANALYZE audit_logs;
VACUUM ANALYZE course_enrollments;
VACUUM ANALYZE grades;
```

**Backup Strategy:**

```bash
# Daily backup
pg_dump -U postgres lms > lms_backup_$(date +%Y%m%d).sql

# Backup with compression
pg_dump -U postgres -Fc lms > lms_backup_$(date +%Y%m%d).dump

# Restore
pg_restore -U postgres -d lms lms_backup_20251010.dump
```

---

## CONCLUSION

The new `lms` database represents a complete modernization of the education system's data layer:

**Benefits:**
- ✅ 84% reduction in tables (356 → 55)
- ✅ Modern role-based security
- ✅ Comprehensive audit logging
- ✅ Data integrity enforcement
- ✅ Better performance
- ✅ Easier maintenance

**Next Steps:**
1. Update all backend code to use new database
2. Update all frontend API calls
3. Test thoroughly
4. Deploy to production
5. Decommission old `edu` database

**Support:**
- Documentation: This file
- Schema diagrams: See ER diagrams
- Role matrix: See role hierarchy section
- Migration scripts: See `backend/*.sql` files

---

**Document Version:** 1.0  
**Last Updated:** October 10, 2025  
**Maintained By:** Development Team
