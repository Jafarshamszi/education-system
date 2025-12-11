"""
Student management API endpoints - Updated for LMS database
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel

from app.core.config import settings
from app.auth import get_current_user, CurrentUser

router = APIRouter(prefix="/students", tags=["students"])


# Database connection function
def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=RealDictCursor
    )


# Pydantic models
class PersonInfo(BaseModel):
    """Person information"""
    id: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None


class AcademicProgramInfo(BaseModel):
    """Academic program information"""
    id: str
    code: str
    name: dict  # JSONB with translations


class StudentResponse(BaseModel):
    """Student response model"""
    id: str
    student_number: str
    person: Optional[PersonInfo] = None
    academic_program: Optional[AcademicProgramInfo] = None
    status: str
    study_mode: Optional[str] = None
    funding_type: Optional[str] = None
    enrollment_date: str
    expected_graduation_date: Optional[str] = None
    gpa: Optional[float] = None
    total_credits_earned: int


class StudentListResponse(BaseModel):
    """Paginated student list response"""
    count: int
    total_pages: int
    current_page: int
    per_page: int
    results: List[StudentResponse]


class StudentStatsResponse(BaseModel):
    """Student statistics"""
    total_students: int
    active_students: int
    graduated_students: int
    average_gpa: Optional[float] = None


@router.get("/", response_model=StudentListResponse)
def get_students(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Results per page"),
    search: Optional[str] = Query(None, description="Search by name or student number"),
    status: Optional[str] = Query(None, description="Filter by status"),
    study_mode: Optional[str] = Query(None, description="Filter by study mode"),
    academic_program_id: Optional[str] = Query(None, description="Filter by program"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get paginated list of students
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Results per page (default: 25, max: 100)
    - search: Search term for name or student number
    - status: Filter by student status
    - study_mode: Filter by study mode
    - academic_program_id: Filter by academic program UUID
    """
    # Check permissions
    if current_user.user_type not in ["ADMIN", "TEACHER", "SYSADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view student list"
        )
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Build WHERE clause
        where_conditions = []
        params = []
        
        print(f"DEBUG: search={search}, status={status}, study_mode={study_mode}, program={academic_program_id}")
        
        if search:
            where_conditions.append("""
                (s.student_number ILIKE %s 
                 OR p.first_name ILIKE %s 
                 OR p.last_name ILIKE %s
                 OR CONCAT(p.first_name, ' ', p.last_name) ILIKE %s)
            """)
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term, search_term])
        
        if status:
            where_conditions.append("s.status = %s")
            params.append(status)
        
        if study_mode:
            where_conditions.append("s.study_mode = %s")
            params.append(study_mode)
        
        if academic_program_id:
            where_conditions.append("s.academic_program_id = %s")
            params.append(academic_program_id)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        print(f"DEBUG: where_clause={where_clause}")
        print(f"DEBUG: params={params}")
        
        # Count total records
        count_query = f"""
            SELECT COUNT(DISTINCT s.id)
            FROM students s
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            {where_clause}
        """
        cur.execute(count_query, params)
        total_count = cur.fetchone()['count']
        print(f"DEBUG: total_count={total_count}")
        total_pages = (total_count + per_page - 1) // per_page
        
        # Get paginated results
        offset = (page - 1) * per_page
        
        query = f"""
            SELECT 
                s.id,
                s.student_number,
                s.status,
                s.study_mode,
                s.funding_type,
                s.enrollment_date,
                s.expected_graduation_date,
                s.gpa,
                s.total_credits_earned,
                p.id as person_id,
                p.first_name,
                p.last_name,
                p.middle_name,
                ap.id as program_id,
                ap.code as program_code,
                ap.name as program_name
            FROM students s
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            LEFT JOIN academic_programs ap ON s.academic_program_id = ap.id
            {where_clause}
            ORDER BY s.enrollment_date DESC, s.student_number
            LIMIT %s OFFSET %s
        """
        
        cur.execute(query, params + [per_page, offset])
        rows = cur.fetchall()
        print(f"DEBUG: rows count={len(rows)}")
        
        # Build response
        students = []
        for row in rows:
            person_info = None
            if row['person_id']:
                person_info = PersonInfo(
                    id=str(row['person_id']),
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    middle_name=row['middle_name']
                )
            
            program_info = None
            if row['program_id']:
                program_info = AcademicProgramInfo(
                    id=str(row['program_id']),
                    code=row['program_code'],
                    name=row['program_name'] or {}
                )
            
            students.append(StudentResponse(
                id=str(row['id']),
                student_number=row['student_number'],
                person=person_info,
                academic_program=program_info,
                status=row['status'],
                study_mode=row['study_mode'],
                funding_type=row['funding_type'],
                enrollment_date=str(row['enrollment_date']),
                expected_graduation_date=str(row['expected_graduation_date']) if row['expected_graduation_date'] else None,
                gpa=float(row['gpa']) if row['gpa'] is not None else None,
                total_credits_earned=row['total_credits_earned']
            ))
        
        return StudentListResponse(
            count=total_count,
            total_pages=total_pages,
            current_page=page,
            per_page=per_page,
            results=students
        )
        
    finally:
        cur.close()
        conn.close()


