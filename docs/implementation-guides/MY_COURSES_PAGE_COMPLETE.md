# My Courses Page - Teacher Dashboard

## 📅 Date: October 12, 2025

## 🎯 Overview

Created a comprehensive "My Courses" page for teachers that displays detailed information about all courses they are teaching. The page fetches real data from the NEW database (lms) and displays it using shadcn/ui components.

---

## ✨ Features Implemented

### Backend API Endpoint

**Endpoint**: `GET /api/v1/teachers/me/courses`

**Features**:
- ✅ Fetches detailed course information from NEW database (lms)
- ✅ Includes comprehensive course details (credits, hours, enrollment, etc.)
- ✅ Extracts multilingual data from JSONB fields
- ✅ Supports up to 100 courses per teacher
- ✅ Ordered by academic year, term, and course code

**Response Model**: `TeacherCoursesListResponse`
```typescript
{
  total_courses: number,
  courses: [
    {
      offering_id: string,          // Unique UUID
      course_code: string,           // e.g., "SUBJ00691"
      course_name: string,           // Azerbaijani name from JSONB
      course_description: string | null,
      credit_hours: number,          // Course credits
      lecture_hours: number,         // Weekly lecture hours
      lab_hours: number,             // Weekly lab hours
      tutorial_hours: number,        // Weekly tutorial hours
      course_level: string | null,   // undergraduate/graduate/etc
      section_code: string,          // Section identifier
      semester: string,              // Fall/Spring/Summer
      academic_year: string,         // e.g., "2020-2021"
      term_type: string,             // fall/spring/summer
      max_enrollment: number,        // Maximum students
      current_enrollment: number,    // Currently enrolled
      delivery_mode: string | null,  // in_person/online/hybrid
      enrollment_status: string,     // open/closed/cancelled
      language_of_instruction: string, // az/en/ru
      is_published: boolean          // Published status
    }
  ]
}
```

### Frontend Page

**Route**: `/dashboard/courses`

**Features**:
- ✅ Displays all courses in a responsive grid layout
- ✅ Real-time search functionality (by name, code, or section)
- ✅ Loading states with skeleton components
- ✅ Error handling with user-friendly messages
- ✅ Color-coded status badges
- ✅ Enrollment progress bars
- ✅ Course details at a glance

**Components Used** (shadcn/ui):
- Card, CardHeader, CardTitle, CardDescription, CardContent
- Badge (with variants)
- Input (for search)
- Skeleton (for loading states)
- Icons from lucide-react

---

## 🎨 UI Design

### Course Card Layout

Each course card displays:

#### Header Section
```
┌─────────────────────────────────┐
│ [SUBJ00691]        [✓ Published]│
│                                  │
│ Xarici dildə işgüzar və         │
│ akademik kommunikasiya- 3        │
│                                  │
│ 2022/2023_PY_HF-B03.            │
└─────────────────────────────────┘
```

#### Content Section
```
┌─────────────────────────────────┐
│ 📅 Fall 2020-2021               │
│                                  │
│ 🎓 3 Credits • 0h Lecture       │
│                                  │
│ 👥 0/30 enrolled                │
│ [━━━━━━━━━━━━━━━━━━━━━━] 0%    │
│                                  │
│ [In Person] [Open] [🌐 AZ]      │
└─────────────────────────────────┘
```

### Color Coding

**Enrollment Status Badges**:
- `open` → Blue (default)
- `closed` → Gray (secondary)
- `cancelled` → Red (destructive)

**Delivery Mode Badges**:
- `in_person` → Blue (default)
- `online` → Gray (secondary)
- `hybrid` → Outline

**Published Status**:
- Published: Green checkmark (✓)
- Unpublished: Gray X icon

---

## 📊 Database Schema Used

### Tables Queried

1. **users** - User authentication
2. **staff_members** - Teacher/instructor records
3. **course_instructors** - Teacher-course assignments
4. **course_offerings** - Course offering instances
5. **courses** - Course definitions
6. **academic_terms** - Semester/term information

### Key Relationships

```sql
users (id)
  └── staff_members (user_id)
      └── course_instructors (instructor_id)
          └── course_offerings (course_offering_id)
              ├── courses (course_id)
              └── academic_terms (academic_term_id)
```

### SQL Query

```sql
SELECT
    co.id as offering_id,
    c.code as course_code,
    c.name as course_name_json,
    c.description as course_description_json,
    c.credit_hours,
    c.lecture_hours,
    c.lab_hours,
    c.tutorial_hours,
    c.course_level,
    co.section_code,
    at.term_type,
    at.academic_year,
    co.max_enrollment,
    co.current_enrollment,
    co.delivery_mode,
    co.enrollment_status,
    co.language_of_instruction,
    co.is_published
FROM course_instructors ci
JOIN course_offerings co ON ci.course_offering_id = co.id
JOIN courses c ON co.course_id = c.id
JOIN academic_terms at ON co.academic_term_id = at.id
WHERE ci.instructor_id = %s
ORDER BY at.academic_year DESC, at.term_type, c.code
LIMIT 100
```

