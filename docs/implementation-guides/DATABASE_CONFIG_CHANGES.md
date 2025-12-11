# Database Configuration Changes - Quick Reference

## What Changed

The Education System backends have been updated to use the **new `lms` database** instead of the old `edu` database.

## Files Modified

| File | Old Value | New Value | Status |
|------|-----------|-----------|--------|
| `backend/django_backend/education_system/education_system/settings.py` | `NAME: 'edu'` | `NAME: 'lms'` | ✅ Updated |
| `backend/app/core/config.py` | `DB_NAME: "edu"` | `DB_NAME: "lms"` | ✅ Updated |
| `backend/.env` | ❌ Did not exist | ✅ Created with `lms` config | ✅ Created |
| `backend/.env.example` | `education_system` | `lms` | ✅ Updated |
| `.env.example` | `education_system` | `lms` | ✅ Updated |

## Database Connection Details

```
Host: localhost
Port: 5432
User: postgres
Password: 1111
Database: lms (was: edu)
```

## Verification Commands

### Check Django Configuration
```bash
grep "'NAME':" backend/django_backend/education_system/education_system/settings.py | head -1
# Should show: 'NAME': 'lms',
```

### Check FastAPI Configuration
```bash
grep "DB_NAME" backend/app/core/config.py
# Should show: DB_NAME: str = "lms"
```

### Test Database Connection
```bash
PGPASSWORD=1111 psql -U postgres -h localhost -d lms -c "SELECT current_database();"
# Should return: lms
```

## Starting the Backends

### Django Backend
```bash
cd backend/django_backend/education_system
python manage.py runserver 8001
```

### FastAPI Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Both will automatically connect to the `lms` database!

## Documentation

For full details, see: `BACKEND_CONFIGURATION_COMPLETE.md`