@router.get("/stats", response_model=StudentStatsResponse)
def get_student_stats():
    """
    Get student statistics
    
    Returns overall statistics including:
    - Total number of students
    - Number of active students
    - Number of graduated students
    - Average GPA across all students
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        query = """
            SELECT 
                COUNT(*) as total_students,
                COUNT(*) FILTER (WHERE status = 'active') as active_students,
                COUNT(*) FILTER (WHERE status = 'graduated') as graduated_students,
                ROUND(AVG(gpa), 2) as average_gpa
            FROM students
        """
        
        cur.execute(query)
        result = cur.fetchone()
        
        return StudentStatsResponse(
            total_students=result['total_students'],
            active_students=result['active_students'],
            graduated_students=result['graduated_students'],
            average_gpa=float(result['average_gpa']) if result['average_gpa'] is not None else None
        )
        
    finally:
        cur.close()
        conn.close()


@router.get("/{student_id}", response_model=StudentResponse)
def get_student_detail(student_id: UUID):
    """
    Get detailed information for a specific student
    
    Path Parameters:
    - student_id: UUID of the student
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        query = """
            SELECT 
                s.id,
                s.student_number,
                s.status,
                s.study_mode,
                s.funding_type,
                s.enrollment_date,
                s.expected_graduation_date,
                s.gpa,
                s.total_credits_earned,
                p.id as person_id,
                p.first_name,
                p.last_name,
                p.middle_name,
                ap.id as program_id,
                ap.code as program_code,
                ap.name as program_name
            FROM students s
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            LEFT JOIN academic_programs ap ON s.academic_program_id = ap.id
            WHERE s.id = %s
        """
        
        cur.execute(query, [str(student_id)])
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Student not found")
        
        person_info = None
        if row['person_id']:
            person_info = PersonInfo(
                id=str(row['person_id']),
                first_name=row['first_name'],
                last_name=row['last_name'],
                middle_name=row['middle_name']
            )
        
        program_info = None
        if row['program_id']:
            program_info = AcademicProgramInfo(
                id=str(row['program_id']),
                code=row['program_code'],
                name=row['program_name'] or {}
            )
        
        return StudentResponse(
            id=str(row['id']),
            student_number=row['student_number'],
            person=person_info,
            academic_program=program_info,
            status=row['status'],
            study_mode=row['study_mode'],
            funding_type=row['funding_type'],
            enrollment_date=str(row['enrollment_date']),
            expected_graduation_date=str(row['expected_graduation_date']) if row['expected_graduation_date'] else None,
            gpa=float(row['gpa']) if row['gpa'] is not None else None,
            total_credits_earned=row['total_credits_earned']
        )
        
    finally:
        cur.close()
        conn.close()


# Student Dashboard Models
class CourseGradeInfo(BaseModel):
    """Course grade information"""
    course_code: str
    course_name: str
    grade: Optional[str] = None
    credits: int


class StudentDashboardResponse(BaseModel):
    """Student dashboard data"""
    full_name: str
    student_number: str
    current_gpa: Optional[float] = None
    total_credits: int
    courses: List[CourseGradeInfo]


