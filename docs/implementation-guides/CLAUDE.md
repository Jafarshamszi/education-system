# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

University Learning Management System (LMS) - A comprehensive education management platform built with FastAPI (backend) and Next.js 15 (frontend). The system manages students, teachers, courses, enrollments, grading, attendance, and academic operations across multiple organizational units.

**Key Characteristics:**
- Multi-campus university support with hierarchical organization structure
- Multilingual support (Azerbaijani, Russian, English) using JSONB fields
- UUID-based database schema in PostgreSQL
- Role-based access control (RBAC) with hierarchical permissions
- Real-time session management with JWT authentication

## Development Commands

### Backend Commands

**Environment Setup:**
```bash
# Activate virtual environment (REQUIRED - do not create new venv)
source /home/axel/Developer/Education-system/.venv/bin/python

# Install dependencies (if needed)
pip install -r requirements.txt
```

**Running the Server:**
```bash
cd backend

# Development server (user runs this - you don't need to)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Testing:**
```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest --cov=app tests/

# Run single test
pytest tests/test_auth.py::test_login -v
```

**Database Operations:**
```bash
cd backend

# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

**Code Quality:**
```bash
cd backend

# Format code
black app/

# Sort imports
isort app/

# Type checking
mypy app/

# Linting
flake8 app/
```

### Frontend Commands

**Running Development Server:**
```bash
cd frontend

# Development server (user runs this - you don't need to)
bun dev

# Or with npm
npm run dev
```

**Building:**
```bash
cd frontend

# Production build
bun run build

# Start production server
bun run start
```

**Linting:**
```bash
cd frontend

# Run ESLint
bun run lint
# or
npm run lint
```

## Architecture Overview

### Backend Architecture

**Technology Stack:**
- FastAPI 0.104.1 - Modern async web framework
- SQLAlchemy 2.0.23 - ORM with async support
- PostgreSQL (with asyncpg + psycopg2-binary) - Primary database (DB: `lms`)
- Pydantic 2.4.2 - Data validation
- JWT + bcrypt - Authentication and password hashing

**Project Structure:**
```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization & middleware
│   ├── api/                 # API route handlers
│   │   ├── __init__.py      # Main API router registration
│   │   ├── auth.py          # Login, logout, token refresh
│   │   ├── teachers.py      # Teacher management (uses staff_members table)
│   │   ├── students.py      # Student operations
│   │   ├── users.py         # User CRUD
│   │   └── [other endpoints]
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py          # User accounts
│   │   ├── person.py        # Personal information
│   │   ├── staff_member.py  # Teaching staff (replaces old teachers)
│   │   ├── student.py       # Student records
│   │   └── organization_unit.py  # Institutional structure
│   ├── schemas/             # Pydantic request/response models
│   ├── core/
│   │   ├── config.py        # Settings (loads from .env)
│   │   └── database.py      # DB connection management
│   ├── auth/
│   │   ├── dependencies.py  # Auth dependency injection (RBAC)
│   │   ├── jwt_handler.py   # Token creation/verification
│   │   └── password.py      # bcrypt password hashing
│   └── utils/               # Helper functions
└── tests/                   # Pytest test suite
```

**Database Connection:**
- **Primary DB:** `lms` (PostgreSQL) - modern UUID-based schema
- **Old DB:** `edu` (DEPRECATED - DO NOT USE)
- All endpoints MUST use `os.getenv("DB_NAME", "lms")` for database name
- Connection pattern in API endpoints:
  ```python
  def get_db_connection():
      return psycopg2.connect(
          host="localhost",
          database=os.getenv("DB_NAME", "lms"),  # ALWAYS use this pattern
          user="postgres",
          password="1111",
          cursor_factory=RealDictCursor
      )
  ```

**Key Database Tables (LMS Schema):**
- `users` - User accounts with authentication (UUID primary keys)
- `persons` - Personal demographic data (linked to users via user_id)
- `staff_members` - Teaching staff (NEW - replaces old "teachers" table)
  - Uses UUID keys
  - Links: user_id → users.id → persons.user_id
  - Fields: employee_number, position_title, organization_unit_id
- `students` - Student-specific data
- `organization_units` - Hierarchical institutional structure (faculties, departments)
- `course_offerings` - Courses offered in specific terms
- `course_enrollments` - Student enrollment records
- `grades` - Assessment grades
- `attendance_records` - Class attendance tracking

