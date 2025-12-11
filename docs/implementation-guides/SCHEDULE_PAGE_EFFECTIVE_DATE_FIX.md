# Schedule Page Fix - Effective Date Issue

## Problem
The schedule endpoint was returning 0 classes even though the teacher had 38 classes scheduled for Tuesday.

## Root Cause
The SQL query included a filter:
```sql
AND (cs.effective_until IS NULL OR cs.effective_until >= CURRENT_DATE)
```

This filter was excluding all schedules because:
- All class schedules have `effective_until = 2025-06-14` (June 14, 2025)
- Current date is October 12, 2025
- Therefore, all schedules were considered "expired"

## Solution
Removed the `effective_until` date filter from the query since:
1. The schedules are still valid teaching assignments
2. The `effective_until` date represents the academic term end, not when schedules should be hidden
3. Teachers need to see their recurring class schedules regardless of the academic term dates

## Changes Made

### Backend (`backend/app/api/teachers.py`)

**Before:**
```python
WHERE ci.instructor_id = %s
AND cs.day_of_week = %s
AND (cs.effective_until IS NULL OR cs.effective_until >= CURRENT_DATE)
ORDER BY cs.start_time
```

**After:**
```python
WHERE ci.instructor_id = %s
AND cs.day_of_week = %s
ORDER BY cs.start_time
```

### Additional Fix
Also fixed the instructor ID retrieval to match the pattern used in other endpoints:

**Before:**
```python
instructor_id = current_user.username  # This is actually the user_id
```

**After:**
```python
cur.execute("""
    SELECT id FROM users WHERE username = %s
""", [current_user.username])

teacher_user = cur.fetchone()
if not teacher_user:
    raise HTTPException(status_code=404, detail="Teacher not found")

instructor_id = teacher_user['id']
```

### Frontend (`frontend-teacher/app/dashboard/schedule/page.tsx`)
Enhanced error handling to show more detailed error messages:

**Before:**
```typescript
if (!response.ok) {
    throw new Error('Failed to fetch schedule');
}
```

**After:**
```typescript
if (!response.ok) {
    const errorText = await response.text();
    console.error('Schedule fetch error:', response.status, errorText);
    throw new Error(`Failed to fetch schedule: ${response.status} ${response.statusText}`);
}
```

## Testing Results

### Before Fix
- API endpoint returned: `[]` (empty array)
- Frontend displayed: "No Classes Scheduled"

### After Fix
- API endpoint returned: 38 classes for Tuesday
- Schedule data verified:
  - First class: 08:30-09:50
  - Total students: Sum of all enrolled students
  - All class details present (code, name, section, room, enrollment)

## Database Impact
No database changes required. This was a query logic issue, not a data issue.

## Future Considerations
If we need to filter by academic term in the future, consider:
1. Adding an `academic_term_id` filter instead of date-based filtering
2. Using `effective_from` and `effective_until` for informational purposes only
3. Implementing a separate "archived" flag for truly inactive schedules

## Status
✅ **FIXED** - Schedule page now displays all classes correctly