@router.get("/me/dashboard", response_model=StudentDashboardResponse)
def get_my_dashboard(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current authenticated student's dashboard data
    
    Returns:
    - Student basic info
    - Current GPA and credits
    - Enrolled courses with grades
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get authenticated student's data
        cur.execute("""
            SELECT
                s.id,
                s.student_number,
                s.gpa,
                s.total_credits_earned,
                s.user_id,
                p.first_name,
                p.last_name,
                p.middle_name
            FROM students s
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            WHERE u.username = %s
        """, [current_user.username])
        
        student = cur.fetchone()
        
        if not student:
            raise HTTPException(
                status_code=404,
                detail="Student profile not found"
            )
        
        full_name = f"{student['first_name']} {student['last_name']}"
        full_name = full_name.strip()
        if student['middle_name']:
            middle = student['middle_name']
            full_name = f"{student['first_name']} {middle} "
            full_name += f"{student['last_name']}".strip()
        
        # Get enrolled courses with grades
        cur.execute("""
            SELECT
                c.code as course_code,
                COALESCE(
                    c.name->>'en',
                    c.name->>'az',
                    c.code
                ) as course_name,
                ce.grade as grade,
                c.credit_hours as credits
            FROM course_enrollments ce
            LEFT JOIN course_offerings co
                ON ce.course_offering_id = co.id
            LEFT JOIN courses c ON co.course_id = c.id
            WHERE ce.student_id = %s
                AND ce.enrollment_status IN ('active', 'completed')
            ORDER BY ce.enrollment_date DESC
            LIMIT 10
        """, [str(student['id'])])
        
        courses = []
        for row in cur.fetchall():
            courses.append(CourseGradeInfo(
                course_code=row['course_code'] or 'N/A',
                course_name=row['course_name'] or 'Unknown Course',
                grade=row['grade'],
                credits=row['credits'] or 0
            ))
        
        gpa_value = None
        if student['gpa']:
            gpa_value = float(student['gpa'])
        
        return StudentDashboardResponse(
            full_name=full_name,
            student_number=student['student_number'],
            current_gpa=gpa_value,
            total_credits=student['total_credits_earned'] or 0,
            courses=courses
        )
        
    finally:
        cur.close()
        conn.close()


class CourseScheduleInfo(BaseModel):
    day_of_week: int
    day_name: str
    start_time: str
    end_time: str
    room: Optional[str] = None
    schedule_type: Optional[str] = None
    instructor_name: Optional[str] = None


class CourseDetailInfo(BaseModel):
    enrollment_id: str
    course_id: str
    course_code: str
    course_name: str
    credits: int
    enrollment_status: str
    grade: Optional[str] = None
    grade_points: Optional[float] = None
    attendance_percentage: Optional[float] = None
    instructor_name: Optional[str] = None
    schedules: List[CourseScheduleInfo] = []
    semester: Optional[str] = None
    academic_year: Optional[str] = None


class StudentCoursesResponse(BaseModel):
    student_id: str
    student_number: str
    full_name: str
    enrolled_courses: List[CourseDetailInfo] = []
    completed_courses: List[CourseDetailInfo] = []

class ClassScheduleEvent(BaseModel):
    id: str
    title: str
    course_code: str
    course_name: str
    start: str
    end: str
    day_of_week: int
    day_name: str
    room: Optional[str] = None
    schedule_type: Optional[str] = None
    instructor_name: Optional[str] = None
    background_color: str = "#3788d8"

class StudentScheduleResponse(BaseModel):
    student_id: str
    student_number: str
    full_name: str
    schedule_events: List[ClassScheduleEvent] = []


@router.get("/me/courses", response_model=StudentCoursesResponse)
def get_my_courses(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get detailed course information for the authenticated student
    including schedules, grades, and instructors.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )
    
    try:
        # Get authenticated student's data
        cur.execute("""
            SELECT
                s.id, s.student_number, s.user_id,
                p.first_name, p.last_name, p.middle_name
            FROM students s
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            WHERE u.username = %s
        """, [current_user.username])
        
        student = cur.fetchone()
        if not student:
            raise HTTPException(
                status_code=404,
                detail="Student profile not found"
            )
        
        full_name = f"{student['first_name']} {student['last_name']}"
        full_name = full_name.strip()
        if student['middle_name']:
            middle = student['middle_name']
            full_name = f"{student['first_name']} {middle} "
            full_name += f"{student['last_name']}".strip()
        
        # Get enrolled courses with full details
        cur.execute("""
            SELECT DISTINCT ON (ce.id)
                ce.id as enrollment_id,
                c.id as course_id,
                c.code as course_code,
                COALESCE(
                    c.name->>'en',
                    c.name->>'az',
                    c.code
                ) as course_name,
                c.credit_hours as credits,
                ce.enrollment_status,
                ce.grade,
                ce.grade_points,
                ce.attendance_percentage,
                co.id as offering_id,
                at.term_type as semester,
                at.academic_year,
                p_inst.first_name as inst_first_name,
                p_inst.last_name as inst_last_name
            FROM course_enrollments ce
            JOIN course_offerings co ON ce.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            LEFT JOIN academic_terms at ON co.academic_term_id = at.id
            LEFT JOIN course_instructors ci
                ON ci.course_offering_id = co.id
                AND ci.role = 'primary'
            LEFT JOIN users u_inst ON ci.instructor_id = u_inst.id
            LEFT JOIN persons p_inst ON u_inst.id = p_inst.user_id
            WHERE ce.student_id = %s
                AND ce.enrollment_status IN ('enrolled', 'active')
            ORDER BY
                ce.id,
                ci.assigned_date ASC,
                at.academic_year DESC,
                at.term_number DESC
        """, [str(student['id'])])
        
        enrolled_courses_data = cur.fetchall()
        enrolled_courses = []
        
        for course_data in enrolled_courses_data:
            # Get schedules for this course offering
            cur.execute("""
                SELECT
                    cs.day_of_week,
                    cs.start_time,
                    cs.end_time,
                    cs.schedule_type,
                    r.room_number as room,
                    p.first_name as inst_first_name,
                    p.last_name as inst_last_name
                FROM class_schedules cs
                LEFT JOIN rooms r ON cs.room_id = r.id
                LEFT JOIN users u ON cs.instructor_id = u.id
                LEFT JOIN persons p ON u.id = p.user_id
                WHERE cs.course_offering_id = %s
                ORDER BY cs.day_of_week, cs.start_time
            """, [str(course_data['offering_id'])])
            
            schedules_data = cur.fetchall()
            schedules = []
            
            day_names = [
                "Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday", "Sunday"
            ]
            
            for sched in schedules_data:
                instructor_name = None
                if sched['inst_first_name'] and sched['inst_last_name']:
                    inst_name = f"{sched['inst_first_name']} "
                    inst_name += f"{sched['inst_last_name']}"
                    instructor_name = inst_name.strip()
                
                schedules.append(CourseScheduleInfo(
                    day_of_week=sched['day_of_week'],
                    day_name=day_names[sched['day_of_week']],
                    start_time=str(sched['start_time']),
                    end_time=str(sched['end_time']),
                    room=sched['room'],
                    schedule_type=sched['schedule_type'],
                    instructor_name=instructor_name
                ))
            
            instructor_name = None
            if course_data['inst_first_name'] and course_data['inst_last_name']:
                inst_name = f"{course_data['inst_first_name']} "
                inst_name += f"{course_data['inst_last_name']}"
                instructor_name = inst_name.strip()
            
            enrolled_courses.append(CourseDetailInfo(
                enrollment_id=str(course_data['enrollment_id']),
                course_id=str(course_data['course_id']),
                course_code=course_data['course_code'],
                course_name=course_data['course_name'],
                credits=course_data['credits'],
                enrollment_status=course_data['enrollment_status'],
                grade=course_data['grade'],
                grade_points=float(course_data['grade_points'])
                    if course_data['grade_points'] else None,
                attendance_percentage=float(course_data['attendance_percentage'])
                    if course_data['attendance_percentage'] else None,
                instructor_name=instructor_name,
                schedules=schedules,
                semester=course_data['semester'],
                academic_year=course_data['academic_year']
            ))
        
        # Get completed courses
        cur.execute("""
            SELECT DISTINCT ON (ce.id)
                ce.id as enrollment_id,
                c.id as course_id,
                c.code as course_code,
                COALESCE(
                    c.name->>'en',
                    c.name->>'az',
                    c.code
                ) as course_name,
                c.credit_hours as credits,
                ce.enrollment_status,
                ce.grade,
                ce.grade_points,
                ce.attendance_percentage,
                at.term_type as semester,
                at.academic_year,
                p_inst.first_name as inst_first_name,
                p_inst.last_name as inst_last_name
            FROM course_enrollments ce
            JOIN course_offerings co ON ce.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            LEFT JOIN academic_terms at ON co.academic_term_id = at.id
            LEFT JOIN course_instructors ci
                ON ci.course_offering_id = co.id
                AND ci.role = 'primary'
            LEFT JOIN users u_inst ON ci.instructor_id = u_inst.id
            LEFT JOIN persons p_inst ON u_inst.id = p_inst.user_id
            WHERE ce.student_id = %s
                AND ce.enrollment_status = 'completed'
            ORDER BY
                ce.id,
                ci.assigned_date ASC,
                at.academic_year DESC,
                at.term_number DESC
            LIMIT 20
        """, [str(student['id'])])
        
        completed_courses_data = cur.fetchall()
        completed_courses = []
        
        for course_data in completed_courses_data:
            instructor_name = None
            if course_data['inst_first_name'] and course_data['inst_last_name']:
                inst_name = f"{course_data['inst_first_name']} "
                inst_name += f"{course_data['inst_last_name']}"
                instructor_name = inst_name.strip()
            
            completed_courses.append(CourseDetailInfo(
                enrollment_id=str(course_data['enrollment_id']),
                course_id=str(course_data['course_id']),
                course_code=course_data['course_code'],
                course_name=course_data['course_name'],
                credits=course_data['credits'],
                enrollment_status=course_data['enrollment_status'],
                grade=course_data['grade'],
                grade_points=float(course_data['grade_points'])
                    if course_data['grade_points'] else None,
                attendance_percentage=float(course_data['attendance_percentage'])
                    if course_data['attendance_percentage'] else None,
                instructor_name=instructor_name,
                schedules=[],
                semester=course_data['semester'],
                academic_year=course_data['academic_year']
            ))
        
        return StudentCoursesResponse(
            student_id=str(student['id']),
            student_number=student['student_number'],
            full_name=full_name,
            enrolled_courses=enrolled_courses,
            completed_courses=completed_courses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_my_courses: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch courses: {str(e)}"
        )
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


@router.get("/me/schedule", response_model=StudentScheduleResponse)
def get_my_schedule(
    current_user: CurrentUser = Depends(get_current_user),
    start_date: str = None,
    end_date: str = None
):
    """
    Get all class schedules for the authenticated student's enrolled courses
    Returns schedule events formatted for FullCalendar with recurring weekly events
    
    Parameters:
    - start_date: ISO format date (YYYY-MM-DD) for range start (optional)
    - end_date: ISO format date (YYYY-MM-DD) for range end (optional)
    
    If no dates provided, returns current week to 4 weeks ahead
    """
    try:
        from datetime import datetime, timedelta
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get student info
        cur.execute("""
            SELECT 
                s.id, 
                s.student_number, 
                u.username,
                p.first_name,
                p.last_name,
                p.middle_name
            FROM students s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            WHERE u.username = %s AND s.status = 'active'
        """, [current_user.username])
        
        student = cur.fetchone()
        
        if not student:
            raise HTTPException(
                status_code=404,
                detail="Student profile not found"
            )
        
        # Build full name
        full_name_parts = []
        if student.get('first_name'):
            full_name_parts.append(student['first_name'])
        if student.get('middle_name'):
            full_name_parts.append(student['middle_name'])
        if student.get('last_name'):
            full_name_parts.append(student['last_name'])
        full_name = ' '.join(full_name_parts) if full_name_parts \
            else student['username']
        
        # Determine date range for schedule
        if start_date and end_date:
            try:
                range_start = datetime.strptime(start_date, '%Y-%m-%d').date()
                range_end = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            # Default: current week to 4 weeks ahead
            today = datetime.now().date()
            range_start = today - timedelta(days=today.weekday())
            range_end = range_start + timedelta(weeks=4)
        
        # Use the database function to get clean, non-conflicting schedule
        cur.execute("""
            SELECT
                schedule_id::text,
                course_code,
                course_name,
                day_of_week,
                start_time,
                end_time,
                room_number as room,
                schedule_type,
                effective_from,
                effective_until,
                SPLIT_PART(instructor_name, ' ', 1) as inst_first_name,
                SPLIT_PART(instructor_name, ' ', 2) as inst_last_name
            FROM get_student_schedule(%s)
        """, [str(student['id'])])
        
        schedules_data = cur.fetchall()

        print(f"DEBUG: Found {len(schedules_data)} unique schedule templates")
        print(f"DEBUG: Generating events for range {range_start} to {range_end}")

        schedule_events = []
        day_names = [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ]
        
        # Color palette for different courses
        course_colors = {}
        colors = [
            "#3788d8", "#22c55e", "#f59e0b",
            "#ec4899", "#8b5cf6", "#14b8a6", "#f97316"
        ]
        color_index = 0
        
        # Generate recurring weekly events for each schedule template
        for schedule in schedules_data:
            # Assign color per course
            if schedule['course_code'] not in course_colors:
                course_colors[schedule['course_code']] = \
                    colors[color_index % len(colors)]
                color_index += 1
            
            # Build instructor name
            instructor_name = None
            if schedule['inst_first_name'] and schedule['inst_last_name']:
                instructor_name = \
                    f"{schedule['inst_first_name']} " \
                    f"{schedule['inst_last_name']}"
            
            # Get schedule validity period
            sched_start = schedule['effective_from']
            sched_end = schedule['effective_until']
            
            # Calculate actual date range intersection
            actual_start = max(range_start, sched_start) \
                if sched_start else range_start
            actual_end = min(range_end, sched_end) \
                if sched_end else range_end
            
            # Find first occurrence of this day of week in range
            current_date = actual_start
            day_offset = (schedule['day_of_week'] - current_date.weekday()) % 7
            first_occurrence = current_date + timedelta(days=day_offset)
            
            # Generate weekly occurrences (limited to requested range only)
            occurrence_date = first_occurrence

            while occurrence_date <= actual_end:
                # Create start and end datetime strings
                start_dt = f"{occurrence_date.strftime('%Y-%m-%d')}" \
                           f"T{schedule['start_time']}"
                end_dt = f"{occurrence_date.strftime('%Y-%m-%d')}" \
                         f"T{schedule['end_time']}"
                
                schedule_events.append(ClassScheduleEvent(
                    id=f"{schedule['schedule_id']}_{occurrence_date}",
                    title=f"{schedule['course_code']}",
                    course_code=schedule['course_code'],
                    course_name=schedule['course_name'],
                    start=start_dt,
                    end=end_dt,
                    day_of_week=schedule['day_of_week'],
                    day_name=day_names[schedule['day_of_week']],
                    room=schedule['room'],
                    schedule_type=schedule['schedule_type'],
                    instructor_name=instructor_name,
                    background_color=course_colors[schedule['course_code']]
                ))

                # Move to next week
                occurrence_date += timedelta(weeks=1)

        print(f"DEBUG: Generated total of {len(schedule_events)} events")

        return StudentScheduleResponse(
            student_id=str(student['id']),
            student_number=student['student_number'],
            full_name=full_name,
            schedule_events=schedule_events
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_my_schedule: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch schedule: {str(e)}"
        )
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


# Grades Models
class AssessmentGrade(BaseModel):
    """Individual assessment grade details"""
    assessment_id: str
    assessment_title: str
    assessment_type: str
    course_code: str
    course_name: str
    total_marks: float
    marks_obtained: Optional[float] = None
    percentage: Optional[float] = None
    letter_grade: Optional[str] = None
    weight_percentage: Optional[float] = None
    feedback: Optional[str] = None
    graded_at: Optional[str] = None
    graded_by_name: Optional[str] = None
    is_final: bool = False


class CourseGradeSummary(BaseModel):
    """Summary of grades for a specific course"""
    course_code: str
    course_name: str
    credit_hours: int
    total_assessments: int
    graded_assessments: int
    average_percentage: Optional[float] = None
    final_grade: Optional[str] = None
    grade_points: Optional[float] = None


class StudentGradesResponse(BaseModel):
    """Student grades overview"""
    student_id: str
    student_number: str
    full_name: str
    current_gpa: Optional[float] = None
    total_credits_earned: int
    course_summaries: List[CourseGradeSummary] = []
    detailed_grades: List[AssessmentGrade] = []


@router.get("/me/grades", response_model=StudentGradesResponse)
def get_my_grades(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get comprehensive grade information for the authenticated student
    
    Returns:
    - Student basic info and GPA
    - Course-level grade summaries
    - Detailed assessment grades with feedback
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )
    
    try:
        # Get authenticated student's data
        cur.execute("""
            SELECT
                s.id, s.student_number, s.gpa, s.total_credits_earned,
                p.first_name, p.last_name, p.middle_name
            FROM students s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            WHERE u.username = %s
        """, [current_user.username])
        
        student = cur.fetchone()
        
        if not student:
            raise HTTPException(
                status_code=404,
                detail="Student profile not found"
            )
        
        # Build full name
        full_name = f"{student['first_name']} {student['last_name']}"
        if student['middle_name']:
            full_name = \
                f"{student['first_name']} {student['middle_name']} " \
                f"{student['last_name']}"
        full_name = full_name.strip()
        
        student_id = str(student['id'])
        
        # Get detailed grades for all assessments
        cur.execute("""
            SELECT
                g.id as grade_id,
                a.id as assessment_id,
                COALESCE(a.title->>'en', a.title->>'az', 
                         'Assessment') as assessment_title,
                a.assessment_type,
                a.total_marks,
                a.weight_percentage,
                g.marks_obtained,
                g.percentage,
                g.letter_grade,
                g.feedback,
                g.graded_at,
                g.is_final,
                c.code as course_code,
                COALESCE(c.name->>'en', c.name->>'az', 
                         c.code) as course_name,
                c.credit_hours,
                p_grader.first_name as grader_first_name,
                p_grader.last_name as grader_last_name
            FROM grades g
            JOIN assessments a ON g.assessment_id = a.id
            JOIN course_offerings co ON a.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            LEFT JOIN users u_grader ON g.graded_by = u_grader.id
            LEFT JOIN persons p_grader ON u_grader.id = p_grader.user_id
            WHERE g.student_id = %s
            ORDER BY g.graded_at DESC NULLS LAST, c.code, a.assessment_type
        """, [student_id])
        
        grades_data = cur.fetchall()
        
        detailed_grades = []
        course_grades_map = {}
        
        for grade in grades_data:
            # Build grader name
            grader_name = None
            if grade['grader_first_name'] and grade['grader_last_name']:
                grader_name = \
                    f"{grade['grader_first_name']} " \
                    f"{grade['grader_last_name']}"
            
            # Add to detailed grades
            detailed_grades.append(AssessmentGrade(
                assessment_id=str(grade['assessment_id']),
                assessment_title=grade['assessment_title'],
                assessment_type=grade['assessment_type'] or 'Other',
                course_code=grade['course_code'],
                course_name=grade['course_name'],
                total_marks=float(grade['total_marks']) \
                    if grade['total_marks'] else 0,
                marks_obtained=float(grade['marks_obtained']) \
                    if grade['marks_obtained'] is not None else None,
                percentage=float(grade['percentage']) \
                    if grade['percentage'] is not None else None,
                letter_grade=grade['letter_grade'],
                weight_percentage=float(grade['weight_percentage']) \
                    if grade['weight_percentage'] else None,
                feedback=grade['feedback'],
                graded_at=grade['graded_at'].isoformat() \
                    if grade['graded_at'] else None,
                graded_by_name=grader_name,
                is_final=grade['is_final'] or False
            ))
            
            # Track course-level statistics
            course_code = grade['course_code']
            if course_code not in course_grades_map:
                course_grades_map[course_code] = {
                    'course_name': grade['course_name'],
                    'credit_hours': grade['credit_hours'] or 0,
                    'total': 0,
                    'graded': 0,
                    'percentages': []
                }
            
            course_grades_map[course_code]['total'] += 1
            if grade['marks_obtained'] is not None:
                course_grades_map[course_code]['graded'] += 1
                if grade['percentage'] is not None:
                    course_grades_map[course_code]['percentages'].append(
                        float(grade['percentage'])
                    )
        
        # Get enrollment grades for final course grades
        cur.execute("""
            SELECT
                c.code as course_code,
                ce.grade as final_grade,
                ce.grade_points
            FROM course_enrollments ce
            JOIN course_offerings co ON ce.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            WHERE ce.student_id = %s
            AND ce.grade IS NOT NULL
        """, [student_id])
        
        enrollment_grades = cur.fetchall()
        enrollment_map = {
            row['course_code']: {
                'final_grade': row['final_grade'],
                'grade_points': float(row['grade_points']) \
                    if row['grade_points'] else None
            }
            for row in enrollment_grades
        }
        
        # Build course summaries
        course_summaries = []
        for course_code, stats in course_grades_map.items():
            avg_pct = None
            if stats['percentages']:
                avg_pct = sum(stats['percentages']) / len(stats['percentages'])
            
            enrollment_info = enrollment_map.get(course_code, {})
            
            course_summaries.append(CourseGradeSummary(
                course_code=course_code,
                course_name=stats['course_name'],
                credit_hours=stats['credit_hours'],
                total_assessments=stats['total'],
                graded_assessments=stats['graded'],
                average_percentage=round(avg_pct, 2) if avg_pct else None,
                final_grade=enrollment_info.get('final_grade'),
                grade_points=enrollment_info.get('grade_points')
            ))
        
        # Sort course summaries by code
        course_summaries.sort(key=lambda x: x.course_code)
        
        return StudentGradesResponse(
            student_id=student_id,
            student_number=student['student_number'],
            full_name=full_name,
            current_gpa=float(student['gpa']) if student['gpa'] else None,
            total_credits_earned=student['total_credits_earned'] or 0,
            course_summaries=course_summaries,
            detailed_grades=detailed_grades
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_my_grades: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch grades: {str(e)}"
        )
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


# ==================== ASSIGNMENTS ENDPOINTS ====================

class AssignmentSubmission(BaseModel):
    """Submission details for an assignment"""
    submission_id: Optional[str] = None
    submitted_at: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    graded_at: Optional[str] = None
    graded_by_name: Optional[str] = None


class Assignment(BaseModel):
    """Individual assignment details"""
    assignment_id: str
    course_code: str
    course_name: str
    title: str
    description: str
    instructions: Optional[str] = None
    due_date: str
    total_marks: float
    weight_percentage: Optional[float] = None
    status: str  # pending, submitted, graded, overdue
    submission: Optional[AssignmentSubmission] = None


class StudentAssignmentsResponse(BaseModel):
    """Response containing all student assignments"""
    student_id: str
    student_number: str
    full_name: str
    total_assignments: int
    pending_count: int
    submitted_count: int
    graded_count: int
    overdue_count: int
    assignments: List[Assignment] = []


@router.get("/me/assignments", response_model=StudentAssignmentsResponse)
async def get_my_assignments(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get all assignments for the authenticated student
    
    Returns:
    - Student basic info
    - Assignment statistics
    - List of all assignments with submission status
    
    NOTE: This is currently using MOCK DATA for demonstration.
    TODO: Connect to real assignments table when available.
    Database currently doesn't have a dedicated assignments table.
    Future implementation should create:
    - assignments table (id, course_id, title, description, due_date, etc.)
    - assignment_submissions table (id, assignment_id, student_id, file, score, etc.)
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )
    
    try:
        # Get authenticated student's data
        cur.execute("""
            SELECT
                s.id, s.student_number, s.gpa,
                p.first_name, p.last_name, p.middle_name
            FROM students s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            WHERE u.username = %s
        """, [current_user.username])
        
        student = cur.fetchone()
        
        if not student:
            raise HTTPException(
                status_code=404,
                detail="Student profile not found"
            )
        
        # Build full name
        full_name = f"{student['first_name']} {student['last_name']}"
        if student['middle_name']:
            full_name = f"{student['first_name']} {student['middle_name']} {student['last_name']}"
        full_name = full_name.strip()
        
        student_id = str(student['id'])
        
        # Get student's enrolled courses for realistic mock data
        cur.execute("""
            SELECT DISTINCT
                c.code as course_code,
                COALESCE(c.name->>'en', c.name->>'az', c.code) as course_name
            FROM course_enrollments ce
            JOIN course_offerings co ON ce.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            WHERE ce.student_id = %s
            LIMIT 5
        """, [student_id])
        
        enrolled_courses = cur.fetchall()
        
        # MOCK DATA - Replace with real database queries when assignments table exists
        from datetime import datetime, timedelta
        
        assignments_list = []
        
        if enrolled_courses:
            # Create realistic mock assignments based on actual enrolled courses
            assignment_templates = [
                {
                    "title": "Weekly Analysis Report",
                    "description": "Analyze the case study and prepare a comprehensive report",
                    "instructions": "1. Read the provided case study\n2. Identify key problems\n3. Propose solutions\n4. Submit as PDF",
                    "days_until_due": 5,
                    "total_marks": 100,
                    "weight": 10,
                    "status": "pending"
                },
                {
                    "title": "Group Project Presentation",
                    "description": "Prepare and submit presentation slides for your group project",
                    "instructions": "1. Create PowerPoint/PDF slides\n2. Include introduction, analysis, conclusions\n3. Maximum 15 slides",
                    "days_until_due": -2,  # Overdue
                    "total_marks": 150,
                    "weight": 15,
                    "status": "overdue"
                },
                {
                    "title": "Research Paper Draft",
                    "description": "Submit first draft of your research paper on assigned topic",
                    "instructions": "1. Minimum 2000 words\n2. Include references (APA format)\n3. Submit as Word document or PDF",
                    "days_until_due": 10,
                    "total_marks": 200,
                    "weight": 20,
                    "status": "pending"
                },
                {
                    "title": "Problem Set #3",
                    "description": "Complete all problems from Chapter 5",
                    "instructions": "1. Show all work\n2. Scan or type solutions\n3. Submit as single PDF file",
                    "days_until_due": -5,  # Submitted
                    "total_marks": 50,
                    "weight": 5,
                    "status": "submitted",
                    "submission": {
                        "submitted_at": (datetime.now() - timedelta(days=5)).isoformat(),
                        "file_name": "problem_set_3.pdf",
                        "file_size": 1024567
                    }
                },
                {
                    "title": "Midterm Project",
                    "description": "Complete midterm project as per requirements",
                    "instructions": "1. Follow project guidelines\n2. Include all required sections\n3. Submit code + documentation",
                    "days_until_due": -15,  # Graded
                    "total_marks": 100,
                    "weight": 25,
                    "status": "graded",
                    "submission": {
                        "submitted_at": (datetime.now() - timedelta(days=15)).isoformat(),
                        "file_name": "midterm_project.zip",
                        "file_size": 5242880,
                        "score": 85.0,
                        "feedback": "Excellent work! Well-structured code and comprehensive documentation. Minor improvements needed in error handling.",
                        "graded_at": (datetime.now() - timedelta(days=10)).isoformat(),
                        "graded_by_name": "GUNAY ORUJOVA"
                    }
                }
            ]
            
            assignment_id = 1
            for idx, course in enumerate(enrolled_courses[:3]):  # Use first 3 courses
                for template_idx, template in enumerate(assignment_templates):
                    if assignment_id > 8:  # Limit total assignments
                        break
                    
                    due_date = datetime.now() + timedelta(days=template["days_until_due"])
                    
                    # Determine status
                    status = template["status"]
                    if status == "pending" and template["days_until_due"] < 0:
                        status = "overdue"
                    
                    submission_data = None
                    if "submission" in template:
                        submission_data = AssignmentSubmission(**template["submission"])
                    
                    assignment = Assignment(
                        assignment_id=str(assignment_id),
                        course_code=course['course_code'],
                        course_name=course['course_name'],
                        title=template["title"],
                        description=template["description"],
                        instructions=template["instructions"],
                        due_date=due_date.isoformat(),
                        total_marks=template["total_marks"],
                        weight_percentage=template["weight"],
                        status=status,
                        submission=submission_data
                    )
                    
                    assignments_list.append(assignment)
                    assignment_id += 1
        
        # Calculate statistics
        pending_count = sum(1 for a in assignments_list if a.status == "pending")
        submitted_count = sum(1 for a in assignments_list if a.status == "submitted")
        graded_count = sum(1 for a in assignments_list if a.status == "graded")
        overdue_count = sum(1 for a in assignments_list if a.status == "overdue")
        
        # Sort by due date (upcoming first)
        assignments_list.sort(key=lambda x: x.due_date)
        
        return StudentAssignmentsResponse(
            student_id=student_id,
            student_number=student['student_number'],
            full_name=full_name,
            total_assignments=len(assignments_list),
            pending_count=pending_count,
            submitted_count=submitted_count,
            graded_count=graded_count,
            overdue_count=overdue_count,
            assignments=assignments_list
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_my_assignments: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch assignments: {str(e)}"
        )
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


from fastapi import UploadFile, File
import os


class SubmissionResponse(BaseModel):
    """Response after submitting an assignment"""
    success: bool
    submission_id: str
    submitted_at: str
    file_name: str
    file_size: int
    message: str


@router.post("/me/assignments/{assignment_id}/submit", response_model=SubmissionResponse)
async def submit_assignment(
    assignment_id: str,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Submit an assignment with file upload
    
    NOTE: This is currently a MOCK implementation for demonstration.
    TODO: Implement real file storage and database recording.
    Future implementation should:
    1. Save file to storage (local/S3/cloud)
    2. Create record in assignment_submissions table
    3. Update assignment status
    4. Send notification to instructor
    """
    try:
        # Validate file type
        allowed_extensions = ['pdf', 'docx', 'doc', 'zip', 'txt', 'jpg', 'png']
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content to get size
        content = await file.read()
        file_size = len(content)
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit"
            )
        
        # MOCK: In real implementation, save file to storage
        # upload_dir = f"uploads/assignments/{current_user.username}/{assignment_id}"
        # os.makedirs(upload_dir, exist_ok=True)
        # file_path = f"{upload_dir}/{file.filename}"
        # with open(file_path, "wb") as f:
        #     f.write(content)
        
        from datetime import datetime
        submission_time = datetime.now().isoformat()
        
        # MOCK: In real implementation, save to database
        # save_submission_to_db(assignment_id, current_user.id, file_path, file_size)
        
        return SubmissionResponse(
            success=True,
            submission_id=f"SUBM_{assignment_id}_{current_user.username}",
            submitted_at=submission_time,
            file_name=file.filename,
            file_size=file_size,
            message="Assignment submitted successfully! (MOCK - file not actually saved)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in submit_assignment: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit assignment: {str(e)}"
        )