---

## 🔧 Implementation Details

### Backend (`backend/app/api/teachers.py`)

#### Models Added

```python
class DetailedCourseInfo(BaseModel):
    offering_id: str
    course_code: str
    course_name: str
    course_description: Optional[str] = None
    credit_hours: int
    lecture_hours: int
    lab_hours: int
    tutorial_hours: int
    course_level: Optional[str] = None
    section_code: str
    semester: str
    academic_year: str
    term_type: str
    max_enrollment: int
    current_enrollment: int
    delivery_mode: Optional[str] = None
    enrollment_status: str
    language_of_instruction: str
    is_published: bool

class TeacherCoursesListResponse(BaseModel):
    total_courses: int
    courses: List[DetailedCourseInfo] = []
```

#### Endpoint Function

```python
@router.get("/me/courses", response_model=TeacherCoursesListResponse)
def get_teacher_courses(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get detailed list of courses taught by the current teacher"""
    
    # Connect to NEW lms database
    conn = psycopg2.connect(dbname="lms", ...)
    
    # Get staff member
    # Get detailed course information
    # Extract multilingual JSONB data
    # Return formatted response
```

**Key Processing**:
- Extracts Azerbaijani text from JSONB `name` and `description` fields
- Maps `term_type` to readable semester names
- Handles NULL values gracefully
- Returns up to 100 courses ordered by relevance

### Frontend (`frontend-teacher/app/dashboard/courses/page.tsx`)

#### State Management

```typescript
const [coursesData, setCoursesData] = useState<CoursesData | null>(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const [searchQuery, setSearchQuery] = useState("");
```

#### Data Fetching

```typescript
useEffect(() => {
  const fetchCourses = async () => {
    const token = localStorage.getItem("access_token");
    const response = await fetch(
      "http://localhost:8000/api/v1/teachers/me/courses",
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    const data = await response.json();
    setCoursesData(data);
  };
  fetchCourses();
}, []);
```

#### Search Filtering

```typescript
const filteredCourses = coursesData?.courses.filter(
  (course) =>
    course.course_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    course.course_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
    course.section_code.toLowerCase().includes(searchQuery.toLowerCase())
) || [];
```

#### Helper Functions

```typescript
// Get badge variant for enrollment status
const getStatusBadgeVariant = (status: string) => {
  switch (status.toLowerCase()) {
    case "open": return "default";
    case "closed": return "secondary";
    case "cancelled": return "destructive";
    default: return "outline";
  }
};

// Format delivery mode text
const formatDeliveryMode = (mode: string | null) => {
  if (!mode) return "Not specified";
  return mode.split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};
```

---

## 🎬 User Flow

1. **User navigates to "My Courses"** in sidebar
2. **Page loads** with skeleton states
3. **API call** fetches courses from backend
4. **Data displays** in responsive grid
5. **User can search** to filter courses
6. **Real-time filtering** updates the grid
7. **Enrollment progress** shown visually
8. **Status badges** color-coded for quick recognition

---

## 📱 Responsive Design

### Desktop (lg: 3 columns)
```
┌──────┐ ┌──────┐ ┌──────┐
│Course│ │Course│ │Course│
└──────┘ └──────┘ └──────┘
```

### Tablet (md: 2 columns)
```
┌──────┐ ┌──────┐
│Course│ │Course│
└──────┘ └──────┘
```

### Mobile (1 column)
```
┌──────┐
│Course│
└──────┘
┌──────┐
│Course│
└──────┘
```

---

## ✅ Testing

### Backend API Test

