# MAJOR-KAFEDRA-TEACHER RELATIONSHIP ANALYSIS - FINAL REPORT

## Database Structure Findings

### Key Tables
1. **teachers** - Contains teacher records
   - `organization_id` - Links to departments/kafedra

2. **organizations** - Contains organizational units (kafedra, faculties, etc.)
   - Hierarchical structure with `parent_id`
   - Different types indicated by `type_id`

3. **course** - Course records
   - `education_plan_subject_id` - Links to education plan subjects

4. **education_plan_subject** - Subject definitions in education plans
   - `subject_id` - Links to subject dictionary
   - `subject_group_id` - Links to subject groups
   - **NO kafedra_id column**

5. **subject_dic** - Subject dictionary
   - **NO kafedra_id column**

## Problem

**There is NO direct link between subjects/courses and kafedra (departments)!**

The database structure doesn't have a `kafedra_id` field in:
- `education_plan_subject`
- `subject_dic`
- `education_plan_subject_group`

## Solution Strategy

Since there's no direct kafedra link, we need to implement a different approach:

### Option 1: Use Education Group (ixtisas/major)
When creating a course, use the education group (which represents the major/specialization) to filter teachers.

**Logic:**
1. Course creation form selects `education_group_id`
2. Find all teachers who teach for students in that education group
3. This is done by finding teachers assigned to courses for that education group

### Option 2: Manual Teacher-Subject Association (Recommended)
Create a mapping table or use existing course_teacher relationships to suggest teachers based on:
1. Teachers who have previously taught similar subjects
2. Teachers in the same faculty/organization as the education group
3. All active teachers (with manual selection)

### Option 3: Add Kafedra Field (Database Migration Required)
Add a `kafedra_id` column to `subject_dic` or `education_plan_subject` table to establish the proper relationship.

## Recommended Implementation

### Backend API Endpoint
Create an endpoint that filters teachers by education_group_id:

```python
@router.get("/teachers/by-education-group/{education_group_id}")
async def get_teachers_by_education_group(education_group_id: int):
    """
    Get teachers relevant to an education group
    Returns teachers who have taught courses for this education group
    """
    # Query teachers who have taught courses for this education group
    # Plus all teachers from related organizations
```

### Alternative: Organization-Based Filtering
Use the organization hierarchy to filter teachers:

1. Get the education group's organization
2. Find all teachers in that organization or its child organizations
3. Return filtered list

## Implementation Plan

1. **Backend**: Create new API endpoint `/teachers/filtered` that accepts `education_group_id` or `organization_id`
2. **Frontend**: Update course creation modal to:
   - Detect when education group is selected
   - Call the filtered teachers endpoint
   - Update teacher dropdown with filtered results
3. **Fallback**: If no teachers found for filter, show all teachers

## Database Query Examples

### Get Teachers by Organization
```sql
SELECT t.*, p.first_name_az, p.last_name_az, p.father_name_az
FROM teachers t
INNER JOIN persons p ON p.id = t.person_id
WHERE t.organization_id = :org_id
  AND t.active = 1
```

### Get Organization by Education Group (if relationship exists)
Need to determine the relationship between education_group and organizations.
