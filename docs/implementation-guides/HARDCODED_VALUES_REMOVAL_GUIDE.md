# Removing Hardcoded Values - Implementation Guide

## Overview
This document outlines the removal of hardcoded values from the Education System codebase and provides guidelines for proper configuration management.

## Changes Implemented

### 1. Frontend Environment Configuration

#### Teacher Frontend (`frontend-teacher`)
- Created `.env.local` and `.env.local.example` files
- Created `lib/api-config.ts` for centralized API configuration
- Environment variables:
  - `NEXT_PUBLIC_API_URL`: Backend API base URL (default: http://localhost:8000)
  - `NEXT_PUBLIC_API_VERSION`: API version (default: v1)
  - `NEXT_PUBLIC_APP_NAME`: Application name
  - `NODE_ENV`: Environment (development/production)

#### Student Frontend (`frontend-student`)
- Created `.env.local` and `.env.local.example` files
- Created `lib/api-config.ts` for centralized API configuration
- Same environment variables as teacher frontend

#### Admin Frontend (`frontend`)
- Created `.env.local` and `.env.local.example` files  
- Same environment variables as other frontends

### 2. Backend Configuration

#### Database Configuration
- All database credentials moved to environment variables in `.env`:
  - `DB_HOST`: Database host (default: localhost)
  - `DB_PORT`: Database port (default: 5432)
  - `DB_USER`: Database user (default: postgres)
  - `DB_PASSWORD`: Database password
  - `DB_NAME`: Database name (default: lms)

#### CORS Configuration
- CORS origins moved to environment variable:
  - `BACKEND_CORS_ORIGINS`: Comma-separated list of allowed origins
  - Example: `http://localhost:3000,http://localhost:3001,http://localhost:8080`

### 3. API Configuration Utility

Created `lib/api-config.ts` in each frontend with:

```typescript
// Centralized API endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_URL}/auth/login`,
    // ... other endpoints
  },
  TEACHERS: { ... },
  STUDENTS: { ... },
};

// Utility functions
export function buildUrl(baseUrl, params): string
export function getAuthHeaders(): HeadersInit
export function authFetch(url, options): Promise<Response>
```

## Migration Guide

### For Frontend Developers

#### Old Way (Hardcoded):
```typescript
const response = await fetch('http://localhost:8000/api/v1/teachers/me/dashboard', {
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});
```

#### New Way (Using API Config):
```typescript
import { API_ENDPOINTS, authFetch } from '@/lib/api-config';

const response = await authFetch(API_ENDPOINTS.TEACHERS.DASHBOARD);
```

### For Backend Developers

#### Old Way (Hardcoded in API files):
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="lms",
    user="postgres",
    password="1111"
)
```

#### New Way (Using Settings):
```python
from app.core.config import get_settings
import psycopg2

settings = get_settings()

conn = psycopg2.connect(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD
)
```

## Files That Need Manual Updates

### High Priority (Production-Critical)

#### Frontend Teacher:
- [ ] `components/login-form.tsx` - Update to use API_ENDPOINTS.AUTH.LOGIN
- [ ] `app/dashboard/page.tsx` - Update to use API_ENDPOINTS.TEACHERS.DASHBOARD
- [ ] `app/dashboard/courses/page.tsx` - Update to use API_ENDPOINTS.TEACHERS.COURSES
- [ ] `app/dashboard/students/page.tsx` - Update to use API_ENDPOINTS.TEACHERS.STUDENTS
- [ ] `app/dashboard/attendance/page.tsx` - Update to use API_ENDPOINTS.TEACHERS.STUDENTS
- [ ] `app/dashboard/grades/page.tsx` - Update to use API_ENDPOINTS.TEACHERS.STUDENTS
- [ ] `app/dashboard/schedule/page.tsx` - Update to use API_ENDPOINTS.TEACHERS.SCHEDULE
- [ ] `components/app-sidebar.tsx` - Update to use API_ENDPOINTS.TEACHERS.DASHBOARD

#### Frontend Student:
- [ ] `components/login-form.tsx` - Update to use API_ENDPOINTS.AUTH.LOGIN
- [ ] `app/dashboard/page.tsx` - Update to use API_ENDPOINTS.STUDENTS.DASHBOARD
- [ ] `app/dashboard/courses/page.tsx` - Update to use API_ENDPOINTS.STUDENTS.COURSES
- [ ] `app/dashboard/schedule/page.tsx` - Update to use API_ENDPOINTS.STUDENTS.SCHEDULE
- [ ] `app/dashboard/grades/page.tsx` - Update to use API_ENDPOINTS.STUDENTS.GRADES
- [ ] `app/dashboard/assignments/page.tsx` - Update to use API_ENDPOINTS.STUDENTS.ASSIGNMENTS
- [ ] `app/dashboard/profile/page.tsx` - Update to use API_ENDPOINTS.AUTH.USER