```bash
TOKEN=$(cat /tmp/teacher_token.txt)
curl -s "http://localhost:8000/api/v1/teachers/me/courses" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected Response**:
```json
{
  "total_courses": 4,
  "courses": [
    {
      "offering_id": "cc8a97c1-c89b-430f-a18b-cd46e4373743",
      "course_code": "SUBJ00690",
      "course_name": "Xarici dildə işgüzar və akademik kommunikasiya- 2",
      "credit_hours": 3,
      "lecture_hours": 0,
      "lab_hours": 0,
      "tutorial_hours": 0,
      "semester": "Fall",
      "academic_year": "2020-2021",
      "max_enrollment": 30,
      "current_enrollment": 0,
      "delivery_mode": "in_person",
      "enrollment_status": "open",
      "language_of_instruction": "az",
      "is_published": true
    },
    // ... 3 more courses
  ]
}
```

### Frontend Test

1. Navigate to http://localhost:3001/dashboard/courses
2. Verify courses display in grid
3. Test search functionality
4. Check responsive layout
5. Verify badges and status indicators

**Checklist**:
- ✅ All 4 courses displayed
- ✅ Credit hours shown correctly (3 credits each)
- ✅ Enrollment bars at 0% (0/30 students)
- ✅ Delivery mode badges show "In Person"
- ✅ Status badges show "Open"
- ✅ Language badges show "AZ"
- ✅ Published status icons displayed
- ✅ Search filters correctly

---

## 🔍 Sample Data

### Teacher: GÜNAY RAMAZANOVA (5GK3GY7)

**Course 1**:
- Code: SUBJ00690
- Name: Xarici dildə işgüzar və akademik kommunikasiya- 2
- Credits: 3
- Enrollment: 0/30
- Status: Open
- Mode: In Person

**Course 2**:
- Code: SUBJ00691
- Name: Xarici dildə işgüzar və akademik kommunikasiya- 3
- Credits: 3
- Enrollment: 0/30
- Status: Open
- Mode: In Person

**Course 3**:
- Code: SUBJ00691 (different section)
- Name: Xarici dildə işgüzar və akademik kommunikasiya- 3
- Credits: 3
- Enrollment: 0/30
- Status: Open
- Mode: In Person

**Course 4**:
- Code: SUBJ69355
- Name: Dövlət idarəçiliyi nəzəriyyəsi
- Credits: 3
- Enrollment: 0/30
- Status: Open
- Mode: In Person

---

## 🚀 Future Enhancements

### Planned Features

1. **Course Details Modal**
   - Click on course card to see full details
   - Course description
   - Learning outcomes
   - Assessment methods
   - Student list

2. **Filtering Options**
   - Filter by semester
   - Filter by enrollment status
   - Filter by delivery mode
   - Filter by academic year

3. **Sorting Options**
   - Sort by course code
   - Sort by enrollment count
   - Sort by semester
   - Sort by credits

4. **Actions**
   - Quick attendance marking
   - View student roster
   - Access course materials
   - Grade management

5. **Statistics**
   - Total students across all courses
   - Average enrollment rate
   - Most enrolled course
   - Least enrolled course

6. **Export**
   - Export course list to PDF
   - Export to CSV
   - Print-friendly view

---

## 📦 Dependencies Used

### Backend
- `psycopg2` - PostgreSQL database adapter
- `psycopg2.extras.RealDictCursor` - Dictionary-based results
- `FastAPI` - API framework
- `Pydantic` - Data validation

### Frontend
- `Next.js 15` - React framework
- `TypeScript` - Type safety
- `shadcn/ui` - UI components
  - Card components
  - Badge component
  - Input component
  - Skeleton component
- `lucide-react` - Icon library
- `Tailwind CSS` - Styling

---

## 🎯 Key Achievements

1. ✅ **Real Database Integration**: Uses NEW lms database
2. ✅ **Comprehensive Data**: Shows all course details
3. ✅ **Multilingual Support**: Extracts Azerbaijani names from JSONB
4. ✅ **Responsive Design**: Works on all screen sizes
5. ✅ **Search Functionality**: Filter courses in real-time
6. ✅ **Visual Indicators**: Color-coded status badges
7. ✅ **Progress Tracking**: Enrollment progress bars
8. ✅ **Error Handling**: Graceful error messages
9. ✅ **Loading States**: Skeleton screens for better UX
10. ✅ **Type Safety**: Full TypeScript implementation

---

## 📝 Files Created/Modified

### Created
1. **Backend**: `backend/app/api/teachers.py`
   - Added `DetailedCourseInfo` model (19 fields)
   - Added `TeacherCoursesListResponse` model
   - Added `get_teacher_courses` endpoint (~150 lines)

2. **Frontend**: `frontend-teacher/app/dashboard/courses/page.tsx`
   - Created complete courses page (~340 lines)
   - TypeScript interfaces
   - Data fetching logic
   - Search functionality
   - Responsive grid layout
   - Badge variants
   - Helper functions

### Modified
- **Sidebar**: Already had "My Courses" link pointing to `/dashboard/courses`

---

## ✅ Compliance Check

### Rules Followed
1. ✅ **Real Database**: Uses NEW lms database (not old edu)
2. ✅ **No Mock Data**: All data from actual database records
3. ✅ **shadcn/ui Components**: Only used shadcn components
4. ✅ **TypeScript**: Full TypeScript with strict typing
5. ✅ **Tailwind CSS**: All styling with Tailwind
6. ✅ **Context7**: Used Context7 for shadcn documentation
7. ✅ **Responsive**: Mobile-first responsive design
8. ✅ **Accessibility**: Proper semantic HTML and ARIA

---

**Status**: ✅ COMPLETE  
**Backend Endpoint**: http://localhost:8000/api/v1/teachers/me/courses  
**Frontend Route**: http://localhost:3001/dashboard/courses  
**Teacher Test Account**: 5GK3GY7 / gunay91  
**Courses Displayed**: 4 real courses from database  
**Database**: lms (NEW)  
**Components**: 100% shadcn/ui  
