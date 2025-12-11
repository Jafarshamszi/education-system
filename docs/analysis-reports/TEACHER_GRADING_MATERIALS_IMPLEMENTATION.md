# Teacher Frontend - Grading & Course Materials Features Implementation

**Date:** October 14, 2025  
**Status:** ✅ Phase 1 Complete (Grading System) | 🚧 Phase 2 In Progress (Materials Upload)

---

## 📋 Overview

This document details the implementation of three major features requested for the teacher frontend:

1. ✅ **Change grading scale from 0-100 to 1-10**
2. 🚧 **Add course materials upload feature**
3. ✅ **Implement attendance-before-grades validation**

---

## ✅ COMPLETED: Grading Scale Change (0-100 → 1-10)

### Changes Made

#### Frontend: `frontend-teacher/app/dashboard/grades/page.tsx`

**1. Default Total Marks Changed:**
```typescript
// Before
const [totalMarks, setTotalMarks] = useState<string>("100");

// After
const [totalMarks, setTotalMarks] = useState<string>("10");
```

**2. Input Validation Updated:**
```typescript
<Input
  id="total"
  type="number"
  min="1"        // Changed from "0"
  max="10"       // Added max limit
  step="0.5"
  placeholder="10"
/>
```

**3. Grade Input Fields Updated:**
```typescript
<Input
  type="number"
  min="1"                          // Changed from "0"
  max="10"                         // Changed from totalMarks variable
  step="0.5"
  placeholder="Enter grade (1-10)" // Updated placeholder
/>
```

**4. UI Labels Updated:**
- "Total Marks *" → "Total Marks (out of 10) *"
- Table header: "Grade (/{totalMarks})" dynamically shows "/10"
- Placeholders updated to reflect 1-10 scale

### Grading Scale Interpretation

The system now uses a 10-point scale with percentage mapping:
- **9.0-10.0** = A (90-100%) → Green
- **8.0-8.9** = B (80-89%) → Blue
- **7.0-7.9** = C (70-79%) → Yellow
- **6.0-6.9** = D (60-69%) → Orange
- **Below 6.0** = F → Red

---

## ✅ COMPLETED: Attendance-Before-Grades Validation

### Problem Statement

Teachers need to:
1. Submit attendance BEFORE entering grades
2. Cannot grade students who were absent or late
3. See attendance status while grading

### Solution Architecture

#### Backend Changes: `backend/app/api/teachers.py`

**1. New Endpoint: Check Attendance Status**

```python
@router.get("/me/attendance/check")
def check_attendance_status(
    course_offering_id: str,
    attendance_date: str,  # YYYY-MM-DD
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Check if attendance has been submitted for a specific course and date.
    Returns:
    - has_attendance: boolean
    - student_attendance: dict with each student's status
    """
```

**Response Format:**
```json
{
  "has_attendance": true,
  "attendance_date": "2025-10-14",
  "course_offering_id": "123",
  "total_records": 25,
  "student_attendance": {
    "student_id_1": {
      "student_id": "student_id_1",
      "student_number": "783QLRA",
      "full_name": "John Doe",
      "status": "present",
      "notes": null
    },
    "student_id_2": {
      "status": "absent",
      ...
    }
  }
}
```

**2. Updated: POST /me/grades Endpoint**

Added two validation checks:

**Check 1: Attendance Must Be Submitted**
```python
# Check if attendance records exist for this date
cur.execute("""
    SELECT COUNT(*) as attendance_count
    FROM attendance_records ar
    JOIN class_schedules cs ON ar.class_schedule_id = cs.id
    WHERE cs.course_offering_id = %s
        AND ar.attendance_date = %s
""", [request.course_offering_id, request.assessment_date])

if attendance_check['attendance_count'] == 0:
    raise HTTPException(
        status_code=400,
        detail="Attendance must be submitted before entering grades for this date"
    )
```

**Check 2: Skip Absent/Late Students**
```python
for grade in request.grades:
    # Check student's attendance status
    cur.execute("""
        SELECT ar.status
        FROM attendance_records ar
        JOIN class_schedules cs ON ar.class_schedule_id = cs.id
        WHERE cs.course_offering_id = %s
            AND ar.attendance_date = %s
            AND ar.student_id = %s
    """, [request.course_offering_id, request.assessment_date, grade.student_id])

    attendance_record = cur.fetchone()
    
    # Skip grading if student was absent or late
    if attendance_record and attendance_record['status'] in ['absent', 'late']:
        skipped_students.append({
            'student_id': grade.student_id,
            'reason': f"Student was {attendance_record['status']}"
        })
        continue
```

**Updated Response:**
```json
{
  "message": "Successfully saved grades for 20 students. Skipped 5 students (absent/late)",
  "assessment_id": "456",
  "grades_saved": 20,
  "skipped_students": [
    {
      "student_id": "789",
      "reason": "Student was absent"
    }
  ]
}
```

#### Frontend Changes: `frontend-teacher/app/dashboard/grades/page.tsx`