**Authentication Flow:**
1. POST `/api/v1/auth/login` with username/password
2. System verifies with bcrypt (passwords stored as bcrypt hashes starting with `$2`)
3. Returns JWT access_token (30min) + refresh_token (7 days)
4. Client includes `Authorization: Bearer {token}` header
5. `get_current_user` dependency validates JWT and loads user
6. RBAC checks role permissions via `user_groups` relationships

**API Response Patterns:**
- List endpoints return: `{count: int, total_pages: int, results: List[...]}`
- Detail endpoints return: Single object or 404
- Errors: `{detail: string}` with appropriate HTTP status code

### Frontend Architecture

**Technology Stack:**
- Next.js 15.5.3 with React 19 - App Router architecture
- TypeScript - Type safety throughout
- Tailwind CSS 4 + shadcn/ui - Styling and component library
- Axios - HTTP client for API communication
- React Hook Form + Zod - Form validation
- next-themes - Dark/light mode support

**Project Structure:**
```
frontend/src/
├── app/
│   ├── layout.tsx           # Root layout with providers
│   ├── page.tsx             # Landing page
│   ├── login/               # Login page (public)
│   ├── dashboard/           # Protected dashboard routes
│   │   ├── teachers/        # Teacher management UI
│   │   ├── students/        # Student management UI
│   │   ├── education-plans/ # Curriculum management
│   │   └── [other modules]
│   └── requests/            # Request management
├── components/
│   ├── ui/                  # shadcn/ui components
│   ├── layout/              # Layout components (Sidebar, Header)
│   └── [feature components]
├── lib/
│   ├── api.ts               # Axios configuration
│   └── utils.ts             # Helper utilities
├── types/                   # TypeScript type definitions
│   └── teachers.ts          # Teacher API types (matches backend)
└── hooks/                   # Custom React hooks
```

**API Integration Pattern:**
```typescript
// Axios instance configured in lib/api.ts
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
  headers: { 'Content-Type': 'application/json' }
});

// Request interceptor adds JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Always handle pagination response format
const response = await api.get('/teachers/', { params: { page: 1, per_page: 25 } });
const { count, total_pages, results } = response.data;
```

**Defensive Frontend Patterns:**
```typescript
// Always use optional chaining and nullish coalescing
setData(Array.isArray(response.data?.results) ? response.data.results : []);

// Defensive rendering
{!data || data.length === 0 ? (
  <EmptyState />
) : (
  data.map(item => <ItemCard key={item.id} {...item} />)
)}
```

## Critical Implementation Notes

### Database Schema Migration (COMPLETED)

The system migrated from old "edu" database to new "lms" database:

**Key Changes:**
- Old: BigInteger IDs → New: UUID primary keys
- Old: `teachers` table → New: `staff_members` table
- Field renames: `firstname` → `first_name`, `lastname` → `last_name`, `patronymic` → `middle_name`
- JSONB fields for multilingual content (e.g., `{"az": "...", "en": "...", "ru": "..."}`)

**When Working with Teachers:**
- Use `StaffMember` model, NOT old `Teacher` model
- Join pattern: `staff_members → users (via user_id) → persons (via user_id)`
- Position info stored in JSONB: `position_title` field

### Password Security (IMPLEMENTED)

All passwords MUST be bcrypt hashed:
```python
from app.auth.password import hash_password, verify_password

# Creating user
user.password_hash = hash_password(plain_password)

# Verifying login
if not verify_password(plain_password, user.password_hash):
    raise HTTPException(status_code=401, detail="Invalid password")

# Checking if already hashed
if password_hash.startswith('$2'):
    # Already bcrypt hashed
```

### Common Pitfalls to Avoid

1. **DO NOT hardcode database name to "edu"** - always use `os.getenv("DB_NAME", "lms")`
2. **DO NOT use old Teacher model** - use StaffMember model for staff queries
3. **DO NOT forget pagination format** - list endpoints return `{count, results}` not just array
4. **DO NOT skip null checks in frontend** - always use optional chaining for API responses
5. **DO NOT store plain text passwords** - always hash with bcrypt before saving
6. **DO NOT create new virtual environments** - use existing `.venv` in project root

### Adding New API Endpoints

1. Create endpoint file in `backend/app/api/your_endpoint.py`:
   ```python
   from fastapi import APIRouter, Depends
   from app.auth.dependencies import get_current_user

   router = APIRouter(prefix="/your-resource", tags=["your-resource"])

   @router.get("/")
   async def list_items(user = Depends(get_current_user)):
       # Implementation
       return {"count": len(items), "results": items}
   ```

2. Register in `backend/app/api/__init__.py`:
   ```python
   from .your_endpoint import router as your_router
   api_router.include_router(your_router)
   ```

