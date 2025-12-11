# COMPLETE MIGRATION SOLUTION - IMPLEMENTATION GUIDE

## Status Summary

### ✅ COMPLETED TASKS
1. **Root Cause Analysis**: Identified that `journal.course_id` → `course.id` (not education_plan)
2. **Database Connection Manager**: Auto-fallback system implemented and tested
3. **Schema Updates**: Added tracking columns (old_course_id, old_journal_id)
4. **Audit Logging System**: Created comprehensive logging tables
5. **Database Optimization**: Added indexes and configured autovacuum

### 📊 MIGRATION STATUS
- **Old Database**: 6,064 courses with 510,269 enrollments
- **New Database**: 1,581 courses (26.3%) with 94,558 enrollments (18.5%)
- **Missing**: 4,439 courses (73.7%) and 415,711 enrollments (81.5%)

### 🎯 DATA MODEL DISCOVERED
```
Old Database Structure:
journal (enrollments)
  ├─ course_id → course.id (NOT education_plan!)
  └─ student_id → students.id

course table
  ├─ education_plan_subject_id
  ├─ semester_id
  ├─ education_year_id
  └─ Contains 6,064 distinct courses referenced by journal

New Database Structure:
course_enrollments
  ├─ course_offering_id → course_offerings.id
  └─ student_id → students.id

course_offerings
  ├─ course_id → courses.id
  └─ academic_term_id → academic_terms.id
```

## Implementation Steps

### STEP 1: Schema Updates (✅ COMPLETED)

Run the SQL script:
```bash
psql -U postgres -h localhost -d lms -f backend/complete_migration_plan.sql
```

**What it does:**
- Adds `old_course_id` column to `course_offerings`
- Adds `old_journal_id` column to `course_enrollments`
- Creates `audit_logs` table for comprehensive logging
- Creates `user_sessions` table for session tracking
- Creates `page_views` table for page view analytics
- Adds indexes for performance
- Creates helper functions for logging

**Verification:**
```sql
-- Check tracking columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'course_offerings' AND column_name = 'old_course_id';

-- Check audit tables
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('audit_logs', 'user_sessions', 'page_views');
```

### STEP 2: Data Migration Script

**File**: `backend/complete_data_migration.py`

**Before running**, you need to:

1. **Map old courses to new courses** - The script needs proper mapping logic:
   - Old `course.education_plan_subject_id` → needs mapping to actual courses
   - Old `course.semester_id` → new `academic_terms.id`
   - This requires domain knowledge of your course structure

2. **Verify student mappings exist**:
   ```sql
   SELECT COUNT(*) FROM students WHERE metadata->>'old_student_id' IS NOT NULL;
   ```

**Running the migration:**
```bash
cd backend
python3 complete_data_migration.py
```

**What it does:**
1. Loads student ID mappings (old → new UUIDs)
2. Loads existing course mappings
3. Migrates 4,439 missing courses
4. Migrates 415,711 missing enrollments
5. Updates enrollment counts
6. Generates final report

### STEP 3: Implement Audit Logging in Application

#### Django (backend/django_project/settings.py)

Add middleware:
```python
MIDDLEWARE = [
    ...
    'backend.middleware.audit_logging.AuditLoggingMiddleware',
]
```

Create middleware file (`backend/middleware/audit_logging.py`):
```python
import psycopg2
from django.utils.deprecation import MiddlewareMixin
from database.connection_manager import get_db_manager
import json

class AuditLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated:
            duration_ms = int((time.time() - request._start_time) * 1000)
            
            # Log to audit_logs table
            db_manager = get_db_manager()
            with db_manager.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO audit_logs (
                        user_id, username, action_type, request_path,
                        request_method, response_status, response_time_ms,
                        ip_address, user_agent, session_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(request.user.id),
                    request.user.username,
                    'page_view',
                    request.path,
                    request.method,
                    response.status_code,
                    duration_ms,
                    request.META.get('REMOTE_ADDR'),
                    request.META.get('HTTP_USER_AGENT'),
                    request.session.session_key
                ))
                conn.commit()
        
        return response
```

#### FastAPI (backend/fastapi_app/main.py)

Add middleware:
```python
from fastapi import FastAPI, Request
from database.connection_manager import get_db_manager
import time
import uuid

app = FastAPI()

@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Log request
    if hasattr(request.state, 'user'):
        duration_ms = int((time.time() - start_time) * 1000)
        
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO audit_logs (
                    user_id, username, action_type, request_path,
                    request_method, response_status, response_time_ms,
                    ip_address, user_agent
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(request.state.user.id),
                request.state.user.username,
                'api_request',
                str(request.url.path),
                request.method,
                response.status_code,
                duration_ms,
                request.client.host,
                request.headers.get('user-agent')
            ))
            conn.commit()
    
    return response
```

### STEP 4: Session Tracking

Create login endpoint that tracks sessions:

```python
from database.connection_manager import get_db_manager
import uuid

def user_login(username, password, request):
    # ... authenticate user ...
    
    # Create session record
    session_id = str(uuid.uuid4())
    
    db_manager = get_db_manager()
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_sessions (
                user_id, username, session_id, ip_address, user_agent
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user.id,
            username,
            session_id,
            request.META.get('REMOTE_ADDR'),
            request.META.get('HTTP_USER_AGENT')
        ))
        conn.commit()
    
    return session_id
```

### STEP 5: Database Optimization (✅ COMPLETED)

Already applied:
- ✅ Foreign key indexes
- ✅ Status/enum field indexes
- ✅ Date field indexes
- ✅ GIN indexes for JSONB columns
- ✅ Autovacuum configuration
- ✅ Table statistics updated

