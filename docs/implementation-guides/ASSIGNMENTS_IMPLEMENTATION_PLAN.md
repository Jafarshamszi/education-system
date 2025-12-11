# Assignments Feature Implementation Plan

## Current Situation Analysis

### Database Status
- **Database**: Using old `edu` database schema (NOT the new migrated schema)
- **Existing Tables**: 
  - `exam` - For exams/tests
  - `exam_student` - For exam submissions
  - **NO assignments/homework tables exist**
- **Impact**: Need to create complete assignment system from scratch

### Requirements
1. Students can view class assignments
2. See deadlines and which class/course
3. View assignment details (description, instructions, grading criteria)
4. Upload assignment submissions (file upload)
5. See submission status (pending, submitted, graded)
6. View grades and feedback on submitted assignments

## Implementation Strategy

### Option 1: Use Existing `exam` Table (Recommended for Quick Implementation)
**Pros:**
- No database schema changes needed
- Reuse existing structure
- `exam` table already has fields for assignments-like data
- `exam_student` table already tracks student submissions

**Cons:**
- Semantically confusing (exam vs assignment)
- May have limitations for assignment-specific features

**Table Structure (`exam`):**
```
- id: bigint (PK)
- subject_id: bigint → linked to courses
- exam_name: text
- exam_date: date
- duration: integer
- total_marks: numeric
- passing_marks: numeric
- description: text
- status: active/inactive
```

**Table Structure (`exam_student`):**
```
- id: bigint (PK)
- exam_id: bigint → exam.id
- student_id: bigint → students.id
- submission_date: timestamp
- score: numeric
- status: enum (submitted, graded, etc.)
- file_path: text (for uploaded files)
```

### Option 2: Create New Tables (Proper Implementation)
**Pros:**
- Clean separation of concerns
- Can design specifically for assignments
- Future-proof

**Cons:**
- Requires database migrations
- More complex initial setup
- Need to ensure compatibility with existing system

**Proposed Schema:**
```sql
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    course_id BIGINT REFERENCES subjects(id),
    title TEXT NOT NULL,
    description TEXT,
    instructions TEXT,
    due_date TIMESTAMP NOT NULL,
    total_marks NUMERIC(10,2),
    weight_percentage NUMERIC(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE assignment_submissions (
    id SERIAL PRIMARY KEY,
    assignment_id BIGINT REFERENCES assignments(id),
    student_id BIGINT REFERENCES students(id),
    submission_date TIMESTAMP DEFAULT NOW(),
    file_path TEXT,
    file_name TEXT,
    file_size BIGINT,
    status TEXT DEFAULT 'submitted',
    score NUMERIC(10,2),
    feedback TEXT,
    graded_at TIMESTAMP,
    graded_by BIGINT REFERENCES users(id),
    UNIQUE(assignment_id, student_id)
);
```

## Recommended Approach: Hybrid Solution

### Phase 1: Use Existing Infrastructure (Immediate)
1. Filter `exam` table for assignment-type items
2. Add `exam_type` field (exam/assignment/quiz) if doesn't exist
3. Use `exam_student` for submissions
4. Implement file upload to store on server/cloud

### Phase 2: Enhance with Metadata (Future)
1. Add JSONB metadata field to `exam` table for assignment-specific data
2. Store instructions, rubrics, etc. in metadata

## Backend API Design

### Endpoint 1: GET /api/v1/students/me/assignments
**Purpose**: Get all assignments for authenticated student

**Response**:
```json
{
  "student_id": "uuid",
  "student_number": "STU123",
  "full_name": "Student Name",
  "assignments": [
    {
      "assignment_id": "123",
      "course_code": "SUBJ00169",
      "course_name": "Business Analysis",
      "title": "Week 1 Homework",
      "description": "Complete the analysis...",
      "instructions": "Follow these steps...",
      "due_date": "2024-09-30T23:59:59",
      "total_marks": 100,
      "weight_percentage": 10,
      "status": "pending|submitted|graded|overdue",
      "submission": {
        "submitted_at": "2024-09-25T14:30:00",
        "file_name": "assignment.pdf",
        "score": 85,
        "feedback": "Good work...",
        "graded_at": "2024-10-01T10:00:00"
      }
    }
  ]
}
```

**SQL Query**:
```sql
SELECT
    e.id as assignment_id,
    s.subject_code as course_code,
    s.subject_name as course_name,
    e.exam_name as title,
    e.description,
    e.exam_date as due_date,
    e.total_marks,
    es.submission_date as submitted_at,
    es.file_path as file_name,
    es.score,
    es.feedback,
    es.graded_at,
    CASE
        WHEN es.id IS NULL AND e.exam_date < NOW() THEN 'overdue'
        WHEN es.id IS NULL THEN 'pending'
        WHEN es.score IS NULL THEN 'submitted'
        ELSE 'graded'
    END as status
FROM exam e
JOIN subjects s ON e.subject_id = s.id
JOIN journal j ON s.id = j.subject_id
LEFT JOIN exam_student es ON e.id = es.exam_id AND es.student_id = %s
WHERE j.student_id = %s
    AND e.exam_type = 'assignment' -- if field exists
ORDER BY e.exam_date ASC
```

### Endpoint 2: POST /api/v1/students/me/assignments/{id}/submit
**Purpose**: Submit assignment with file upload

**Request**:
- Content-Type: multipart/form-data
- Body: file (PDF, DOCX, ZIP, etc.)

**Response**:
```json
{
  "success": true,
  "submission_id": "456",
  "submitted_at": "2024-09-25T14:30:00",
  "file_name": "assignment.pdf",
  "file_size": 1024567,
  "message": "Assignment submitted successfully"
}
```