3. Create TypeScript types in `frontend/src/types/your_resource.ts`

4. Add API calls in frontend using axios with auth interceptor

### Testing Strategy

**Backend Tests:**
- Unit tests for models, schemas, utilities
- Integration tests for API endpoints with test database
- Use pytest fixtures for test data (see `tests/conftest.py`)
- Mock external dependencies when appropriate

**Testing User Roles:**
```python
# Create test user with specific role
test_user = create_test_user(role="ADMIN")
headers = {"Authorization": f"Bearer {get_token_for_user(test_user)}"}
response = client.get("/api/v1/protected-resource", headers=headers)
```

## Environment Configuration

**Backend `.env` file location:** `/home/axel/Developer/Education-system/backend/.env`

Required variables:
```bash
ENVIRONMENT=development
DEBUG=True
PROJECT_NAME="Education Management System"
API_PREFIX=/api/v1

# Database (CRITICAL - always use 'lms')
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=1111
DB_NAME=lms

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Frontend environment:** No `.env` file needed - API URL hardcoded to `http://127.0.0.1:8000`

## API Documentation

When backend server is running:
- **Swagger UI:** http://127.0.0.1:8000/api/v1/docs
- **ReDoc:** http://127.0.0.1:8000/api/v1/redoc
- **Health Check:** http://127.0.0.1:8000/health

## Code Style Conventions

### Backend (Python)
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Docstrings for all public functions (Google style)
- Async/await for I/O operations where possible
- Use Pydantic models for request/response validation

### Frontend (TypeScript)
- Use functional components with hooks
- Proper TypeScript typing (avoid `any`)
- Component files use PascalCase
- Use `const` over `let` where possible
- Destructure props in component parameters

## Git Workflow

Current branch structure:
- `main` - Production-ready code
- `Development` - Active development branch (currently checked out)

**When committing:**
- Write clear, descriptive commit messages
- Reference issue numbers if applicable
- Keep commits focused on single changes

## Recent Major Changes

1. **Password Migration** - All 6,491 user passwords migrated from plain text to bcrypt hashes
2. **Teachers Endpoint Rewrite** - Complete rewrite to use `staff_members` table with UUID schema
3. **Database Connection Fix** - Fixed 8 endpoints that were using deprecated "edu" database
4. **Frontend Type Safety** - Added comprehensive null checks and TypeScript types
5. **API Router Update** - Switched from old `teachers_comprehensive_router` to new `teachers_router`

## Performance Considerations

- Database queries use connection pooling (SQLAlchemy handles this)
- Frontend implements pagination for large datasets (default: 25 items per page)
- Use `LIMIT` and `OFFSET` in database queries for pagination
- Indexes exist on foreign key columns for join performance

## Security Notes

- All passwords stored as bcrypt hashes (cost factor 12)
- JWT tokens expire after 30 minutes (access) / 7 days (refresh)
- CORS configured for localhost:3000-3004 only
- SQL injection prevented via parameterized queries (psycopg2)
- XSS protection via React's automatic escaping

## Troubleshooting

**"Database connection failed":**
- Check PostgreSQL is running: `pg_ctl status`
- Verify DB name is "lms" not "edu"
- Check credentials in .env file

**"404 Not Found on API endpoint":**
- Verify endpoint registered in `app/api/__init__.py`
- Check prefix matches route definition
- Ensure backend server restarted after code changes

**"Frontend not fetching data":**
- Check browser network tab for actual error response
- Verify API response format matches TypeScript types
- Check JWT token in localStorage hasn't expired
- Ensure pagination format: `{count, results}` not just array

**"User cannot login":**
- Verify password is bcrypt hashed in database (starts with `$2`)
- Check username exists in `users` table
- Verify user `is_active` is true

## Database Schema Notes

The LMS database uses a UUID-based schema with the following conventions:
- All primary keys are UUIDs (not integers)
- Soft deletes: `is_active` or `active` boolean column (don't actually DELETE)
- Timestamps: `created_at` and `updated_at` on most tables
- JSONB for multilingual content: `{"az": "text", "en": "text", "ru": "text"}`
- Foreign keys use `_id` suffix (e.g., `user_id`, `organization_unit_id`)

## Additional Resources

- PostgreSQL documentation: https://www.postgresql.org/docs/15/
- FastAPI documentation: https://fastapi.tiangolo.com/
- Next.js documentation: https://nextjs.org/docs
- SQLAlchemy 2.0 documentation: https://docs.sqlalchemy.org/en/20/
