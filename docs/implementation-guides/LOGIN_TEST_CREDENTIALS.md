# Login Test Credentials

## Test Users for Login Testing

### Admin User (Simple)
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: admin@bbu.edu.az
- **Full Name**: Admin User
- **Status**: Active, Not Locked

### Existing User 1 (From Database)
- **Username**: `otahmadov`
- **Password**: `sinam20!9pro`
- **Email**: otahmadov@temp.bbu.edu.az
- **Full Name**: Orkhan Ahmadov
- **Status**: Active, Not Locked

### Existing User 2 (Created for Testing)
- **Username**: `5047UEA`
- **Password**: `sinam20!9pro`
- **Email**: 5047UEA@temp.bbu.edu.az
- **Full Name**: Test User 5047UEA
- **Status**: Active, Not Locked

## System Status

### Backend Status ✓
- **Database**: Connected successfully (PostgreSQL on localhost:5432/lms)
- **Tables**: All required tables exist (users, persons, etc.)
- **Total Users**: 6,490 users in database
- **Auth Endpoint**: `/api/v1/auth/login` - Working correctly
- **Token Generation**: JWT tokens are generated successfully
- **CORS**: Configured to allow localhost:3000-3004

### Frontend Status ✓
- **Login Form**: Located at `/frontend/src/components/auth/LoginForm.tsx`
- **API URL**: Correctly pointing to `http://localhost:8000/api/v1/auth/login`
- **Login Page**: Located at `/frontend/src/app/login/page.tsx`

## Verified Functionality

1. ✅ Backend imports and starts without errors
2. ✅ Database connection is working
3. ✅ Users table has data
4. ✅ Login endpoint is registered and accessible
5. ✅ JWT token generation works
6. ✅ Password verification works (plain text comparison)
7. ✅ Person data is fetched and included in response
8. ✅ Frontend form posts to correct endpoint

## How to Test Login

### Using the Frontend:
1. Start the backend server (you mentioned you do this)
2. Start the frontend (you mentioned you do this)
3. Navigate to `http://localhost:3000/login`
4. Enter username: `admin` and password: `admin123`
5. Click "Sign in"
6. Should redirect to `/dashboard`

### Using cURL (Backend Only):
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Expected response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": "2aafc97f-fa53-4cb8-8810-af6b9bbcb956",
  "username": "admin",
  "user_type": "UNKNOWN",
  "full_name": "Admin User",
  "email": "admin@bbu.edu.az"
}
```

## Security Status

### ✅ Password Security Implemented
- **All passwords are now hashed** using bcrypt (industry standard)
- Hash format: `$2b$12$...` (60 characters)
- Migration complete: 6,491/6,491 passwords hashed (100%)
- Login endpoint uses secure bcrypt verification
- See `PASSWORD_MIGRATION_COMPLETE.md` for details

### Note: User Type
- User type is currently hardcoded as "UNKNOWN" in the response
- TODO: Implement role/user type detection from database tables

### Database Configuration
- Host: localhost
- Port: 5432
- Database: lms
- User: postgres
- Password: 1111 (as per .env file)

## If Login Still Doesn't Work

Check the following:

1. **Backend Running**: Ensure backend is running on port 8000
   ```bash
   # Test if backend is accessible
   curl http://localhost:8000/health
   ```

2. **Frontend Running**: Ensure frontend is running on port 3000

3. **Browser Console**: Check for CORS errors or network errors

4. **Backend Logs**: Check for authentication errors or exceptions

5. **Network Tab**: Verify the POST request to `/api/v1/auth/login` is being sent

## System Architecture

```
Frontend (Next.js)          Backend (FastAPI)           Database (PostgreSQL)
Port: 3000                  Port: 8000                  Port: 5432
┌────────────────┐         ┌──────────────────┐        ┌──────────────┐
│  LoginForm     │ ──────> │  /auth/login     │ ────>  │  users       │
│  (React)       │ <────── │  (FastAPI)       │ <────  │  persons     │
└────────────────┘         └──────────────────┘        └──────────────┘
     Stores JWT                 Returns JWT               Validates
     in localStorage            + User Info               Credentials
```

## Additional Test Users

You can create more test users by running:
```python
/home/axel/Developer/Education-system/.venv/bin/python -c "
from app.core.database import SessionLocal
from app.models import User, Person
import uuid
from datetime import datetime

db = SessionLocal()
# Create your user here...
db.close()
"
```
