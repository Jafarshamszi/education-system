# Schedule Conflict Resolution Plan

## Current Situation

### Problem Scale
- **10,591 conflict groups** found across all teachers
- **48,090 duplicate schedule records** need to be deleted
- Teachers have up to **25 classes scheduled at the same time**

### Example Conflict
```
Saturday 13:25-14:45: 25 conflicts for one teacher
  ✓ KEEP: SUBJ71807 (Enrollment: 213)  
  ✗ DELETE: 24 other courses (most with 0 enrollment)
```

### Root Cause
- No database constraints preventing schedule conflicts
- Data imported or created without validation
- Teachers assigned to multiple courses at exact same time slot

## Resolution Strategy

### Phase 1: Data Cleanup (REQUIRED FIRST)

**Action:** Run `cleanup_schedule_conflicts.py --execute`

**Logic:**
- For each conflicting time slot, keeps the class with **highest enrollment**
- Deletes all other classes at that time
- Preserves student enrollments for kept classes

**What Gets Deleted:**
- Classes with 0 enrollment (majority)
- Lower enrollment classes when conflicts exist
- Total: **48,090 duplicate schedule records**

**What Gets Kept:**
- Class with most enrolled students per time slot
- All unique (non-conflicting) schedules
- Student enrollment data remains intact

### Phase 2: Database Constraints (PREVENTS FUTURE CONFLICTS)

**Action:** Run SQL migration `add_schedule_conflict_prevention.sql`

**Prevents:**
1. ✅ Teacher teaching multiple classes at same time
2. ✅ Overlapping time slots for same instructor
3. ✅ Invalid time ranges (start_time >= end_time)

**Implementation:**
- PostgreSQL trigger function validates instructor conflicts
- Checks for time overlaps before INSERT/UPDATE
- Raises exception if conflict detected

### Phase 3: Backend Validation (API LEVEL)

**Action:** Add validation to FastAPI schedule endpoints

**Validates:**
- Schedule creation requests
- Schedule update requests
- Returns user-friendly error messages

## Execution Steps

### Step 1: Backup Database
```bash
pg_dump -U postgres -h localhost lms > lms_backup_before_cleanup_$(date +%Y%m%d).sql
```

### Step 2: Run Cleanup (Dry Run First)
```bash
cd /home/axel/Developer/Education-system/backend

# Review what will be deleted
python3 cleanup_schedule_conflicts.py

# Check the output carefully
# Verify that classes with high enrollment are kept
```

### Step 3: Execute Cleanup
```bash
# This will DELETE 48,090 records
python3 cleanup_schedule_conflicts.py --execute

# When prompted, type: DELETE
```

### Step 4: Apply Database Constraints
```bash
psql -U postgres -h localhost -d lms -f migrations/add_schedule_conflict_prevention.sql
```

### Step 5: Verify Results
```bash
# Check for remaining conflicts (should be 0)
python3 analyze_schedule_conflicts.py

# Test constraint works
psql -U postgres -h localhost -d lms
```

## Testing the Constraint

After applying the migration, test that conflicts are prevented:

```sql
-- This should FAIL with error message
INSERT INTO class_schedules (
    course_offering_id,
    day_of_week,
    start_time,
    end_time
) VALUES (
    (SELECT id FROM course_offerings LIMIT 1),
    1, -- Tuesday
    '08:30:00',
    '09:50:00'
);
-- If instructor already has class at this time, will raise:
-- ERROR: Schedule conflict: Instructor already has a class at this time
```

## Impact Assessment

### Before Cleanup
- ❌ Teachers have 20-25 classes at same time
- ❌ Calendar views show overlapping events
- ❌ Impossible schedules exist in database
- ❌ Data integrity compromised

### After Cleanup + Constraints
- ✅ Each teacher has maximum 1 class per time slot
- ✅ Calendar views show clean schedule
- ✅ Realistic, achievable schedules
- ✅ Database enforces business rules
- ✅ Cannot create conflicts through any interface

## Rollback Plan

If issues occur after cleanup:

```bash
# Restore from backup
psql -U postgres -h localhost -d lms < lms_backup_before_cleanup_YYYYMMDD.sql

# Drop the constraint if needed
psql -U postgres -h localhost -d lms << EOF
DROP TRIGGER IF EXISTS trigger_check_instructor_conflict ON class_schedules;
DROP FUNCTION IF EXISTS check_instructor_time_conflict();
DROP INDEX IF EXISTS idx_no_teacher_schedule_conflicts;
ALTER TABLE class_schedules DROP CONSTRAINT IF EXISTS check_schedule_times;
EOF
```

## Frontend Impact

### Calendar View
- **Before:** Showing 4-25 overlapping events per time slot
- **After:** Showing 1 event per time slot (clean view)

### Attendance Page
- **Before:** Multiple courses at same time (confusing)
- **After:** Only one class per time slot

### Schedule Page  
- **Before:** Impossible schedules displayed
- **After:** Realistic, achievable schedules

## Files Created

1. **`analyze_schedule_conflicts.py`** - Analysis tool
   - Identifies all conflicts
   - Shows detail of each conflict
   - Reports affected teachers

2. **`cleanup_schedule_conflicts.py`** - Cleanup script
   - Removes duplicate schedules
   - Keeps highest enrollment
   - Safe dry-run mode

3. **`migrations/add_schedule_conflict_prevention.sql`** - Database constraints
   - Trigger function for conflict detection
   - Unique index prevention
   - Time validation

4. **`SCHEDULE_CONFLICT_RESOLUTION_PLAN.md`** - This document

## Recommendations

### Immediate Action (Required)
1. ✅ Create database backup
2. ✅ Run cleanup script (dry-run first)
3. ✅ Execute cleanup (delete 48,090 records)
4. ✅ Apply database constraints

### Follow-up Actions
1. Review schedule creation process
2. Add UI validation in admin interfaces
3. Train staff on proper schedule creation
4. Regular audits for data quality

### Backend API Updates Needed
- Add schedule conflict validation to create/update endpoints
- Return user-friendly error messages
- Show conflicting schedule details in error response

## Questions to Consider

1. **Course Redistribution:** Should students from deleted courses be moved?
   - Most deleted courses have 0 enrollment (no impact)
   - Courses with students: kept (highest enrollment priority)

2. **Historical Data:** Keep deleted schedules in audit log?
   - Current script permanently deletes
   - Could modify to soft-delete (set deleted_at)

3. **Multi-Section Handling:** Same course, different sections?
   - Already handled by calendar grouping
   - Constraint allows this (different course_offering_id)

## Expected Results

### Database
- ✅ Clean schedule data (1 class per time slot)
- ✅ Constraints prevent future conflicts
- ✅ ~48K fewer records (better performance)

### User Experience
- ✅ Accurate schedules displayed
- ✅ No overlapping calendar events  
- ✅ Realistic class assignments
- ✅ Better system trust

### System Integrity
- ✅ Data matches reality
- ✅ Business rules enforced
- ✅ Impossible states prevented

## Support

If you encounter issues:

1. **Check logs:** Look for specific error messages
2. **Rollback:** Use backup to restore previous state
3. **Verify data:** Run analysis script after cleanup
4. **Test constraint:** Try creating conflict (should fail)

---

**Status:** Ready to execute
**Risk Level:** Medium (large data deletion, but keeping highest priority)
**Recommendation:** Proceed with caution, backup first

**Execution Command:**
```bash
# When ready
cd /home/axel/Developer/Education-system/backend
python3 cleanup_schedule_conflicts.py --execute
```
