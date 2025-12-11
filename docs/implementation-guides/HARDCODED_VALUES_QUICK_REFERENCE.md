# Quick Reference: Hardcoded Values Removal

## Environment Variables

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1
NODE_ENV=development
```

### Backend (.env)
```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_NAME=lms
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Code Patterns

### Frontend - API Calls

❌ **DON'T**:
```typescript
fetch('http://localhost:8000/api/v1/teachers/me/dashboard')
```

✅ **DO**:
```typescript
import { API_ENDPOINTS, authFetch } from '@/lib/api-config';
authFetch(API_ENDPOINTS.TEACHERS.DASHBOARD)
```

### Frontend - Login

❌ **DON'T**:
```typescript
axios.post('http://localhost:8000/api/v1/auth/login', data)
```

✅ **DO**:
```typescript
import { API_ENDPOINTS } from '@/lib/api-config';
axios.post(API_ENDPOINTS.AUTH.LOGIN, data)
```

### Backend - Database Connection

❌ **DON'T**:
```python
conn = psycopg2.connect(
    password="1111",
    database="lms"
)
```

✅ **DO**:
```python
from app.core.config import get_settings
settings = get_settings()
conn = psycopg2.connect(
    password=settings.DB_PASSWORD,
    database=settings.DB_NAME
)
```

## Available API Endpoints

### Teachers
```typescript
API_ENDPOINTS.TEACHERS.ME
API_ENDPOINTS.TEACHERS.DASHBOARD
API_ENDPOINTS.TEACHERS.COURSES
API_ENDPOINTS.TEACHERS.STUDENTS
API_ENDPOINTS.TEACHERS.SCHEDULE
API_ENDPOINTS.TEACHERS.SCHEDULE_CALENDAR
API_ENDPOINTS.TEACHERS.GRADES
```

### Students
```typescript
API_ENDPOINTS.STUDENTS.ME
API_ENDPOINTS.STUDENTS.DASHBOARD
API_ENDPOINTS.STUDENTS.COURSES
API_ENDPOINTS.STUDENTS.SCHEDULE
API_ENDPOINTS.STUDENTS.GRADES
API_ENDPOINTS.STUDENTS.ASSIGNMENTS
```

### Auth
```typescript
API_ENDPOINTS.AUTH.LOGIN
API_ENDPOINTS.AUTH.LOGOUT
API_ENDPOINTS.AUTH.USER
```

## Utility Functions

```typescript
// Build URL with query params
import { buildUrl } from '@/lib/api-config';
const url = buildUrl(API_ENDPOINTS.TEACHERS.SCHEDULE, { 
  day: 'Monday' 
});
// Result: http://localhost:8000/api/v1/teachers/me/schedule?day=Monday

// Authenticated fetch (auto-includes token)
import { authFetch } from '@/lib/api-config';
const response = await authFetch(url);

// Get auth headers
import { getAuthHeaders } from '@/lib/api-config';
const headers = getAuthHeaders();
```

## Testing

```bash
# Check if env vars are loaded
echo $NEXT_PUBLIC_API_URL

# Test backend config
cd backend && python -c "from app.core.config import get_settings; print(get_settings().DB_NAME)"

# Run detection script
python3 detect_hardcoded_values.py
```

## Files to Update

### Priority 1 (Teacher Frontend)
- [ ] app/dashboard/page.tsx
- [ ] app/dashboard/courses/page.tsx
- [ ] app/dashboard/students/page.tsx
- [ ] app/dashboard/attendance/page.tsx
- [ ] app/dashboard/grades/page.tsx
- [ ] app/dashboard/schedule/page.tsx

### Priority 2 (Student Frontend)
- [ ] app/dashboard/page.tsx
- [ ] app/dashboard/courses/page.tsx
- [ ] app/dashboard/schedule/page.tsx
- [ ] app/dashboard/grades/page.tsx
- [ ] app/dashboard/assignments/page.tsx
- [ ] app/dashboard/profile/page.tsx

### Priority 3 (Backend API)
- [ ] app/api/teachers.py
- [ ] app/api/class_schedule.py
- [ ] app/api/academic_schedule.py
- [ ] app/api/student_orders.py

---
For full details: See HARDCODED_VALUES_REMOVAL_GUIDE.md
