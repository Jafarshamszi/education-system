# Complete Event Endpoints Migration Report

## Overview
This document details the comprehensive migration of all academic schedule event endpoints from the old database structure (`academic_schedule_details`) to the new database structure (`calendar_events`).

## Changes Summary

### Phase 3: Event Management Endpoints Migration

All event CRUD endpoints have been updated to use the new `calendar_events` table instead of the legacy `academic_schedule_details` table.

---

## 1. CREATE Event Endpoint

**Endpoint:** `POST /api/v1/academic-schedule/events`

### Model Changes: EventCreate

**Old Structure:**
```python
class EventCreate(BaseModel):
    academic_schedule_id: str
    type_id: str
    start_date: str  # Format: DD/MM/YYYY
    end_date: Optional[str] = None  # Format: DD/MM/YYYY
```

**New Structure:**
```python
class EventCreate(BaseModel):
    academic_term_id: str  # UUID of the academic term
    event_type: str  # 'academic', 'exam', 'registration', 'holiday'
    title: dict  # JSONB with multilingual titles
    start_date: str  # Format: ISO 8601 or DD/MM/YYYY
    end_date: Optional[str] = None  # Format: ISO 8601 or DD/MM/YYYY
    is_mandatory: Optional[bool] = True
    description: Optional[dict] = None  # JSONB multilingual
```

### Function Changes

**Old Implementation:**
- Generated sequential integer IDs
- Inserted into `academic_schedule_details` table
- Used `type_id` for event classification
- Hardcoded `create_user_id = 100000000`
- Only supported DD/MM/YYYY date format

**New Implementation:**
- Generates UUID for new events
- Inserts into `calendar_events` table
- Uses `event_type` enum ('academic', 'exam', 'registration', 'holiday')
- Supports both ISO 8601 and DD/MM/YYYY date formats
- Stores multilingual titles and descriptions as JSONB
- Properly handles `created_at` and `updated_at` timestamps

**Request Example:**
```json
{
  "academic_term_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "academic",
  "title": {
    "az": "Yaz semestrinin başlanğıcı",
    "ru": "Начало весеннего семестра",
    "en": "Spring semester start"
  },
  "start_date": "2025-02-16T00:00:00+04:00",
  "end_date": "2025-02-16T00:00:00+04:00",
  "is_mandatory": true,
  "description": {
    "az": "İlk gün",
    "ru": "Первый день",
    "en": "First day"
  }
}
```

---

## 2. UPDATE Event Endpoint

**Endpoint:** `PUT /api/v1/academic-schedule/events/{event_id}`

### Model Changes: EventUpdate

**Old Structure:**
```python
class EventUpdate(BaseModel):
    start_date: Optional[str] = None  # Format: DD/MM/YYYY
    end_date: Optional[str] = None  # Format: DD/MM/YYYY
```

**New Structure:**
```python
class EventUpdate(BaseModel):
    start_date: Optional[str] = None  # Format: ISO 8601 or DD/MM/YYYY
    end_date: Optional[str] = None  # Format: ISO 8601 or DD/MM/YYYY
```

### Function Changes

**Old Implementation:**
- Updated `academic_schedule_details` table
- Used `start_date` and `end_date` columns (text format)
- Updated `update_date` and `update_user_id`
- Only supported DD/MM/YYYY format

**New Implementation:**
- Updates `calendar_events` table
- Uses `start_datetime` and `end_datetime` columns (timestamp)
- Updates `updated_at` timestamp automatically
- Supports both ISO 8601 and DD/MM/YYYY formats with `parse_date()` helper
- Removed obsolete `update_user_id` field

**Request Example:**
```json
{
  "start_date": "2025-03-01T00:00:00+04:00",
  "end_date": "2025-03-01T00:00:00+04:00"
}
```

**Backward Compatibility:**
Also accepts legacy format:
```json
{
  "start_date": "01/03/2025",
  "end_date": "01/03/2025"
}
```

---

## 3. DELETE Event Endpoint

**Endpoint:** `DELETE /api/v1/academic-schedule/events/{event_id}`

### Changes

**Old Implementation:**
```python
# Check if event exists
cursor.execute("SELECT id FROM academic_schedule_details WHERE id = %s", (event_id,))

# Delete the event
cursor.execute("DELETE FROM academic_schedule_details WHERE id = %s", (event_id,))
```

**New Implementation:**
```python
# Check if event exists in calendar_events
cursor.execute("SELECT id FROM calendar_events WHERE id = %s", (event_id,))

# Delete the event from calendar_events
cursor.execute("DELETE FROM calendar_events WHERE id = %s", (event_id,))
```

**Behavior:**
- Returns 404 if event not found
- Returns 200 with success message if deleted
- Properly handles database errors with rollback

---

## Date Format Support

All event endpoints now support **dual date format parsing**:

### ISO 8601 Format (Primary)
- **Format:** `YYYY-MM-DDTHH:MM:SS±HH:MM`
- **Example:** `2025-02-16T00:00:00+04:00`
- **Usage:** Default format returned by API and expected from modern clients

### DD/MM/YYYY Format (Legacy)
- **Format:** `DD/MM/YYYY`
- **Example:** `16/02/2025`
- **Usage:** Backward compatibility with old data and clients

### Parse Logic
```python
def parse_date(date_str):
    if not date_str:
        return None
    # Try ISO 8601 format first
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        # Try DD/MM/YYYY format
        try:
            day, month, year = date_str.split('/')
            return datetime(int(year), int(month), int(day))
        except:
            return None
```

---

## Database Schema Comparison

