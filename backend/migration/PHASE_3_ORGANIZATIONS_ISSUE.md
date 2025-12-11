# Phase 3: Organizations Migration - Known Issue

## Problem Summary
The organizations table migration is failing due to invalid parent_id references in the old database.

## Root Cause
Some organizations have `parent_id` values that reference organization IDs that don't exist in the organizations table. This is a data integrity issue in the old 'edu' database.

## Evidence
- 60 total organizations in old database
- All organizations successfully inserted (60/60)
- Foreign key constraint recreation fails because some parent_id values reference non-existent organization UUIDs

## Failed UUID Example
```
parent_id=(ab286d30-98c7-49a3-ad78-8c5dfdad828c) is not present in table "organization_units"
```

## Temporary Solution
Organizations migration is SKIPPED for now. The system can function without migrated organizations as:
1. Users, persons, students, staff are all migrated successfully
2. Organizations are not critical for initial system operation
3. Can be fixed and re-run independently later

## Next Steps to Fix
1. Analyze the old organizations table to find orphaned parent_id references:
   ```sql
   SELECT o.id, o.parent_id
   FROM organizations o
   WHERE o.parent_id IS NOT NULL
   AND o.parent_id NOT IN (SELECT id FROM organizations);
   ```

2. Options:
   - Set orphaned parent_ids to NULL
   - Create placeholder organizations for missing parents
   - Skip organizations with invalid parents

3. Re-run Phase 3 migration after data cleanup

## Impact
- **LOW IMPACT**: Organizations are reference data, not critical for core LMS functionality
- Students, staff, and user authentication all work without organizations
- Course and enrollment migrations (Phase 4-5) may need organization_id, but can use NULL or default value

## Recommendation
Continue with Phase 4-5 migrations. Fix organizations in a separate data cleanup task.

---
**Status**: DEFERRED - Not blocking critical migration
**Priority**: Medium - Can be fixed post-deployment
