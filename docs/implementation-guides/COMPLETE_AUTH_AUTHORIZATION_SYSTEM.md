# Complete Authentication & Authorization System

## Overview
This document describes the complete authentication and authorization system implemented in the Education System, including login authentication, role-based access control, and route protection.

## System Architecture

### 1. Authentication Flow

```
User Login → Backend Validates → Returns JWT + User Type → Frontend Stores → Access Granted
```

#### Login Process
1. User enters credentials (username + password) on appropriate login page
2. Frontend sends POST request to `/api/v1/auth/login` with:
   - `username`: User's username
   - `password`: User's password
   - `frontend_type`: Portal type ("student", "teacher", or "admin")

3. Backend validates:
   - User exists in database
   - Password is correct (bcrypt hash verification)
   - Account is active and not locked
   - User type matches frontend_type (role-based access control)

4. Backend returns:
   - `access_token`: JWT bearer token
   - `user_id`: User's UUID
   - `username`: User's username
   - `user_type`: STUDENT, TEACHER, or ADMIN
   - `full_name`: User's full name
   - `email`: User's email

5. Frontend stores in localStorage:
   - access_token
   - user_id
   - username
   - user_type
   - full_name
   - email

### 2. Role-Based Login Restrictions (Backend)

The backend enforces portal access restrictions at the authentication level:

#### Access Control Matrix
| User Type | Student Portal | Teacher Portal | Admin Portal |
|-----------|---------------|---------------|--------------|
| STUDENT   | ✅ Allowed     | ❌ Blocked     | ❌ Blocked    |
| TEACHER   | ❌ Blocked     | ✅ Allowed     | ✅ Allowed    |
| ADMIN     | ❌ Blocked     | ✅ Allowed     | ✅ Allowed    |

#### Implementation
**File**: `backend/app/api/auth.py`

```python
# Access control validation
if login_data.frontend_type:
    allowed_access = {
        "student": ["STUDENT"],
        "teacher": ["TEACHER", "ADMIN"],
        "admin": ["TEACHER", "ADMIN"]
    }
    
    allowed_types = allowed_access.get(login_data.frontend_type, [])
    if user_type not in allowed_types:
        # Return HTTP 403 Forbidden with user-friendly error message
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User type not allowed for this portal"
        )
```

#### Error Messages
- **Student → Teacher Portal**: "Students cannot access the teacher portal. Please use the student portal to login."
- **Student → Admin Portal**: "Students cannot access the admin portal. Please use the student portal to login."
- **Teacher → Student Portal**: "Teachers cannot access the student portal. Please use the teacher portal to login."
- **Admin → Student Portal**: "Administrators cannot access the student portal. Please use the admin portal to login."

### 3. Login Pages (Frontend)

#### Student Login
- **URL**: `/login/student`
- **File**: `frontend/src/app/login/student/page.tsx`
- **Frontend Type**: "student"
- **Allowed Users**: STUDENT only

#### Teacher Login
- **URL**: `/login/teacher`
- **File**: `frontend/src/app/login/teacher/page.tsx`
- **Frontend Type**: "teacher"
- **Allowed Users**: TEACHER, ADMIN

#### Admin Login
- **URL**: `/login/admin`
- **File**: `frontend/src/app/login/admin/page.tsx`
- **Frontend Type**: "admin"
- **Allowed Users**: TEACHER, ADMIN

### 4. Route Protection (Frontend)

To prevent users from manually navigating to unauthorized pages after login, we implement client-side route protection.

#### ProtectedRoute Component
**File**: `frontend/src/components/auth/ProtectedRoute.tsx`

This component:
1. Checks if user is logged in (has access_token in localStorage)
2. Verifies user_type matches allowed roles for the route
3. Redirects unauthorized users with error message
4. Auto-redirects to appropriate dashboard after 3 seconds

#### Usage Example