**File Storage Strategy**:
```
/uploads/assignments/{student_id}/{assignment_id}/{filename}
```

### Endpoint 3: GET /api/v1/students/me/assignments/{id}
**Purpose**: Get detailed information about specific assignment

**Response**: Same as individual assignment object above

## Frontend UI Design

### Page Structure
```
/dashboard/assignments
├── Header (Title + Add filters)
├── Summary Cards (Total, Pending, Submitted, Graded)
├── Tabs (All | Pending | Submitted | Graded | Overdue)
└── Assignment List/Cards
    ├── Assignment Card
    │   ├── Course Badge
    │   ├── Title
    │   ├── Due Date (with countdown/overdue indicator)
    │   ├── Status Badge
    │   ├── Progress Bar (if graded)
    │   └── Actions (View Details | Submit | View Submission)
    └── Assignment Details Dialog
        ├── Full Description
        ├── Instructions
        ├── Requirements
        ├── Grading Rubric
        ├── File Upload Area (if not submitted)
        ├── Submission Info (if submitted)
        └── Grade & Feedback (if graded)
```

### Components Needed
1. **shadcn/ui**:
   - Tabs (for filtering)
   - Card (assignment cards)
   - Badge (status, course)
   - Dialog (assignment details)
   - Progress (grade visualization)
   - Button (actions)
   - Separator (visual separation)
   - Form (file upload)
   
2. **Custom**:
   - FileUpload component
   - CountdownTimer component
   - StatusIndicator component

### Features
1. **Status Indicators**:
   - 🔴 Overdue (red)
   - 🟡 Pending (yellow)
   - 🔵 Submitted (blue)
   - 🟢 Graded (green)

2. **Deadline Display**:
   - "Due in 3 days"
   - "Overdue by 2 days"
   - "Due today at 11:59 PM"

3. **File Upload**:
   - Drag & drop area
   - File type validation (PDF, DOCX, ZIP)
   - Size limit (10MB)
   - Progress indicator
   - Preview uploaded file name

4. **Filters & Sorting**:
   - By status (tabs)
   - By course (dropdown)
   - By date (ascending/descending)
   - Search by title

## Implementation Steps

### Step 1: Backend Setup (1-2 hours)
1. ✅ Analyze database structure
2. ⏳ Check if `exam` table has type field or add filter logic
3. ⏳ Create `/me/assignments` endpoint
4. ⏳ Create `/me/assignments/{id}/submit` endpoint
5. ⏳ Implement file upload handling
6. ⏳ Test with student 783QLRA

### Step 2: Frontend Setup (2-3 hours)
1. ⏳ Install shadcn components (tabs, progress, separator)
2. ⏳ Create `/app/dashboard/assignments/page.tsx`
3. ⏳ Implement assignment list with tabs
4. ⏳ Create assignment card component
5. ⏳ Implement file upload component
6. ⏳ Create assignment details dialog
7. ⏳ Add status badges and deadline indicators

### Step 3: Integration & Testing (30min - 1 hour)
1. ⏳ Test API with real data
2. ⏳ Test file upload functionality
3. ⏳ Test UI with different statuses
4. ⏳ Verify navigation link in sidebar

## File Upload Implementation

### Backend (FastAPI)
```python
from fastapi import UploadFile, File
import os
from datetime import datetime

UPLOAD_DIR = "uploads/assignments"

@router.post("/students/me/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Get student
    student = get_student_by_user_id(current_user.id)
    
    # Validate file type
    allowed_types = ['pdf', 'docx', 'doc', 'zip', 'txt']
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(400, "Invalid file type")
    
    # Create directory
    upload_path = f"{UPLOAD_DIR}/{student.id}/{assignment_id}"
    os.makedirs(upload_path, exist_ok=True)
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = f"{upload_path}/{filename}"
    
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Save to database
    save_submission(assignment_id, student.id, filepath, len(content))
    
    return {"success": True, "filename": filename}
```

### Frontend
```tsx
const handleFileUpload = async (file: File, assignmentId: string) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(
    `http://localhost:8000/api/v1/students/me/assignments/${assignmentId}/submit`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }
  );
  
  return response.json();
};
```

## Data Model Summary

### Using Existing `exam` Table as Assignments:
- ✅ No schema changes needed
- ✅ Quick to implement
- ✅ Reuses existing submission tracking
- ⚠️ Need to differentiate exams from assignments (use description/metadata)

### Fields Mapping:
```
exam.exam_name → Assignment Title
exam.description → Assignment Description + Instructions
exam.exam_date → Due Date
exam.total_marks → Total Points
exam_student.file_path → Submission File
exam_student.submission_date → Submitted At
exam_student.score → Grade
```

## Next Steps

1. **Immediate**: Check if there are any exams in the database that can be used as sample assignments
2. **Create Backend**: Implement the two main endpoints
3. **Test Backend**: Verify with student 783QLRA
4. **Create Frontend**: Build the assignments page UI
5. **Test E2E**: Full workflow testing

## Success Criteria

- [ ] Students can see list of assignments
- [ ] Assignments show course name, title, due date
- [ ] Status badges show correctly (pending, submitted, graded, overdue)
- [ ] Students can click to see assignment details
- [ ] Students can upload files for assignments
- [ ] Submitted assignments show submission date and file name
- [ ] Graded assignments show score and feedback
- [ ] Overdue assignments are visually highlighted
- [ ] UI is responsive and follows shadcn/ui patterns
- [ ] All data comes from real database