#### Frontend Admin:
- [ ] `src/components/auth/LoginForm.tsx`
- [ ] `src/components/auth/LoginFormEnhanced.tsx`
- [ ] `src/app/dashboard/teachers/page.tsx`
- [ ] `src/app/dashboard/students/page.tsx`
- [ ] `src/app/dashboard/education-plans/page.tsx`
- [ ] `src/app/dashboard/student-orders/page.tsx`
- [ ] `src/components/single-event-edit-modal.tsx`
- [ ] `src/components/academic-schedule-edit-modal.tsx`

#### Backend API Files:
- [ ] `app/api/teachers.py` - Replace hardcoded DB connections (lines ~502, 644, 789)
- [ ] `app/api/class_schedule.py` - Replace hardcoded DB connection (line ~144)
- [ ] `app/api/academic_schedule.py` - Replace hardcoded DB connection (line ~18)
- [ ] `app/api/student_orders.py` - Replace hardcoded DB connection (line ~21)
- [ ] `app/api/student_groups.py` - Replace hardcoded DB connection (line ~21)
- [ ] `app/api/curriculum_simplified.py` - Replace hardcoded DB connection (line ~22)

### Medium Priority (Development Tools)

#### Backend Scripts:
- [ ] `analyze_schedule_conflicts.py`
- [ ] `cleanup_schedule_conflicts.py`
- [ ] `analyze_enrollment_migration.py`
- [ ] `update_enrollment_counts.py`
- [ ] `fix_enrollment_counts.py`
- [ ] `update_schedule_dates.py`

### Low Priority (Tests/Temporary Files)
- [ ] `test_student_auth.py`
- [ ] `test_schedule_api.py`
- [ ] `test_backend_endpoint.py`
- [ ] `test_frontend_endpoint.js`
- [ ] Migration scripts in `backend/migration/`

## Deployment Configuration

### Development Environment
1. Copy `.env.local.example` to `.env.local` in each frontend
2. Update values as needed for local development
3. Ensure backend `.env` is configured

### Production Environment
1. Set environment variables in deployment platform:
   ```
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   DB_PASSWORD=<secure-password>
   SECRET_KEY=<secure-secret-key>
   BACKEND_CORS_ORIGINS=https://teacher.yourdomain.com,https://student.yourdomain.com,https://admin.yourdomain.com
   ```

2. Update frontend build commands to use production env:
   ```bash
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com bun run build
   ```

## Security Best Practices

1. **Never commit `.env.local` files** - They are in `.gitignore`
2. **Never hardcode credentials** - Always use environment variables
3. **Use different secrets** for each environment (dev, staging, prod)
4. **Rotate secrets regularly** - Especially after team member changes
5. **Use strong passwords** - Never use "1111" or simple passwords in production
6. **Restrict CORS** - Only allow specific domains in production

## Testing Configuration

To verify configuration is working:

### Frontend:
```bash
# In frontend directory
echo "API URL: $NEXT_PUBLIC_API_URL"
bun run dev
# Check browser console for any hardcoded URLs
```

### Backend:
```bash
# In backend directory
python -c "from app.core.config import get_settings; s = get_settings(); print(f'DB: {s.DB_NAME}, CORS: {s.BACKEND_CORS_ORIGINS}')"
```

## Rollback Plan

If issues occur:
1. Revert to using hardcoded values temporarily
2. Ensure `.env` files exist and are properly configured
3. Check environment variable names match code
4. Verify no typos in environment variable names

## Future Improvements

1. **Database Connection Pool** - Create centralized DB connection utility
2. **API Client Library** - Create axios wrapper with built-in auth
3. **Configuration Validation** - Add startup checks for required env vars
4. **Secrets Management** - Use HashiCorp Vault or AWS Secrets Manager
5. **Multi-Environment Support** - Different configs for dev/staging/prod

## Questions & Support

For questions about configuration:
1. Check this document first
2. Verify `.env.local.example` files for available options
3. Review `lib/api-config.ts` for API endpoint structure
4. Check `backend/app/core/config.py` for backend settings

---

Last Updated: October 12, 2025