**1. New State Variables:**
```typescript
const [attendanceStatus, setAttendanceStatus] = useState<{
  has_attendance: boolean;
  student_attendance: { 
    [key: string]: { 
      status: string; 
      student_number: string; 
      full_name: string 
    } 
  };
} | null>(null);
const [attendanceChecked, setAttendanceChecked] = useState(false);
```

**2. Attendance Check on Course/Date Change:**
```typescript
useEffect(() => {
  if (!selectedCourse || !assessmentDate) {
    setAttendanceChecked(false);
    setAttendanceStatus(null);
    return;
  }

  const checkAttendance = async () => {
    const dateStr = format(assessmentDate, "yyyy-MM-dd");
    const response = await fetch(
      `http://localhost:8000/api/v1/teachers/me/attendance/check?course_offering_id=${selectedCourse}&attendance_date=${dateStr}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );

    if (response.ok) {
      const data = await response.json();
      setAttendanceStatus(data);
      setAttendanceChecked(true);
    }
  };

  checkAttendance();
}, [selectedCourse, assessmentDate]);
```

**3. Warning Banner:**
```tsx
{attendanceChecked && !attendanceStatus?.has_attendance && selectedCourse && (
  <Card className="mb-6 border-yellow-600 bg-yellow-50">
    <CardContent className="pt-6 flex items-center gap-3">
      <AlertCircle className="h-5 w-5 text-yellow-700" />
      <p className="text-yellow-800 font-medium">
        Attendance has not been submitted for {format(assessmentDate, "PPP")}. 
        You must submit attendance before entering grades for this date.
      </p>
    </CardContent>
  </Card>
)}
```

**4. Updated Table with Attendance Column:**
```tsx
<TableHeader>
  <TableRow>
    <TableHead>Student</TableHead>
    <TableHead>Student Number</TableHead>
    <TableHead>Attendance</TableHead>  {/* NEW */}
    <TableHead className="w-[150px]">Grade (/10)</TableHead>
    <TableHead>Notes</TableHead>
  </TableRow>
</TableHeader>
```

**5. Attendance Status Display:**
```tsx
<TableCell>
  {studentAttendance ? (
    <Badge 
      variant={
        studentAttendance.status === 'present' ? 'default' :
        studentAttendance.status === 'late' ? 'secondary' :
        'destructive'
      }
      className="capitalize"
    >
      {studentAttendance.status}
    </Badge>
  ) : (
    <span className="text-xs text-muted-foreground">No record</span>
  )}
</TableCell>
```

**6. Disabled Grade Inputs for Absent/Late:**
```tsx
const isAbsentOrLate = studentAttendance && 
  ['absent', 'late'].includes(studentAttendance.status);

<Input
  type="number"
  min="1"
  max="10"
  disabled={isAbsentOrLate || !attendanceStatus?.has_attendance}
  placeholder={isAbsentOrLate ? "Cannot grade" : "Enter grade (1-10)"}
  // ...
/>

{isAbsentOrLate && (
  <p className="text-xs text-muted-foreground italic">
    {studentAttendance?.status === 'absent' ? 
      'Student was absent' : 'Student was late'}
  </p>
)}
```

**7. Disabled Save Button:**
```tsx
<Button
  onClick={handleSubmit}
  disabled={
    saving || 
    students.length === 0 || 
    gradeRecords.size === 0 || 
    !attendanceStatus?.has_attendance  // NEW
  }
>
  <Save className="w-4 h-4 mr-2" />
  {saving ? "Saving..." : "Save Grades"}
