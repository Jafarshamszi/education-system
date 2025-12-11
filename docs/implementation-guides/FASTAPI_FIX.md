# FastAPI Configuration Fix

## Issue Encountered

When starting FastAPI with `uvicorn app.main:app --reload --port 8000`, the following error occurred:

```
pydantic_core._pydantic_core.ValidationError: 2 validation errors for Settings
DATABASE_URL
  Extra inputs are not permitted [type=extra_forbidden, ...]
DATABASE_SYNC_URL
  Extra inputs are not permitted [type=extra_forbidden, ...]
```

## Root Cause

The Pydantic v2 Settings class was configured to forbid extra fields, but the `.env` file contained `DATABASE_URL` and `DATABASE_SYNC_URL` fields that weren't defined in the Settings class.

## Solution Applied

### 1. Updated Settings Configuration (Pydantic v2 syntax)

**File:** `backend/app/core/config.py`

Changed from old Pydantic v1 Config class:
```python
class Config:
    env_file = ".env"
    case_sensitive = True
```

To Pydantic v2 `model_config`:
```python
model_config = SettingsConfigDict(
    env_file=".env",
    case_sensitive=True,
    extra="ignore"  # Ignore extra fields from .env file
)
```

### 2. Cleaned Up .env File

**File:** `backend/.env`

Removed redundant DATABASE_URL fields:
```bash
# REMOVED (redundant):
# DATABASE_URL=postgresql+asyncpg://postgres:1111@localhost:5432/lms
# DATABASE_SYNC_URL=postgresql://postgres:1111@localhost:5432/lms

# KEPT (these are used):
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=1111
DB_NAME=lms
```

The Settings class already generates these URLs via properties:
- `database_url` → `postgresql://postgres:1111@localhost:5432/lms`
- `async_database_url` → `postgresql+asyncpg://postgres:1111@localhost:5432/lms`

## Verification

✅ **Config loads successfully:**
```bash
python -c "from app.core.config import settings; print(f'Database: {settings.DB_NAME}')"
# Output: Database: lms
```

✅ **FastAPI starts successfully:**
```bash
uvicorn app.main:app --port 8000
# Output:
# INFO: Started server process
# INFO: Application startup complete.
# INFO: Uvicorn running on http://127.0.0.1:8000
```

## Current Status

🎉 **FastAPI is now working correctly with the LMS database!**

- Database: `lms` ✅
- Configuration: Pydantic v2 compatible ✅
- Server: Running successfully ✅

## How to Start

```bash
# From backend directory:
uvicorn app.main:app --reload --port 8000

# Or with the correct working directory:
cd backend && uvicorn app.main:app --reload --port 8000
```

The server will automatically connect to the `lms` database on localhost:5432.

---

*Fixed: October 9, 2025*