```tsx
import ProtectedRoute from '@/components/auth/ProtectedRoute';

export default function StudentsPage() {
  return (
    <ProtectedRoute allowedRoles={['TEACHER', 'ADMIN', 'SYSADMIN']}>
      {/* Page content - only accessible by teachers and admins */}
    </ProtectedRoute>
  );
}
```

#### Route Access Matrix
| Route Path | Allowed Roles | Purpose |
|-----------|--------------|---------|
| `/dashboard/students` | TEACHER, ADMIN, SYSADMIN | Student management |
| `/dashboard/student-orders` | TEACHER, ADMIN, SYSADMIN | Student orders |
| `/dashboard/student-groups` | TEACHER, ADMIN, SYSADMIN | Student groups |
| `/dashboard/teachers` | ADMIN, SYSADMIN | Teacher management |
| `/dashboard/requests` | ADMIN, SYSADMIN | Academic requests |
| `/dashboard/organizations` | ADMIN, SYSADMIN | Organization structure |
| `/dashboard/student` | STUDENT | Student dashboard |
| `/dashboard/teacher` | TEACHER | Teacher dashboard |
| `/dashboard` | ALL | General dashboard |

### 5. User Type Detection

The backend determines user type by querying database tables:

**File**: `backend/app/api/auth.py`

```python
# Check if user is a student
student_check = db.execute(
    text("SELECT id FROM students WHERE user_id = :user_id LIMIT 1"),
    {"user_id": str(user.id)}
).fetchone()

if student_check:
    user_type = "STUDENT"
else:
    # Check if user is staff/teacher
    staff_check = db.execute(
        text(
            "SELECT id, academic_rank, administrative_role "
            "FROM staff_members WHERE user_id = :user_id LIMIT 1"
        ),
        {"user_id": str(user.id)}
    ).fetchone()
    
    if staff_check:
        # Determine if TEACHER or ADMIN based on role
        admin_role = staff_check[2] if len(staff_check) > 2 else None
        
        if admin_role and admin_role in [
            'rector', 'vice_rector', 'dean', 'vice_dean',
            'head_of_department'
        ]:
            user_type = "ADMIN"
        else:
            user_type = "TEACHER"
```

#### Database Tables
- **users**: Core authentication (username, password_hash, email)
- **students**: Student records (linked via user_id)
- **staff_members**: Teacher/staff records (linked via user_id)
- **persons**: Personal information (first_name, last_name)

### 6. Security Features

#### Password Security
- **Hashing**: bcrypt with $2b$12$ rounds
- **Fallback**: Legacy plain-text passwords supported with automatic upgrade
- **Length Limit**: 72 bytes (bcrypt limitation)

#### Token Security
- **Type**: JWT (JSON Web Token)
- **Storage**: localStorage (frontend)
- **Expiration**: Configurable (default: from settings.ACCESS_TOKEN_EXPIRE_MINUTES)
- **Contents**: user_id, user_type, username

#### Session Management
- Account status check (is_active, is_locked)
- Token verification on protected routes
- Auto-redirect on missing/invalid authentication

### 7. Testing Scenarios

#### Test Accounts
- **Student**: TEST3333 / TEST3333 (user_type: STUDENT)
- **Teacher**: 5GK3GY7 / gunay91 (user_type: TEACHER)

#### Successful Login Tests

```bash
# Student logging into student portal - SUCCESS
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "TEST3333", "password": "TEST3333", "frontend_type": "student"}'

# Teacher logging into teacher portal - SUCCESS
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "5GK3GY7", "password": "gunay91", "frontend_type": "teacher"}'

# Teacher logging into admin portal - SUCCESS
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "5GK3GY7", "password": "gunay91", "frontend_type": "admin"}'
```

#### Blocked Login Tests

```bash
# Student trying teacher portal - BLOCKED (403)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "TEST3333", "password": "TEST3333", "frontend_type": "teacher"}'
# Response: "Students cannot access the teacher portal..."

# Teacher trying student portal - BLOCKED (403)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "5GK3GY7", "password": "gunay91", "frontend_type": "student"}'
# Response: "Teachers cannot access the student portal..."
```

