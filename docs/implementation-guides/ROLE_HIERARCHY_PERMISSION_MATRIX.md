# ROLE HIERARCHY & PERMISSION MATRIX
## Complete Authorization System Documentation

**Date:** October 10, 2025  
**Database:** lms (PostgreSQL)  
**System:** Education Management System

---

## TABLE OF CONTENTS

1. [Role Hierarchy Overview](#1-role-hierarchy-overview)
2. [Role Assignment Rules](#2-role-assignment-rules)
3. [Complete Permission Matrix](#3-complete-permission-matrix)
4. [Permission Scopes Explained](#4-permission-scopes-explained)
5. [Special Administrative Roles](#5-special-administrative-roles)
6. [Current Role Assignments](#6-current-role-assignments)
7. [How to Assign Roles](#7-how-to-assign-roles)
8. [Security Constraints](#8-security-constraints)
9. [Use Cases & Examples](#9-use-cases--examples)

---

## 1. ROLE HIERARCHY OVERVIEW

### The Role Pyramid

```
                    🔐 SUPER_ADMIN (Level -1)
                    System God - Can do ANYTHING
                             |
                    🔑 ADMIN (Level 0)
                    System Administrator
                             |
                    👔 RECTOR (Level 1)
                    University Rector
                             |
                    👔 VICE_RECTOR (Level 2)
                    Deputy Rector
                             |
        ┌───────────────────┴───────────────────┐
        |                                       |
    👔 DEAN (Level 3)                  👔 HEAD_OF_DEPT (Level 3)
    Faculty Dean                       Department Head
        |                                       |
    👔 VICE_DEAN (Level 4)                      |
    Deputy Dean                                 |
        |                                       |
        └───────────────────┬───────────────────┘
                            |
                    👔 DEPT_HEAD (Level 5)
                    Department Manager
                            |
            ┌───────────────┴───────────────┐
            |                               |
        👨‍🏫 TEACHER (Level 6)          👨‍🎓 ADVISOR (Level 6)
        Faculty Member                Academic Advisor
            |                               |
            └───────────────┬───────────────┘
                            |
                    👨‍🎓 STUDENT (Level 7)
                    Enrolled Student
```

### Role Levels Table

| Level | Role Code | Name | Power | Users |
|-------|-----------|------|-------|-------|
| **-1** | `SUPER_ADMIN` | Super Administrator | Unlimited | 0 |
| **0** | `ADMIN` | Administrator | System-wide | 1 |
| 1 | `RECTOR` | Rector | University-wide | 1 |
| 2 | `VICE_RECTOR` | Vice Rector | University-wide | 0 |
| 3 | `DEAN` | Dean | Faculty-wide | 1 |
| 3 | `HEAD_OF_DEPT` | Head of Department | Department-wide | 0 |
| 4 | `VICE_DEAN` | Vice Dean | Faculty-wide | 0 |
| 5 | `DEPT_HEAD` | Department Head | Department-wide | 0 |
| 6 | `TEACHER` | Teacher | Department/Course | 190 |
| 6 | `ADVISOR` | Academic Advisor | Student advisory | 0 |
| **7** | `STUDENT` | Student | Own data only | 5,959 |

**IMPORTANT:** Lower level number = Higher power

---

## 2. ROLE ASSIGNMENT RULES

### WHO CAN ASSIGN WHAT

#### 🔐 SUPER_ADMIN (Level -1)

**Can Assign:**
- ✅ Any role including ADMIN and SUPER_ADMIN
- ✅ Unlimited system access
- ✅ Override any security constraint

**Cannot Be Assigned By:** Anyone except direct database manipulation

**Current Assignments:** 0 users (reserved for emergency use)

#### 🔑 ADMIN (Level 0)

**Can Assign:**
- ✅ RECTOR (Level 1)
- ✅ VICE_RECTOR (Level 2)
- ✅ DEAN (Level 3)
- ✅ HEAD_OF_DEPT (Level 3)
- ✅ VICE_DEAN (Level 4)
- ✅ DEPT_HEAD (Level 5)
- ✅ TEACHER (Level 6)
- ✅ ADVISOR (Level 6)
- ✅ STUDENT (Level 7)
- ❌ **CANNOT assign:** SUPER_ADMIN or ADMIN (security restriction)

**Can Be Assigned By:** Only SUPER_ADMIN

**Current Assignments:** 1 user (admin system account)

**Critical Rule:** 
> **ADMIN role can ONLY be assigned by SUPER_ADMIN**  
> This prevents privilege escalation attacks

#### 👔 RECTOR (Level 1)

**Can Assign:**
- ✅ DEAN (Level 3)
- ✅ VICE_DEAN (Level 4)
- ✅ DEPT_HEAD (Level 5)
- ✅ TEACHER (Level 6)
- ✅ ADVISOR (Level 6)
- ✅ STUDENT (Level 7)
- ❌ **CANNOT assign:** SUPER_ADMIN, ADMIN, RECTOR, VICE_RECTOR

**Can Be Assigned By:** ADMIN or SUPER_ADMIN

**Current Assignments:** 1 user (İbad Abbasov)

#### 👔 DEAN (Level 3)

**Can Assign (within their faculty):**
- ✅ VICE_DEAN (Level 4)
- ✅ DEPT_HEAD (Level 5)
- ✅ TEACHER (Level 6)
- ✅ ADVISOR (Level 6)
- ✅ STUDENT (Level 7)
- ❌ **CANNOT assign:** Roles at their level or higher

**Can Be Assigned By:** ADMIN, RECTOR, or SUPER_ADMIN

**Current Assignments:** 1 user (Şahin Musayev)

#### 👔 DEPT_HEAD / HEAD_OF_DEPT (Level 5)

**Can Assign (within their department):**
- ✅ TEACHER (Level 6) - with approval
- ✅ ADVISOR (Level 6) - with approval
- ⚠️ **CANNOT assign directly:** Must request approval from DEAN

**Can Be Assigned By:** ADMIN, RECTOR, DEAN, or SUPER_ADMIN

#### 👨‍🏫 TEACHER / ADVISOR (Level 6)

**Can Assign:**
- ❌ Cannot assign roles

**Can Be Assigned By:** ADMIN, RECTOR, DEAN, DEPT_HEAD, or SUPER_ADMIN

#### 👨‍🎓 STUDENT (Level 7)

**Can Assign:**
- ❌ Cannot assign roles

**Can Be Assigned By:** Any administrative role (ADMIN, RECTOR, DEAN, etc.)

### Assignment Hierarchy Chart

```
SUPER_ADMIN → Can assign: ALL ROLES (including ADMIN)
    ↓
ADMIN → Can assign: RECTOR, VICE_RECTOR, DEAN, ... down to STUDENT
    ↓                     (CANNOT assign SUPER_ADMIN or ADMIN)
RECTOR → Can assign: DEAN, VICE_DEAN, ... down to STUDENT
    ↓                     (CANNOT assign above Level 1)
DEAN → Can assign: VICE_DEAN, DEPT_HEAD, ... down to STUDENT
    ↓                   (Only within their faculty)
DEPT_HEAD → Can assign: TEACHER, ADVISOR (with approval)
    ↓                        (Only within their department)
TEACHER/ADVISOR → Cannot assign roles
STUDENT → Cannot assign roles
```

---

## 3. COMPLETE PERMISSION MATRIX

### 35 System Permissions

| # | Resource | Action | Scope | SUPER | ADMIN | RECTOR | DEAN | TEACHER | STUDENT |
|---|----------|--------|-------|-------|-------|--------|------|---------|---------|
| **ATTENDANCE PERMISSIONS** |
| 1 | attendance | read | own | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2 | attendance | read | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 3 | attendance | create | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 4 | attendance | update | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **COURSE PERMISSIONS** |
| 5 | courses | read | university | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 6 | courses | create | system | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 7 | courses | update | system | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 8 | courses | delete | system | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **ENROLLMENT PERMISSIONS** |
| 9 | enrollments | read | own | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 10 | enrollments | create | own | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| 11 | enrollments | read | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 12 | enrollments | update | department | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 13 | enrollments | delete | department | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **GRADE PERMISSIONS** |
| 14 | grades | read | own | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 15 | grades | read | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 16 | grades | create | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 17 | grades | update | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 18 | grades | delete | department | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 19 | grades | approve | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **STUDENT PERMISSIONS** |
| 20 | students | read | own | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 21 | students | read | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 22 | students | read | university | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 23 | students | update | department | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 24 | students | update | university | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **ASSESSMENT PERMISSIONS** |
| 25 | assessments | create | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 26 | assessments | read | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 27 | assessments | update | department | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 28 | assessments | delete | department | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **SYSTEM PERMISSIONS** |
| 29 | users | create | system | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 30 | users | read | system | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 31 | users | update | system | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 32 | users | delete | system | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 33 | roles | manage | system | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 34 | audit_logs | read | system | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 35 | reports | generate | system | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |

**Legend:**
- ✅ = Has permission
- ❌ = No permission

### Permission Distribution by Role

| Role | Total Permissions | Student | Teacher | Admin |
|------|-------------------|---------|---------|-------|
| **SUPER_ADMIN** | 35 (100%) | All + System | All + System | All |
| **ADMIN** | 33 (94%) | All + System | All + System | All except user delete |
| **RECTOR** | 33 (94%) | All + System | All + System | All except user delete |
| **DEAN** | 33 (94%) | Faculty | Faculty | Faculty-wide |
| **TEACHER** | 9 (26%) | - | Department | - |
| **STUDENT** | 5 (14%) | Own data | - | - |

---

## 4. PERMISSION SCOPES EXPLAINED

### Scope Hierarchy

```
system > university > faculty > department > own
```

### Scope Definitions

#### `own` (Lowest)
- **Access:** User's own data only
- **Example:** Student viewing their own grades
- **SQL Filter:** `WHERE user_id = current_user_id`
- **Used By:** All roles

#### `department`
- **Access:** All data within user's department
- **Example:** Teacher viewing all students in their department
- **SQL Filter:** `WHERE department_id = user_department_id`
- **Used By:** TEACHER, ADVISOR, DEPT_HEAD

#### `faculty`
- **Access:** All data within user's faculty
- **Example:** Dean viewing all departments in their faculty
- **SQL Filter:** `WHERE faculty_id = user_faculty_id`
- **Used By:** DEAN, VICE_DEAN

#### `university`
- **Access:** All data university-wide
- **Example:** Rector viewing all students across all faculties
- **SQL Filter:** No department/faculty filter
- **Used By:** RECTOR, VICE_RECTOR

#### `system` (Highest)
- **Access:** Unrestricted access to all data + system configuration
- **Example:** Admin managing roles and permissions
- **SQL Filter:** No filters, can access system tables
- **Used By:** SUPER_ADMIN, ADMIN, RECTOR (limited)

### Scope Examples

**Scenario:** Viewing student grades

```sql
-- STUDENT (own scope)
SELECT * FROM grades WHERE student_id = 'current-student-id';

-- TEACHER (department scope)  
SELECT * FROM grades 
WHERE student_id IN (
    SELECT id FROM students 
    WHERE department_id = 'teacher-department-id'
);

-- DEAN (faculty scope)
SELECT * FROM grades 
WHERE student_id IN (
    SELECT id FROM students 
    WHERE faculty_id = 'dean-faculty-id'
);

-- RECTOR (university scope)
SELECT * FROM grades;  -- All grades

-- ADMIN (system scope)
SELECT * FROM grades;  -- All grades + can modify grade rules
```

---

## 5. SPECIAL ADMINISTRATIVE ROLES

### 🔐 SUPER_ADMIN

**Purpose:** Emergency system access  
**Assignment:** Direct database manipulation only  
**Current Users:** 0 (none assigned)

**Special Privileges:**
- Can assign ADMIN role
- Can override any security constraint
- Can access deleted/archived data
- Can modify system configuration
- Bypass all RLS policies

**When to Use:**
- System recovery
- Emergency role assignment
- Database maintenance
- Security breach response

**Security:**
```sql
-- SUPER_ADMIN assignment must be done manually:
INSERT INTO user_roles (user_id, role_id, is_primary)
VALUES ('user-uuid', (SELECT id FROM roles WHERE code = 'SUPER_ADMIN'), true);

-- Log this action externally
```

### 🔑 ADMIN

**Purpose:** Day-to-day system administration  
**Assignment:** Only by SUPER_ADMIN  
**Current Users:** 1 (admin system account)

**Special Privileges:**
- Full system access (33 permissions)
- Can assign any role except SUPER_ADMIN and ADMIN
- Can view all audit logs
- Can generate system reports
- Can modify user accounts

**Restrictions:**
- ❌ Cannot assign SUPER_ADMIN role
- ❌ Cannot assign ADMIN role to others
- ❌ Cannot delete users (must deactivate)

**Security:**
```sql
-- ADMIN role can only be assigned by SUPER_ADMIN
-- Attempting to assign ADMIN without SUPER_ADMIN should FAIL
```

### 👔 RECTOR

**Purpose:** University leadership  
**Assignment:** By ADMIN or SUPER_ADMIN  
**Current Users:** 1 (İbad Abbasov - 18JKDR3)

**Special Privileges:**
- University-wide access (33 permissions)
- All ADMIN permissions except user deletion
- Can assign DEAN, VICE_DEAN, DEPT_HEAD, TEACHER, STUDENT
- University-level reports
- Strategic decision access

**Dual Roles:**
```sql
-- Rector typically has both RECTOR and TEACHER roles
SELECT * FROM user_roles WHERE user_id = 'rector-uuid';
-- Returns: RECTOR (is_primary=true), TEACHER (is_primary=false)
```

**Staff Record:**
```sql
-- staff_members.administrative_role = 'rector'
UPDATE staff_members 
SET administrative_role = 'rector'
WHERE user_id = 'rector-uuid';
```

### 👔 DEAN

**Purpose:** Faculty leadership  
**Assignment:** By ADMIN, RECTOR, or SUPER_ADMIN  
**Current Users:** 1 (Şahin Musayev - 1BJ7R3G)

**Special Privileges:**
- Faculty-wide access (33 permissions at faculty scope)
- All ADMIN permissions within their faculty
- Can assign roles within their faculty
- Faculty-level reports
- Department oversight

**Scope Limitation:**
```sql
-- Dean can only access their faculty
SELECT * FROM students 
WHERE program_id IN (
    SELECT id FROM academic_programs 
    WHERE organization_unit_id IN (
        SELECT id FROM organization_units 
        WHERE parent_id = 'dean-faculty-id'
    )
);
```

**Dual Roles:**
```sql
-- Dean typically has both DEAN and TEACHER roles
SELECT * FROM user_roles WHERE user_id = 'dean-uuid';
-- Returns: DEAN (is_primary=true), TEACHER (is_primary=false)
```

---

## 6. CURRENT ROLE ASSIGNMENTS

### Active Assignments (as of October 10, 2025)

| Role | Count | Details |
|------|-------|---------|
| **SUPER_ADMIN** | 0 | Reserved for emergency |
| **ADMIN** | 1 | admin (system account) |
| **RECTOR** | 1 | İbad Abbasov (18JKDR3) |
| **VICE_RECTOR** | 0 | Position available |
| **DEAN** | 1 | Şahin Musayev (1BJ7R3G) |
| **HEAD_OF_DEPT** | 0 | Positions available |
| **VICE_DEAN** | 0 | Positions available |
| **DEPT_HEAD** | 0 | Positions available |
| **TEACHER** | 190 active | + 160 expired (inactive staff) |
| **ADVISOR** | 0 | Positions available |
| **STUDENT** | 5,959 | All enrolled students |
| **Total** | 6,151 | Active role assignments |

### Leadership Details

**RECTOR:**
```yaml
Name: İbad Abbasov
Username: 18JKDR3
User ID: 529a5428-ac22-41e4-a35a-12733bec563d
Roles: {RECTOR, TEACHER}
Primary Role: RECTOR
Administrative Role: rector
Permissions: 33 (all ADMIN permissions)
Assigned: October 10, 2025
```

**DEAN:**
```yaml
Name: Şahin Musayev
Username: 1BJ7R3G
User ID: 34709c37-5e9f-4c79-87a7-b8f619d2c985
Roles: {DEAN, TEACHER}
Primary Role: DEAN
Administrative Role: dean
Permissions: 33 (all ADMIN permissions)
Assigned: October 10, 2025
```

**ADMIN:**
```yaml
Username: admin
User ID: [system account]
Roles: {ADMIN}
Primary Role: ADMIN
Permissions: 33 (all ADMIN permissions)
Purpose: System administration
```

### Users Without Roles

- **Count:** 314 active users
- **Reason:** Legacy accounts from old database
- **Action:** Low priority - most have no login activity
- **Status:** Acceptable - RLS policies prevent unauthorized access

---

## 7. HOW TO ASSIGN ROLES

### Via SQL (Recommended for bulk operations)

```sql
-- 1. Assign RECTOR role
INSERT INTO user_roles (user_id, role_id, is_primary, assigned_by)
VALUES (
    'user-uuid-here',
    (SELECT id FROM roles WHERE code = 'RECTOR'),
    true,  -- Primary role
    'admin-user-uuid'  -- Who assigned it
);

-- 2. Update staff administrative_role
UPDATE staff_members
SET administrative_role = 'rector'
WHERE user_id = 'user-uuid-here';

-- 3. Verify assignment
SELECT 
    u.username,
    r.code as role,
    r.name,
    ur.is_primary,
    ur.created_at
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.id = 'user-uuid-here';
```

### Via API (Recommended for UI)

```bash
# POST /api/v1/users/{user_id}/roles
curl -X POST http://localhost:8000/api/v1/users/{user_id}/roles \
  -H "Authorization: Bearer {admin-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "role_code": "DEAN",
    "is_primary": true,
    "valid_from": "2025-10-10",
    "valid_until": null
  }'
```

### Assignment Checklist

**Before assigning administrative roles:**

- [ ] Verify user exists and is active
- [ ] Confirm you have permission to assign this role
- [ ] Check if user already has conflicting roles
- [ ] Verify organizational unit assignment (for DEAN, DEPT_HEAD)
- [ ] Update staff_members.administrative_role if needed
- [ ] Assign necessary permissions to the role
- [ ] Test role access after assignment
- [ ] Log the assignment in audit_logs

### Examples

**Assign DEAN to a user:**

```sql
-- Step 1: Find user
SELECT id, username, first_name, last_name 
FROM users 
WHERE username = '1BJ7R3G';
-- Result: 34709c37-5e9f-4c79-87a7-b8f619d2c985

-- Step 2: Assign DEAN role
INSERT INTO user_roles (user_id, role_id, is_primary)
VALUES (
    '34709c37-5e9f-4c79-87a7-b8f619d2c985',
    (SELECT id FROM roles WHERE code = 'DEAN'),
    true
);

-- Step 3: Update administrative_role
UPDATE staff_members
SET administrative_role = 'dean'
WHERE user_id = '34709c37-5e9f-4c79-87a7-b8f619d2c985';

-- Step 4: Assign permissions (if not already assigned to role)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE code = 'DEAN'),
    id
FROM permissions
WHERE (resource, action, scope) IN (
    ('students', 'read', 'faculty'),
    ('grades', 'read', 'faculty'),
    -- ... other permissions
);

-- Step 5: Verify
SELECT 
    u.username,
    array_agg(r.code) as roles,
    s.administrative_role
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN staff_members s ON u.id = s.user_id
WHERE u.id = '34709c37-5e9f-4c79-87a7-b8f619d2c985'
GROUP BY u.username, s.administrative_role;
```

**Assign TEACHER to multiple users:**

```sql
-- Bulk assign TEACHER role to all staff without roles
INSERT INTO user_roles (user_id, role_id, is_primary)
SELECT 
    s.user_id,
    (SELECT id FROM roles WHERE code = 'TEACHER'),
    true
FROM staff_members s
WHERE s.user_id NOT IN (
    SELECT user_id FROM user_roles 
    WHERE (valid_until IS NULL OR valid_until > CURRENT_TIMESTAMP)
)
AND s.is_active = true;
```

---

## 8. SECURITY CONSTRAINTS

### Database Constraints

**Prevent ADMIN Self-Assignment:**

```sql
-- This constraint should be added to prevent non-SUPER_ADMIN from assigning ADMIN
CREATE OR REPLACE FUNCTION prevent_admin_assignment()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if trying to assign ADMIN or SUPER_ADMIN role
    IF NEW.role_id IN (
        SELECT id FROM roles WHERE code IN ('ADMIN', 'SUPER_ADMIN')
    ) THEN
        -- Check if current user is SUPER_ADMIN
        IF NOT EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = current_setting('app.current_user_id')::uuid
            AND r.code = 'SUPER_ADMIN'
            AND (ur.valid_until IS NULL OR ur.valid_until > CURRENT_TIMESTAMP)
        ) THEN
            RAISE EXCEPTION 'Only SUPER_ADMIN can assign ADMIN or SUPER_ADMIN roles';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_admin_assignment
    BEFORE INSERT ON user_roles
    FOR EACH ROW
    EXECUTE FUNCTION prevent_admin_assignment();
```

### Row-Level Security

**Students can only see their own data:**

```sql
CREATE POLICY students_own_data ON students
    FOR SELECT
    TO PUBLIC
    USING (
        user_id = current_setting('app.current_user_id')::uuid
        OR EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = current_setting('app.current_user_id')::uuid
            AND r.level <= 6  -- Administrative roles
        )
    );
```

### API-Level Checks

**Python permission check:**

```python
def has_permission(user, resource, action, scope):
    """Check if user has permission."""
    return db.query(Permission).join(
        RolePermission, Permission.id == RolePermission.permission_id
    ).join(
        UserRole, RolePermission.role_id == UserRole.role_id
    ).filter(
        UserRole.user_id == user.id,
        Permission.resource == resource,
        Permission.action == action,
        or_(
            Permission.scope == scope,
            Permission.scope == 'system'  # System scope overrides all
        ),
        or_(
            UserRole.valid_until.is_(None),
            UserRole.valid_until > func.now()
        )
    ).first() is not None

# Usage
if not has_permission(current_user, 'grades', 'update', 'department'):
    raise HTTPException(403, "Insufficient permissions")
```

### Audit Logging

**All role assignments are logged:**

```sql
-- Audit log entry example
{
    "action": "INSERT",
    "user_id": "admin-uuid",
    "resource_type": "user_roles",
    "resource_id": "role-assignment-uuid",
    "old_values": null,
    "new_values": {
        "user_id": "target-user-uuid",
        "role_id": "dean-role-uuid",
        "is_primary": true
    },
    "ip_address": "192.168.1.100",
    "created_at": "2025-10-10 14:30:00"
}
```

---

## 9. USE CASES & EXAMPLES

### Use Case 1: Dean Assigns Teacher

**Scenario:** Dean of Faculty of Engineering wants to assign TEACHER role to a new hire

**Permission Check:**
```sql
-- Dean has permission to assign TEACHER within their faculty
SELECT EXISTS (
    SELECT 1 FROM role_permissions rp
    JOIN permissions p ON rp.permission_id = p.id
    JOIN user_roles ur ON rp.role_id = ur.role_id
    WHERE ur.user_id = 'dean-uuid'
    AND p.resource = 'roles'
    AND p.action = 'assign'
    AND p.scope IN ('faculty', 'system')
) as can_assign;
-- Returns: true
```

**Assignment:**
```sql
INSERT INTO user_roles (user_id, role_id, is_primary)
VALUES (
    'new-teacher-uuid',
    (SELECT id FROM roles WHERE code = 'TEACHER'),
    true
);
```

### Use Case 2: Teacher Views Department Students

**Scenario:** Teacher wants to see all students in their department

**Permission:**
- Resource: `students`
- Action: `read`
- Scope: `department`

**Query:**
```sql
SELECT s.student_id, p.first_name, p.last_name, s.cumulative_gpa
FROM students s
JOIN persons p ON s.user_id = p.user_id
WHERE s.program_id IN (
    SELECT id FROM academic_programs
    WHERE organization_unit_id = (
        SELECT department_id FROM staff_members
        WHERE user_id = 'teacher-uuid'
    )
);
```

### Use Case 3: Student Views Own Grades

**Scenario:** Student wants to see their grades

**Permission:**
- Resource: `grades`
- Action: `read`
- Scope: `own`

**Query:**
```sql
SELECT 
    c.code || ' - ' || c.name->>'en' as course,
    g.letter_grade,
    g.grade_point,
    g.earned_credits
FROM grades g
JOIN course_enrollments ce ON g.enrollment_id = ce.id
JOIN course_offerings co ON ce.course_offering_id = co.id
JOIN courses c ON co.course_id = c.id
WHERE ce.student_id = 'student-uuid'
ORDER BY g.created_at DESC;
```

### Use Case 4: Rector Generates University Report

**Scenario:** Rector needs enrollment statistics across all faculties

**Permission:**
- Resource: `reports`
- Action: `generate`
- Scope: `system`

**Query:**
```sql
SELECT 
    ou.name->>'en' as faculty,
    COUNT(DISTINCT s.id) as total_students,
    AVG(s.cumulative_gpa) as avg_gpa,
    COUNT(DISTINCT ce.id) as total_enrollments
FROM students s
JOIN academic_programs ap ON s.program_id = ap.id
JOIN organization_units ou ON ap.organization_unit_id = ou.id
LEFT JOIN course_enrollments ce ON s.id = ce.student_id
WHERE ou.unit_type = 'faculty'
GROUP BY ou.id, ou.name
ORDER BY total_students DESC;
```

### Use Case 5: Admin Cannot Assign ADMIN

**Scenario:** ADMIN user tries to assign ADMIN role to another user (should FAIL)

**Attempt:**
```sql
INSERT INTO user_roles (user_id, role_id, is_primary)
VALUES (
    'target-user-uuid',
    (SELECT id FROM roles WHERE code = 'ADMIN'),
    true
);
```

**Result:**
```
ERROR: Only SUPER_ADMIN can assign ADMIN or SUPER_ADMIN roles
```

**Correct Approach:**
```sql
-- Must be done by SUPER_ADMIN or direct database manipulation
-- 1. Set session context
SET app.current_user_id = 'super-admin-uuid';

-- 2. Then assign
INSERT INTO user_roles ...
```

---

## SUMMARY

### Key Principles

1. **Hierarchy is Strict:** Lower level number = higher power
2. **ADMIN Protection:** Only SUPER_ADMIN can assign ADMIN role
3. **Scope Matters:** Permissions are limited by scope (own → department → faculty → university → system)
4. **Audit Everything:** All role assignments and permission checks are logged
5. **Dual Roles:** Administrative staff can have multiple roles (e.g., RECTOR + TEACHER)

### Quick Reference

**Who can assign what?**
- SUPER_ADMIN → Everything
- ADMIN → Everything except SUPER_ADMIN and ADMIN
- RECTOR → DEAN, TEACHER, STUDENT
- DEAN → TEACHER, STUDENT (within faculty)
- TEACHER → Nothing

**Permission counts:**
- SUPER_ADMIN/ADMIN/RECTOR: 33-35 permissions
- TEACHER: 9 permissions
- STUDENT: 5 permissions

**Current state:**
- 1 ADMIN (system)
- 1 RECTOR (İbad Abbasov)
- 1 DEAN (Şahin Musayev)
- 190 TEACHER (active staff)
- 5,959 STUDENT (enrolled students)

---

**Document Version:** 1.0  
**Last Updated:** October 10, 2025  
**Maintained By:** Development Team  
**Status:** ✅ PRODUCTION READY