</Button>
```

### User Flow

1. Teacher selects course and assessment date
2. System automatically checks if attendance was submitted for that date
3. **If NO attendance:**
   - Yellow warning banner appears
   - All grade inputs disabled
   - Save button disabled
   - Message: "Attendance must be submitted before entering grades"

4. **If attendance EXISTS:**
   - Attendance badge shown for each student (Present/Late/Absent)
   - Present students: Grade input enabled (green badge)
   - Late students: Grade input disabled (yellow badge) + "Student was late" message
   - Absent students: Grade input disabled (red badge) + "Student was absent" message

5. Teacher can only enter grades for present students
6. On save, backend validates again and skips absent/late students
7. Success message shows: "Saved 20 grades. Skipped 5 students (absent/late)"

---

## 🚧 IN PROGRESS: Course Materials Upload Feature

### Database Schema

**Table Created:** `course_materials`

```sql
CREATE TABLE course_materials (
    id BIGSERIAL PRIMARY KEY,
    schedule_subject_id BIGINT NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(100),
    material_type VARCHAR(50) DEFAULT 'document',
    uploaded_by BIGINT NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_visible BOOLEAN DEFAULT TRUE,
    sequence_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes Created:**
- `idx_course_materials_offering` on `schedule_subject_id`
- `idx_course_materials_uploaded_by` on `uploaded_by`
- `idx_course_materials_type` on `material_type`
- `idx_course_materials_visible` on `is_visible`

### Remaining Tasks

1. **Backend: Create FastAPI file upload endpoint**
   - POST `/api/v1/teachers/me/courses/{offering_id}/materials`
   - File validation (size, type, virus scan)
   - Store files in organized directory structure
   - Insert records in `course_materials` table

2. **Backend: Create materials list endpoint**
   - GET `/api/v1/teachers/me/courses/{offering_id}/materials`
   - Return all materials for a course
   - Filter by visibility

3. **Backend: Create delete material endpoint**
   - DELETE `/api/v1/teachers/me/courses/{offering_id}/materials/{material_id}`
   - Verify teacher ownership
   - Delete file from disk
   - Delete database record

4. **Frontend: Update My Courses page**
   - Add "Materials" section to course details modal
   - File upload component with drag-and-drop
   - Materials list with download links
   - Delete confirmation dialog
   - Progress indicators for uploads
   - Error handling for large files

---

## 🧪 Testing Checklist

### Grading Scale (1-10)
- [ ] Default total marks is 10
- [ ] Can enter grades from 1 to 10 with 0.5 increments
- [ ] Cannot enter grades above 10 or below 1
- [ ] Grade colors display correctly (green for 9+, blue for 8+, etc.)
- [ ] Table header shows "Grade (/10)"
- [ ] Backend accepts and saves grades correctly

### Attendance-Before-Grades Validation
- [ ] Warning banner appears when no attendance submitted
- [ ] All inputs disabled when no attendance
- [ ] Save button disabled when no attendance
- [ ] Attendance check API endpoint returns correct data
- [ ] Attendance badges display correctly (Present/Late/Absent)
- [ ] Present students: inputs enabled
- [ ] Late students: inputs disabled + helper text
- [ ] Absent students: inputs disabled + helper text
- [ ] Backend rejects grades without attendance
- [ ] Backend skips absent/late students correctly
- [ ] Success message shows skipped students count
- [ ] Grade inputs become enabled/disabled when attendance changes

### Course Materials Upload (Pending)
- [ ] Upload button visible in My Courses
- [ ] Drag and drop works
- [ ] File size validation (max 50MB)
- [ ] File type validation
- [ ] Upload progress indicator
- [ ] Materials list displays correctly
- [ ] Download links work
- [ ] Delete confirmation dialog
- [ ] Only teacher who uploaded can delete
- [ ] Students can view materials

---

## 📊 Build Status

```
✓ Compiled successfully in 3.8s
✓ Linting and checking validity of types
✓ Generating static pages (14/14)
✓ Finalizing page optimization

Route (app)                         Size  First Load JS
├ ○ /dashboard/grades            12.5 kB         203 kB
```

**Build Status:** ✅ Successful  
**Lint Errors:** 0  
**Type Errors:** 0

---

## 🔐 Security Considerations

### Implemented:
1. ✅ Teacher authorization check for all endpoints
2. ✅ Token-based authentication
3. ✅ SQL injection prevention (parameterized queries)
4. ✅ Attendance validation on both frontend and backend
5. ✅ Grade value validation (1-10 range)

### To Implement (Materials Upload):
1. File size limits (50MB max)
2. File type whitelist (PDF, DOCX, PPTX, ZIP, etc.)
3. Virus scanning
4. Storage quota per teacher
5. Filename sanitization
6. Path traversal prevention

---

## 📝 API Endpoints Summary

### New Endpoints

**GET `/api/v1/teachers/me/attendance/check`**
- Query params: `course_offering_id`, `attendance_date`
- Returns: Attendance status and student records

**POST `/api/v1/teachers/me/grades`** (Enhanced)
- Now validates attendance before saving
- Skips absent/late students automatically
- Returns skipped students list

### Pending Endpoints (Materials)

**POST `/api/v1/teachers/me/courses/{offering_id}/materials`**
- Upload course material file
- Store file and create database record

**GET `/api/v1/teachers/me/courses/{offering_id}/materials`**
- List all materials for a course

**DELETE `/api/v1/teachers/me/courses/{offering_id}/materials/{material_id}`**
- Delete material file and record

---

## 📦 Dependencies

### No New Dependencies Required

All features implemented using existing packages:
- Frontend: Next.js, React, shadcn/ui, Tailwind CSS, date-fns, lucide-react
- Backend: FastAPI, psycopg2, PostgreSQL

### Future Dependencies (Materials Upload):
- `python-multipart` (FastAPI file uploads)
- `aiofiles` (async file operations)
- `python-magic` (file type detection)
- `clamd` (virus scanning - optional)

---

## 🎯 Next Steps

1. **Complete Materials Upload Feature:**
   - Create FastAPI upload endpoint (2-3 hours)
   - Create frontend upload UI (2-3 hours)
   - Add materials list display (1-2 hours)
   - Implement delete functionality (1 hour)
   - Testing (2 hours)

2. **Testing & Validation:**
   - Test grading scale changes
   - Test attendance validation workflow
   - End-to-end testing with real data

3. **Documentation:**
   - User guide for teachers
   - API documentation
   - Deployment notes

---

## 📞 Support & Questions

If you encounter issues:
1. Check browser console for frontend errors
2. Check backend logs for API errors
3. Verify attendance was submitted before attempting to grade
4. Ensure grade values are between 1 and 10

---

**Implementation Date:** October 14, 2025  
**Version:** 1.0  
**Status:** Phase 1 Complete ✅ | Phase 2 In Progress 🚧