### STEP 6: Update Application to Use Connection Manager

#### Django Settings

Update `settings.py`:
```python
from database.connection_manager import get_db_manager

# Initialize database manager
db_manager = get_db_manager({
    'primary_database': 'lms',
    'fallback_database': 'edu',
    'host': 'localhost',
    'user': 'postgres',
    'password': '1111',
    'port': 5432
})

# Django doesn't use our connection manager for ORM,
# but we use it for custom queries
```

For custom queries:
```python
from database.connection_manager import get_db_manager

def get_student_data(student_id):
    db_manager = get_db_manager()
    with db_manager.get_connection(dict_cursor=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        return cur.fetchone()
```

#### FastAPI

Update `main.py`:
```python
from database.connection_manager import get_db_manager
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.db_manager = get_db_manager()
    yield
    # Shutdown
    # Connection manager handles cleanup

app = FastAPI(lifespan=lifespan)

# Dependency for routes
def get_db():
    db_manager = get_db_manager()
    with db_manager.get_connection(dict_cursor=True) as conn:
        yield conn
```

## Analytics Queries

### User Activity Analytics
```sql
-- Daily active users
SELECT 
    DATE(action_timestamp) as date,
    COUNT(DISTINCT user_id) as daily_active_users
FROM audit_logs
WHERE action_type = 'login'
GROUP BY DATE(action_timestamp)
ORDER BY date DESC;

-- Most viewed pages
SELECT 
    page_path,
    COUNT(*) as views,
    COUNT(DISTINCT user_id) as unique_visitors,
    AVG(time_on_page_seconds) as avg_time_seconds
FROM page_views
WHERE view_timestamp > NOW() - INTERVAL '30 days'
GROUP BY page_path
ORDER BY views DESC
LIMIT 20;

-- Session duration statistics
SELECT 
    AVG(session_duration_seconds) as avg_duration,
    MIN(session_duration_seconds) as min_duration,
    MAX(session_duration_seconds) as max_duration,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY session_duration_seconds) as median_duration
FROM user_sessions
WHERE logout_timestamp IS NOT NULL;

-- User actions by type
SELECT 
    action_type,
    COUNT(*) as action_count,
    COUNT(DISTINCT user_id) as unique_users
FROM audit_logs
WHERE action_timestamp > NOW() - INTERVAL '7 days'
GROUP BY action_type
ORDER BY action_count DESC;
```

## Monitoring and Maintenance

### Daily Monitoring Queries

```sql
-- Check migration completeness
SELECT 
    'Courses' as entity,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE old_course_id IS NOT NULL) as migrated,
    ROUND(COUNT(*) FILTER (WHERE old_course_id IS NOT NULL)::NUMERIC / COUNT(*) * 100, 2) as percent
FROM course_offerings
UNION ALL
SELECT 
    'Enrollments',
    COUNT(*),
    COUNT(*) FILTER (WHERE old_journal_id IS NOT NULL),
    ROUND(COUNT(*) FILTER (WHERE old_journal_id IS NOT NULL)::NUMERIC / COUNT(*) * 100, 2)
FROM course_enrollments;

-- Check database health
SELECT 
    current_database as database,
    current_setting('work_mem') as work_mem,
    current_setting('shared_buffers') as shared_buffers,
    current_setting('effective_cache_size') as effective_cache_size;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS external_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC
LIMIT 20;
```

## Troubleshooting

### Issue: Migration script fails with "no student mapping"
**Solution**: Ensure students have metadata with old_student_id:
```sql
SELECT COUNT(*) FROM students WHERE metadata->>'old_student_id' IS NOT NULL;
```

### Issue: Courses not migrating
**Solution**: Check if academic_terms exist:
```sql
SELECT * FROM academic_terms WHERE is_active = TRUE;
```
If none exist, create a default term.

### Issue: Database connection fails
**Solution**: Connection manager auto-fallback should handle this. Check logs:
```python
db_manager = get_db_manager()
status = db_manager.get_database_info()
print(status)
```

### Issue: Audit logs table growing too fast
**Solution**: Implement log rotation:
```sql
-- Archive old logs
CREATE TABLE audit_logs_archive AS
SELECT * FROM audit_logs
WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete archived logs
DELETE FROM audit_logs
WHERE created_at < NOW() - INTERVAL '90 days';
```

## Next Steps

1. **Run Schema Updates** ✅ DONE
2. **Customize Migration Script** - Add proper course/term mapping logic
3. **Run Data Migration** - Migrate 4,439 courses and 415,711 enrollments
4. **Implement Audit Logging** - Add middleware to Django and FastAPI
5. **Update Application** - Use connection manager in all database queries
6. **Test Failover** - Stop LMS database and verify automatic fallback to EDU
7. **Monitor Performance** - Use analytics queries to track system usage
8. **Set Up Backup** - Regular backups of both databases

## Time Estimate

- Schema setup: ✅ 30 minutes (DONE)
- Data migration: 2-3 hours (depending on course mapping complexity)
- Application integration: 2-3 hours
- Testing and verification: 1-2 hours
- **Total**: 5-8 hours

## Success Criteria

✅ Old tracking columns added
✅ Audit logging system created
✅ Database optimized with indexes
✅ Connection manager tested and working
⏳ All 6,064 courses migrated (currently 1,581)
⏳ All 510,269 enrollments migrated (currently 94,558)
⏳ Audit logging capturing user activity
⏳ Automatic failover working in production