### Old Table: academic_schedule_details

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Sequential ID |
| academic_schedule_id | integer | Foreign key to edu_years |
| type_id | integer | Foreign key to event types |
| start_date | text | Format: DD/MM/YYYY |
| end_date | text | Format: DD/MM/YYYY |
| create_date | timestamp | Creation timestamp |
| create_user_id | integer | Creator user ID |
| update_date | timestamp | Last update timestamp |
| update_user_id | integer | Last updater user ID |
| active | integer | 0/1 flag |

### New Table: calendar_events

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | UUID primary key |
| academic_term_id | uuid | Foreign key to academic_terms |
| event_type | text | Enum: academic/exam/registration/holiday |
| title | jsonb | Multilingual titles (az, ru, en) |
| description | jsonb | Multilingual descriptions |
| start_datetime | timestamp | Start date/time with timezone |
| end_datetime | timestamp | End date/time with timezone |
| is_mandatory | boolean | Mandatory flag |
| created_at | timestamp | Creation timestamp |
| updated_at | timestamp | Last update timestamp |

---

## Frontend Integration

### Before (Old Format)
```typescript
// Sent to API
const formatDateForAPI = (date: Date) => {
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
};

// Received from API - expected DD/MM/YYYY
const parseDate = (dateStr: string) => {
  const [day, month, year] = dateStr.split('/');
  return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
};
```

### After (ISO 8601 Format)
```typescript
// Sent to API
const formatDateForAPI = (date: Date) => {
  return date.toISOString();
};

// Received from API - handles both formats
const parseDate = (dateStr: string) => {
  if (!dateStr) return undefined;
  
  // Handle ISO 8601 format (primary)
  if (dateStr.includes('T') || dateStr.includes('-')) {
    const date = new Date(dateStr);
    return isNaN(date.getTime()) ? undefined : date;
  }
  
  // Handle DD/MM/YYYY format (legacy)
  const [day, month, year] = dateStr.split('/');
  if (!day || !month || !year) return undefined;
  return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
};
```

---

## Migration Status

### ✅ Completed Endpoints

1. **GET /api/v1/academic-schedule/stats** - Uses `calendar_events` table
2. **GET /api/v1/academic-schedule/details** - Returns events from `calendar_events`
3. **POST /api/v1/academic-schedule/events** - Creates events in `calendar_events`
4. **PUT /api/v1/academic-schedule/events/{event_id}** - Updates events in `calendar_events`
5. **DELETE /api/v1/academic-schedule/events/{event_id}** - Deletes events from `calendar_events`

### Database Status

- **Old database (edu):** 327 events in `academic_schedule_details` (legacy, read-only)
- **New database (lms):** 84 events in `calendar_events` (active, 2020-2025)
- **Migration script:** `backend/migrate_academic_schedule.py` (one-time use, completed)

---

## Testing Verification

### Test Create Event
```bash
curl -X POST http://localhost:8000/api/v1/academic-schedule/events \
  -H "Content-Type: application/json" \
  -d '{
    "academic_term_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "academic",
    "title": {"az": "Test Event", "en": "Test Event"},
    "start_date": "2025-03-01T00:00:00+04:00",
    "is_mandatory": true
  }'
```

### Test Update Event
```bash
curl -X PUT http://localhost:8000/api/v1/academic-schedule/events/{event_id} \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-03-15T00:00:00+04:00",
    "end_date": "2025-03-15T00:00:00+04:00"
  }'
```

### Test Delete Event
```bash
curl -X DELETE http://localhost:8000/api/v1/academic-schedule/events/{event_id}
```

---

## Breaking Changes

### API Request Changes

**CREATE endpoint:**
- ❌ Removed: `academic_schedule_id` (use `academic_term_id` instead)
- ❌ Removed: `type_id` (use `event_type` string instead)
- ✅ Added: `title` (JSONB multilingual required)
- ✅ Added: `is_mandatory` (boolean, default true)
- ✅ Added: `description` (JSONB multilingual optional)

### API Response Changes

**Date format:**
- ❌ Old: `"start_date": "16/02/2025"`
- ✅ New: `"start_date": "2025-02-16T00:00:00+04:00"`

**Event type:**
- ❌ Old: `"type_id": 110000245`
- ✅ New: `"event_type": "academic"`

**Title:**
- ❌ Old: Single string
- ✅ New: `{"az": "...", "ru": "...", "en": "..."}`

---

## Rollback Plan

If issues occur, the old `academic_schedule_details` table remains intact in the `edu` database with all 327 original events. To rollback:

1. Revert `backend/app/api/academic_schedule.py` to previous version
2. Update frontend to use DD/MM/YYYY format only
3. Point queries back to `academic_schedule_details` table

**Note:** The old table is in a different database, so a full rollback would require updating connection strings.

---

## Next Steps

### Recommended Actions

1. **Test all event operations in staging:**
   - Create event with ISO 8601 dates
   - Create event with DD/MM/YYYY dates (backward compatibility)
   - Update existing event
   - Delete event
   - Verify frontend displays dates correctly

2. **Monitor for issues:**
   - Check server logs for date parsing errors
   - Verify all 84 migrated events display correctly
   - Test event editing in frontend modal

3. **Documentation updates:**
   - Update API documentation with new schemas
   - Document event_type enum values
   - Add examples for JSONB title/description format

4. **Performance optimization:**
   - Add database indexes on `academic_term_id` and `event_type`
   - Consider caching frequently accessed events

---

## Summary

✅ **All event management endpoints migrated to new database structure**
✅ **Dual date format support (ISO 8601 primary, DD/MM/YYYY legacy)**
✅ **JSONB multilingual support for titles and descriptions**
✅ **UUID-based event IDs instead of sequential integers**
✅ **Frontend updated to handle ISO 8601 format**
✅ **84 events successfully migrated and operational**

**Status:** Migration complete and ready for testing.
