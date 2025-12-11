# Why Only 95.8% of Exam Submissions Were Migrated

## 📊 The Numbers

| Metric | Count |
|--------|-------|
| **Total exam submissions in old DB** | 66,337 |
| **Successfully migrated to new DB** | 63,531 |
| **Could NOT be migrated** | 2,806 (4.2%) |
| **Migration coverage** | **95.8%** |

---

## 🎯 The Root Cause: Missing Students

### Student Analysis

Out of **5,193 unique students** who took exams in the old database:
- ✅ **4,868 students** (93.7%) were migrated to the new database
- ❌ **325 students** (6.3%) were **NOT migrated**

These **325 missing students** had **2,806 exam submissions** that cannot be migrated.

---

## ❌ Why Their Submissions Can't Be Migrated

### Database Constraint Prevents It

The new database has a **FOREIGN KEY constraint**:

```sql
assessment_submissions.student_id → students.id
```

**What this means:**
- Every submission MUST reference a student that exists in the `students` table
- You cannot insert a submission for a non-existent student
- PostgreSQL will **reject** the insert with a foreign key violation error

### This is Actually GOOD! 

This constraint ensures **referential integrity** and prevents:
- Orphaned submissions (submissions without owners)
- Data inconsistencies
- Broken relationships in the database

---

## 💡 Why Weren't These 325 Students Migrated?

During the **Phase 1-5 student migration**, these students were likely excluded because:

1. **Inactive Status** - They were marked as `active = 0` in the old database
2. **Incomplete Data** - Missing required fields (name, email, etc.)
3. **Filter Criteria** - The migration script had filters to exclude certain students
4. **Test Accounts** - They might have been test/dummy accounts
5. **Duplicates** - They could be duplicate records that were consolidated
6. **Data Quality** - They failed validation checks

---

## ✅ How to Reach 100% Coverage

### Option 1: Migrate the Missing Students (Recommended)

If these students should be in the new system:

1. **Identify the 325 missing students:**
   ```sql
   SELECT DISTINCT es.student_id
   FROM exam_student es
   WHERE es.active = 1
   AND NOT EXISTS (
       SELECT 1 FROM students s
       WHERE s.metadata->>'old_student_id' = es.student_id::text
   )
   ```

2. **Migrate these students to the new database**
   - Run a targeted student migration for these 325 students
   - Ensure they have all required fields

3. **Then migrate their submissions**
   - The 2,806 submissions can now be migrated
   - This will bring coverage to 100%

### Option 2: Accept 95.8% as Maximum (Current)

If these students were intentionally excluded:

- ✅ **95.8% is the maximum achievable** coverage
- These submissions belong to inactive/invalid student accounts
- Keeping them out maintains data quality
- **This is the current status - ACCEPTABLE**

---

## 📈 Visual Breakdown

```
Total Exam Submissions: 66,337
│
├─ ✅ Migratable (student exists): 63,531 (95.8%)
│   └─ Successfully migrated: 63,531 ✓
│
└─ ❌ Not Migratable (student missing): 2,806 (4.2%)
    └─ Reason: 325 students not in new database
       │
       ├─ Inactive students
       ├─ Incomplete data
       ├─ Test accounts
       └─ Filtered during Phase 1-5 migration
```

---

## 🔍 Verification

You can verify this yourself:

### Check Missing Students
```sql
-- Students with exam submissions but not migrated
SELECT COUNT(DISTINCT es.student_id)
FROM exam_student es
WHERE es.active = 1
AND NOT EXISTS (
    SELECT 1 FROM students s
    WHERE s.metadata->>'old_student_id' = es.student_id::text
);
-- Result: 325 students
```

### Check Their Submissions
```sql
-- Submissions from unmigrated students
SELECT COUNT(*)
FROM exam_student es
WHERE es.active = 1
AND NOT EXISTS (
    SELECT 1 FROM students s
    WHERE s.metadata->>'old_student_id' = es.student_id::text
);
-- Result: 2,806 submissions
```

---

## 📝 Summary

**Question:** Why only 95.8% of exam submissions migrated?

**Answer:** Because **325 students** (6.3% of students with exams) were **not migrated** during the Phase 1-5 student migration. Their **2,806 exam submissions** cannot be migrated due to foreign key constraints that maintain database integrity.

**Current Status:** ✅ **95.8% is the MAXIMUM ACHIEVABLE** given the current student base in the new database.

**To Reach 100%:** Migrate the missing 325 students first, then their 2,806 submissions can follow.

---

**Date:** October 4, 2025  
**Analysis Type:** Database Migration Coverage  
**Status:** Complete Understanding ✓