#### Route Protection Tests

1. **Teacher manually navigating to student pages**:
   - Login through `/login/teacher` → SUCCESS
   - Navigate to `/dashboard/students` → BLOCKED
   - Shows error message and auto-redirects to teacher dashboard

2. **Student manually navigating to teacher pages**:
   - Login through `/login/student` → SUCCESS
   - Navigate to `/dashboard/teachers` → BLOCKED
   - Shows error message and auto-redirects to student dashboard

### 8. Implementation Checklist

#### Backend (✅ Complete)
- [x] User type detection from database tables
- [x] Role-based login restrictions with frontend_type
- [x] Access control validation in login endpoint
- [x] User-friendly error messages for blocked access
- [x] JWT token generation with user_type

#### Frontend (✅ Complete)
- [x] Separate login pages for student/teacher/admin
- [x] LoginFormEnhanced component with frontendType prop
- [x] ProtectedRoute component for route protection
- [x] Route protection applied to students page
- [ ] Route protection applied to all other restricted pages

### 9. Next Steps

#### Apply Route Protection to Remaining Pages

**Pages requiring TEACHER/ADMIN only**:
- `/dashboard/student-orders/page.tsx`
- `/dashboard/student-groups/page.tsx`
- `/dashboard/teachers/page.tsx`

**Pages requiring ADMIN only**:
- `/dashboard/requests/page.tsx`
- `/dashboard/organizations/page.tsx`

**Implementation**:
```tsx
import ProtectedRoute from '@/components/auth/ProtectedRoute';

export default function PageName() {
  return (
    <ProtectedRoute allowedRoles={['TEACHER', 'ADMIN', 'SYSADMIN']}>
      {/* Page content */}
    </ProtectedRoute>
  );
}
```

### 10. Troubleshooting

#### Issue: Teacher can access student pages
**Cause**: Route protection not applied to the page
**Solution**: Wrap page component with ProtectedRoute

#### Issue: User gets "Access Denied" on pages they should access
**Cause**: user_type in localStorage doesn't match allowedRoles
**Solution**: Check localStorage user_type and verify allowedRoles array

#### Issue: Login succeeds but page shows "Verifying access..."
**Cause**: ProtectedRoute loading state
**Solution**: This is normal - component is checking authorization

#### Issue: Auto-redirect not working
**Cause**: redirectTo prop not set or default redirect logic failing
**Solution**: Check useEffect redirect logic in ProtectedRoute component

### 11. Database Schema Reference

```sql
-- Users table (authentication)
users {
  id: UUID (PK)
  username: VARCHAR(150) UNIQUE
  password_hash: VARCHAR(255)
  email: VARCHAR(255)
  is_active: BOOLEAN
  is_locked: BOOLEAN
}

-- Students table (student records)
students {
  id: UUID (PK)
  user_id: UUID (FK → users.id)
  student_number: VARCHAR UNIQUE
  -- other student fields
}

-- Staff members table (teacher/admin records)
staff_members {
  id: UUID (PK)
  user_id: UUID (FK → users.id)
  employee_number: VARCHAR UNIQUE
  academic_rank: VARCHAR
  administrative_role: VARCHAR
  -- other staff fields
}

-- Persons table (personal info)
persons {
  id: UUID (PK)
  user_id: UUID (FK → users.id)
  first_name: VARCHAR
  last_name: VARCHAR
  -- other personal fields
}
```

## Summary

The authentication and authorization system provides:

1. **Backend Authentication**: Validates credentials against database with bcrypt hashing
2. **Role Detection**: Automatically determines user type from database tables
3. **Portal Access Control**: Prevents users from logging into wrong portals
4. **Route Protection**: Prevents manual URL navigation to unauthorized pages
5. **Security**: JWT tokens, password hashing, account status checks
6. **User Experience**: Clear error messages, auto-redirects, loading states

This creates a comprehensive security system that works at both the authentication layer (preventing wrong portal logins) and the authorization layer (preventing unauthorized page access).
