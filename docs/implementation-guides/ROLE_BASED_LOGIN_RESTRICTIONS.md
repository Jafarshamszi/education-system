# Role-Based Login Restrictions Implementation

## Date: October 11, 2025

## Overview
Implemented strict role-based login restrictions to ensure users can only access portals appropriate for their role:
- **Students** → Can only login through student portal
- **Teachers** → Can login through teacher or admin portals
- **Admins** → Can login through teacher or admin portals

## Implementation Details

### 1. Backend Changes

#### Updated Schema (`backend/app/schemas/auth.py`)
Added `frontend_type` parameter to `LoginRequest`:

```python
class LoginRequest(BaseModel):
    """Request schema for user login - username or email + password"""
    username: str  # Can be username or email
    password: str
    frontend_type: Optional[Literal["student", "teacher", "admin"]] = None
```

#### Updated Login Endpoint (`backend/app/api/auth.py`)
Added validation logic after user type determination:

```python
# Validate user type against frontend type (role-based access control)
if login_data.frontend_type:
    allowed_access = {
        "student": ["STUDENT"],
        "teacher": ["TEACHER", "ADMIN"],
        "admin": ["TEACHER", "ADMIN"]
    }
    
    allowed_types = allowed_access.get(login_data.frontend_type, [])
    if user_type not in allowed_types:
        # Create user-friendly error messages
        error_messages = {
            ("STUDENT", "teacher"): (
                "Students cannot access the teacher portal. "
                "Please use the student portal to login."
            ),
            ("STUDENT", "admin"): (
                "Students cannot access the admin portal. "
                "Please use the student portal to login."
            ),
            ("TEACHER", "student"): (
                "Teachers cannot access the student portal. "
                "Please use the teacher portal to login."
            ),
            ("ADMIN", "student"): (
                "Administrators cannot access the student portal. "
                "Please use the admin portal to login."
            )
        }
        
        error_key = (user_type, login_data.frontend_type)
        error_message = error_messages.get(
            error_key,
            f"Access denied. {user_type}s cannot login "
            f"through the {login_data.frontend_type} portal."
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_message
        )
```

### 2. Frontend Changes

#### Updated Login Form Component (`frontend/src/components/auth/LoginFormEnhanced.tsx`)

Added `frontendType` prop to component:

```typescript
interface LoginFormEnhancedProps {
  frontendType?: 'student' | 'teacher' | 'admin';
}

export default function LoginFormEnhanced({ frontendType = 'student' }: LoginFormEnhancedProps) {
  // ...
  
  const onSubmit = async (data: LoginFormData) => {
    // ...
    body: JSON.stringify({
      username: data.username,
      password: data.password,
      frontend_type: frontendType  // Send frontend type to backend
    })
  };
}
```

#### Created Separate Login Pages

**Student Login** (`frontend/src/app/login/student/page.tsx`):
```typescript
export default function StudentLoginPage() {
  return <LoginFormEnhanced frontendType="student" />;
}
```

**Teacher Login** (`frontend/src/app/login/teacher/page.tsx`):
```typescript
export default function TeacherLoginPage() {
  return <LoginFormEnhanced frontendType="teacher" />;
}
```

**Admin Login** (`frontend/src/app/login/admin/page.tsx`):
```typescript
export default function AdminLoginPage() {
  return <LoginFormEnhanced frontendType="admin" />;
}
```

## Access Control Matrix

| User Role | Student Portal | Teacher Portal | Admin Portal |
|-----------|---------------|----------------|--------------|
| STUDENT   | ✅ Allowed    | ❌ Forbidden   | ❌ Forbidden |
| TEACHER   | ❌ Forbidden  | ✅ Allowed     | ✅ Allowed   |
| ADMIN     | ❌ Forbidden  | ✅ Allowed     | ✅ Allowed   |

## Testing Results

### Test 1: Student Accessing Student Portal
**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "TEST3333", "password": "TEST3333", "frontend_type": "student"}'
```

**Result**: ✅ **SUCCESS**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": "74c409cd-967c-4603-94d3-3f40e36cdd1b",
  "username": "TEST3333",
  "user_type": "STUDENT",
  "full_name": "Test3Ad Test3SoyadAd",
  "email": "TEST3333@temp.bbu.edu.az"
}
```

### Test 2: Student Trying to Access Teacher Portal
**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "TEST3333", "password": "TEST3333", "frontend_type": "teacher"}'
```

**Result**: ❌ **BLOCKED (403 Forbidden)**
```json
{
  "detail": "Students cannot access the teacher portal. Please use the student portal to login."
}
```

### Test 3: Teacher Accessing Teacher Portal
**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "5GK3GY7", "password": "gunay91", "frontend_type": "teacher"}'
```

