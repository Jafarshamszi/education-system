#!/bin/bash

# Automated Schedule Conflict Resolution
# This script will fix the duplicate course problem

set -e  # Exit on error

echo ""
echo "============================================================"
echo "SCHEDULE CONFLICT RESOLUTION - AUTOMATED"
echo "============================================================"
echo ""
echo "This will:"
echo "  1. Backup the database"
echo "  2. Remove 48,090 duplicate schedule records"
echo "  3. Add database constraints to prevent future conflicts"
echo ""
echo "⚠️  WARNING: This will DELETE data from the database!"
echo ""
read -p "Type 'EXECUTE' to continue: " response
echo ""

if [ "$response" != "EXECUTE" ]; then
    echo "❌ Cancelled. No changes made."
    exit 1
fi

# Step 1: Backup Database
echo "============================================================"
echo "Step 1: Creating database backup..."
echo "============================================================"
BACKUP_FILE="lms_backup_$(date +%Y%m%d_%H%M%S).sql"
echo "Backup file: $BACKUP_FILE"
pg_dump -U postgres -h localhost lms > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✓ Backup created successfully: $BACKUP_FILE"
    echo "  File size: $(du -h $BACKUP_FILE | cut -f1)"
else
    echo "❌ Backup failed! Aborting."
    exit 1
fi

echo ""
read -p "Backup complete. Press ENTER to continue to cleanup..."
echo ""

# Step 2: Run Cleanup Script
echo "============================================================"
echo "Step 2: Running cleanup script..."
echo "============================================================"
cd /home/axel/Developer/Education-system/backend

# Run cleanup with auto-confirmation
echo "DELETE" | python3 cleanup_schedule_conflicts.py --execute

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Cleanup completed successfully"
else
    echo "❌ Cleanup failed!"
    echo "Database can be restored from: $BACKUP_FILE"
    exit 1
fi

echo ""
read -p "Cleanup complete. Press ENTER to apply constraints..."
echo ""

# Step 3: Apply Database Constraints
echo "============================================================"
echo "Step 3: Applying database constraints..."
echo "============================================================"

psql -U postgres -h localhost -d lms -f migrations/add_schedule_conflict_prevention.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Constraints applied successfully"
else
    echo "❌ Constraint application failed!"
    echo "Database can be restored from: $BACKUP_FILE"
    exit 1
fi

echo ""
echo "============================================================"
echo "✓ ALL STEPS COMPLETED SUCCESSFULLY!"
echo "============================================================"
echo ""
echo "Summary:"
echo "  ✓ Database backed up to: $BACKUP_FILE"
echo "  ✓ Duplicate schedules removed"
echo "  ✓ Constraints applied (prevents future conflicts)"
echo ""
echo "Next steps:"
echo "  1. Refresh the teacher schedule calendar page"
echo "  2. Verify only 1 course shows per time slot"
echo "  3. Test that you cannot create schedule conflicts"
echo ""
echo "If anything went wrong, restore with:"
echo "  psql -U postgres -h localhost -d lms < $BACKUP_FILE"
echo ""
echo "============================================================"