**Result**: ✅ **SUCCESS**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": "b4e0755b-b5af-4ffc-9c22-e4a8e5e3fda6",
  "username": "5GK3GY7",
  "user_type": "TEACHER",
  "full_name": "GÜNAY RAMAZANOVA",
  "email": "5GK3GY7@temp.bbu.edu.az"
}
```

### Test 4: Teacher Trying to Access Student Portal
**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "5GK3GY7", "password": "gunay91", "frontend_type": "student"}'
```

**Result**: ❌ **BLOCKED (403 Forbidden)**
```json
{
  "detail": "Teachers cannot access the student portal. Please use the teacher portal to login."
}
```

### Test 5: Teacher Accessing Admin Portal
**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "5GK3GY7", "password": "gunay91", "frontend_type": "admin"}'
```

**Result**: ✅ **SUCCESS**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": "b4e0755b-b5af-4ffc-9c22-e4a8e5e3fda6",
  "username": "5GK3GY7",
  "user_type": "TEACHER",
  "full_name": "GÜNAY RAMAZANOVA",
  "email": "5GK3GY7@temp.bbu.edu.az"
}
```

## Error Messages

The system provides clear, user-friendly error messages for each restriction scenario:

1. **Student → Teacher Portal**: "Students cannot access the teacher portal. Please use the student portal to login."
2. **Student → Admin Portal**: "Students cannot access the admin portal. Please use the student portal to login."
3. **Teacher → Student Portal**: "Teachers cannot access the student portal. Please use the teacher portal to login."
4. **Admin → Student Portal**: "Administrators cannot access the student portal. Please use the admin portal to login."

## Frontend URL Routes

- **Student Portal Login**: `/login/student`
- **Teacher Portal Login**: `/login/teacher`
- **Admin Portal Login**: `/login/admin`
- **Default Login**: `/login` (defaults to student portal)

## Security Considerations

### Benefits
1. **Role Separation**: Prevents unauthorized access across different user portals
2. **Clear Boundaries**: Each user type has a dedicated entry point
3. **User-Friendly**: Clear error messages guide users to the correct portal
4. **Flexible for Admins**: Teachers and admins can access both teacher and admin portals
5. **HTTP 403 Forbidden**: Uses appropriate status code for access denial

### Implementation Notes
- The `frontend_type` parameter is **optional** for backward compatibility
- When `frontend_type` is not provided, no restriction is enforced
- Validation happens **after** password verification to prevent user enumeration
- Uses HTTP 403 (Forbidden) instead of 401 (Unauthorized) since authentication succeeded but authorization failed

## Micro Frontend Architecture Alignment

This implementation aligns with the project's micro frontend architecture:
- **Student Frontend**: Separate portal for students (e.g., `/login/student`)
- **Teacher/Admin Frontend**: Separate portal for teachers and admins (e.g., `/login/teacher`, `/login/admin`)
- **Shared Components**: `LoginFormEnhanced` component is reused across all portals with different `frontendType` prop

## Next Steps

### Recommended Enhancements
1. **Route Protection**: Add middleware to protect dashboard routes based on user_type
2. **Automatic Redirection**: Redirect users to their appropriate dashboard after login
3. **Session Validation**: Validate user_type matches current portal on each request
4. **Frontend Router Guards**: Add Next.js middleware to prevent accessing wrong portal routes
5. **Logout from All Portals**: Implement cross-portal logout mechanism

### Optional Features
1. **Remember Portal Preference**: Store last used portal in localStorage
2. **Auto-detect User Type**: Show appropriate login link based on detection
3. **Portal Switcher**: Add UI to switch between portals (for admins/teachers)
4. **Audit Logging**: Log portal access attempts for security monitoring

## Files Modified

### Backend
1. `backend/app/schemas/auth.py` - Added `frontend_type` field to `LoginRequest`
2. `backend/app/api/auth.py` - Added role-based access control validation

### Frontend
1. `frontend/src/components/auth/LoginFormEnhanced.tsx` - Added `frontendType` prop and logic
2. `frontend/src/app/login/student/page.tsx` - Created student login page
3. `frontend/src/app/login/teacher/page.tsx` - Created teacher login page
4. `frontend/src/app/login/admin/page.tsx` - Created admin login page

## Conclusion

✅ **Role-based login restrictions successfully implemented**
- Students are restricted to student portal only
- Teachers can access teacher and admin portals
- Admins can access teacher and admin portals
- Clear error messages guide users to correct portal
- All test scenarios passed successfully
- Implementation follows micro frontend architecture principles
