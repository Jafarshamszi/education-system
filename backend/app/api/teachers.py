"""
Teachers API router - Updated to use new LMS schema with staff_members table
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import date
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.database import get_db
from app.core.config import settings
from app.models.staff_member import StaffMember
from app.models.person import Person
from app.models.user import User
from app.models.organization_unit import OrganizationUnit
from app.auth import get_current_user, CurrentUser

router = APIRouter(prefix="/teachers", tags=["teachers"])


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


# Pydantic models for responses
class PersonInfo(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    full_name: str

    class Config:
        from_attributes = True


class OrganizationInfo(BaseModel):
    id: UUID
    name: dict  # JSONB field with translations
    name_localized: Optional[str] = None  # Localized name based on language
    code: Optional[str] = None

    class Config:
        from_attributes = True


def get_localized_name(name_dict: Optional[dict], lang: str = 'en') -> Optional[str]:
    """Get localized name from JSONB field with fallback"""
    if not name_dict:
        return None
    # Try requested language, fallback to en, then az, then any available
    return name_dict.get(lang) or name_dict.get('en') or name_dict.get('az') or next(iter(name_dict.values()), None)


class TeacherListResponse(BaseModel):
    id: UUID
    employee_number: str
    person: Optional[PersonInfo] = None
    position_title: Optional[str] = None
    employment_type: Optional[str] = None
    academic_rank: Optional[str] = None
    organization: Optional[OrganizationInfo] = None
    is_active: bool
    hire_date: Optional[date] = None

    class Config:
        from_attributes = True


class PaginatedTeachersResponse(BaseModel):
    count: int
    total_pages: int
    current_page: int
    per_page: int
    results: List[TeacherListResponse]


class TeacherStatsResponse(BaseModel):
    total_teachers: int
    active_teachers: int
    organizations_count: int


@router.get("/", response_model=PaginatedTeachersResponse)
def get_teachers(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    lang: str = Query('en', regex='^(en|ru|az)$'),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get paginated list of teachers (staff members) with filtering

    Args:
        lang: Language code for localized content (en, ru, az)
    """
    # Check permissions - only admins can list teachers
    if not current_user.has_role("ADMIN") and not current_user.has_role("SYSADMIN"):
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Base query with joins
        query = db.query(StaffMember).join(
            User, StaffMember.user_id == User.id, isouter=True
        ).join(
            Person, User.id == Person.user_id, isouter=True
        ).outerjoin(
            OrganizationUnit, StaffMember.organization_unit_id == OrganizationUnit.id
        )

        # Apply search filter
        if search:
            search_filter = or_(
                Person.first_name.ilike(f"%{search}%"),
                Person.last_name.ilike(f"%{search}%"),
                Person.middle_name.ilike(f"%{search}%"),
                StaffMember.employee_number.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        # Apply filters
        if organization_id:
            try:
                org_uuid = UUID(organization_id)
                query = query.filter(StaffMember.organization_unit_id == org_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid organization ID format")

        if active is not None:
            query = query.filter(StaffMember.is_active == active)

        # Count total records
        total_count = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        staff_members = query.order_by(
            Person.last_name, Person.first_name
        ).offset(offset).limit(per_page).all()

        # Build response data
        results = []
        for staff in staff_members:
            # Get related data
            person = None
            organization = None

            if staff.user_id:
                person_record = db.query(Person).filter(
                    Person.user_id == staff.user_id
                ).first()
                if person_record:
                    person = PersonInfo(
                        id=person_record.id,
                        first_name=person_record.first_name,
                        last_name=person_record.last_name,
                        middle_name=person_record.middle_name,
                        full_name=person_record.full_name
                    )

            if staff.organization_unit_id:
                org_record = db.query(OrganizationUnit).filter(
                    OrganizationUnit.id == staff.organization_unit_id
                ).first()
                if org_record:
                    organization = OrganizationInfo(
                        id=org_record.id,
                        name=org_record.name,
                        name_localized=get_localized_name(org_record.name, lang),
                        code=org_record.code
                    )

            teacher_data = TeacherListResponse(
                id=staff.id,
                employee_number=staff.employee_number,
                person=person,
                position_title=staff.position_title_en or staff.position_title_az,
                employment_type=staff.employment_type,
                academic_rank=staff.academic_rank,
                organization=organization,
                is_active=staff.is_active or False,
                hire_date=staff.hire_date
            )
            results.append(teacher_data)

        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

        return PaginatedTeachersResponse(
            count=total_count,
            total_pages=total_pages,
            current_page=page,
            per_page=per_page,
            results=results
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve teachers: {str(e)}"
        )


@router.get("/stats", response_model=TeacherStatsResponse)
def get_teacher_stats(db: Session = Depends(get_db)):
    """
    Get teacher statistics
    """
    try:
        total_teachers = db.query(StaffMember).count()
        active_teachers = db.query(StaffMember).filter(
            StaffMember.is_active == True
        ).count()
        organizations_count = db.query(
            func.count(func.distinct(StaffMember.organization_unit_id))
        ).filter(
            StaffMember.organization_unit_id.isnot(None)
        ).scalar()

        return TeacherStatsResponse(
            total_teachers=total_teachers,
            active_teachers=active_teachers,
            organizations_count=organizations_count or 0
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve teacher statistics: {str(e)}"
        )


@router.get("/{teacher_id}", response_model=TeacherListResponse)
def get_teacher_detail(
    teacher_id: UUID,
    lang: str = Query('en', regex='^(en|ru|az)$'),
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific teacher

    Args:
        lang: Language code for localized content (en, ru, az)
    """
    try:
        staff = db.query(StaffMember).filter(
            StaffMember.id == teacher_id
        ).first()

        if not staff:
            raise HTTPException(status_code=404, detail="Teacher not found")

        # Get related data
        person = None
        organization = None

        if staff.user_id:
            person_record = db.query(Person).filter(
                Person.user_id == staff.user_id
            ).first()
            if person_record:
                person = PersonInfo(
                    id=person_record.id,
                    first_name=person_record.first_name,
                    last_name=person_record.last_name,
                    middle_name=person_record.middle_name,
                    full_name=person_record.full_name
                )

        if staff.organization_unit_id:
            org_record = db.query(OrganizationUnit).filter(
                OrganizationUnit.id == staff.organization_unit_id
            ).first()
            if org_record:
                organization = OrganizationInfo(
                    id=org_record.id,
                    name=org_record.name,
                    name_localized=get_localized_name(org_record.name, lang),
                    code=org_record.code
                )

        return TeacherListResponse(
            id=staff.id,
            employee_number=staff.employee_number,
            person=person,
            position_title=staff.position_title_en or staff.position_title_az,
            employment_type=staff.employment_type,
            academic_rank=staff.academic_rank,
            organization=organization,
            is_active=staff.is_active or False,
            hire_date=staff.hire_date
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve teacher: {str(e)}"
        )


# Teacher Dashboard Endpoint Models
class TeacherCourseInfo(BaseModel):
    offering_id: str
    course_code: str
    course_name: str
    student_count: int
    semester: Optional[str] = None
    academic_year: Optional[str] = None
    section_code: Optional[str] = None


# Detailed Course Models
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


class TeacherDashboardResponse(BaseModel):
    teacher_id: str
    employee_number: str
    full_name: str
    position_title: Optional[str] = None
    academic_rank: Optional[str] = None
    department: Optional[str] = None
    total_courses: int
    total_students: int
    courses: List[TeacherCourseInfo] = []


class StudentInfo(BaseModel):
    student_id: str
    student_number: str
    full_name: str
    email: Optional[str] = None
    enrollment_date: Optional[str] = None
    enrollment_status: str
    grade: Optional[str] = None
    grade_points: Optional[float] = None
    attendance_percentage: Optional[float] = None
    status: str
    study_mode: Optional[str] = None
    gpa: Optional[float] = None


class CourseStudentsInfo(BaseModel):
    offering_id: str
    course_code: str
    course_name: str
    section_code: str
    semester: str
    academic_year: str
    total_enrolled: int
    students: List[StudentInfo] = []


class TeacherStudentsResponse(BaseModel):
    total_courses: int
    total_unique_students: int
    courses: List[CourseStudentsInfo] = []


# Attendance Models
class AttendanceStudentInfo(BaseModel):
    student_id: str
    student_number: str
    full_name: str
    email: Optional[str] = None
    status: Optional[str] = None  # Current attendance status if exists
    notes: Optional[str] = None


class AttendanceCourseInfo(BaseModel):
    offering_id: str
    course_code: str
    course_name: str
    section_code: str
    semester: str
    academic_year: str
    schedule_id: Optional[str] = None
    class_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class AttendanceRequest(BaseModel):
    class_schedule_id: str
    attendance_date: str  # YYYY-MM-DD format
    records: List[dict]  # [{student_id: str, status: str, notes: Optional[str]}]


class AttendanceRecordResponse(BaseModel):
    id: str
    student_id: str
    student_number: str
    full_name: str
    status: str
    notes: Optional[str] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None


# Grades-related models
class GradeStudentInfo(BaseModel):
    student_id: str
    student_number: str
    full_name: str
    email: Optional[str] = None
    grade_value: Optional[float] = None
    notes: Optional[str] = None
    graded_at: Optional[str] = None


class AssessmentInfo(BaseModel):
    assessment_id: str
    title: str
    assessment_type: str
    total_marks: float
    due_date: Optional[str] = None
    student_count: int


class GradeRecord(BaseModel):
    student_id: str
    grade_value: Optional[float] = None
    notes: Optional[str] = None


class GradeSubmitRequest(BaseModel):
    course_offering_id: str
    assessment_id: Optional[str] = None  # If null, create new assessment
    assessment_title: str
    assessment_type: str  # exam, quiz, assignment, project, presentation, participation, lab, other
    total_marks: float
    assessment_date: str  # YYYY-MM-DD format
    grades: List[GradeRecord]


@router.get("/me/dashboard", response_model=TeacherDashboardResponse)
def get_teacher_dashboard(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current authenticated teacher's dashboard data

    Returns teacher information and courses they are teaching
    with real data from the NEW database (lms schema).
    """
    
    try:
        # Use data from current_user authentication
        full_name = current_user.full_name
        employee_number = current_user.username  # Account username
        
        # Connect to NEW lms database to get real teacher data
        conn = psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get teacher/staff information from NEW database
        # Find staff member by username
        cur.execute("""
            SELECT
                u.id as user_id,
                s.id as staff_id,
                s.employee_number,
                s.position_title,
                s.academic_rank,
                s.organization_unit_id
            FROM users u
            JOIN staff_members s ON u.id = s.user_id
            WHERE u.username = %s AND s.is_active = true
            LIMIT 1
        """, [employee_number])
        
        staff_record = cur.fetchone()
        
        if not staff_record:
            # Staff member not found in new DB, return empty data
            cur.close()
            conn.close()
            return TeacherDashboardResponse(
                teacher_id=str(current_user.id),
                employee_number=employee_number,
                full_name=full_name,
                position_title=None,
                academic_rank=None,
                department=None,
                total_courses=0,
                total_students=0,
                courses=[]
            )
        
        user_id = staff_record['user_id']
        position_title_json = staff_record.get('position_title', {})
        if isinstance(position_title_json, dict):
            position_title = position_title_json.get('az')
        else:
            position_title = None
        academic_rank = staff_record.get('academic_rank')

        # Get real courses taught by this instructor with student counts
        cur.execute("""
            SELECT
                co.id as offering_id,
                c.code as course_code,
                c.name as course_name_json,
                co.section_code,
                at.term_type,
                at.academic_year,
                co.current_enrollment as student_count
            FROM course_instructors ci
            JOIN course_offerings co ON ci.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            JOIN academic_terms at ON co.academic_term_id = at.id
            WHERE ci.instructor_id = %s
            ORDER BY at.academic_year DESC, at.term_type
            LIMIT 20
        """, [user_id])

        course_records = cur.fetchall()

        # Convert to TeacherCourseInfo objects
        courses = []
        for record in course_records:
            # Extract course name from JSONB
            course_name_json = record.get('course_name_json', {})
            if isinstance(course_name_json, dict):
                course_name = course_name_json.get('az', 'Course')
            else:
                course_name = 'Course'

            # Map term_type to semester
            term_type = record.get('term_type', '').lower()
            semester = None
            if term_type == 'fall':
                semester = "Fall"
            elif term_type == 'spring':
                semester = "Spring"
            elif term_type == 'summer':
                semester = "Summer"

            courses.append(TeacherCourseInfo(
                offering_id=str(record['offering_id']),
                course_code=record['course_code'] or "UNKNOWN",
                course_name=course_name,
                student_count=int(record['student_count'] or 0),
                semester=semester,
                academic_year=record.get('academic_year'),
                section_code=record.get('section_code')
            ))

        total_students = sum(c.student_count for c in courses)

        cur.close()
        conn.close()

        return TeacherDashboardResponse(
            teacher_id=str(current_user.id),
            employee_number=employee_number,
            full_name=full_name,
            position_title=position_title,
            academic_rank=academic_rank,
            # TODO: Get department name from organization_unit_id
            department=None,
            total_courses=len(courses),
            total_students=total_students,
            courses=courses
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching dashboard data: {str(e)}"
        )


@router.get("/me/courses", response_model=TeacherCoursesListResponse)
def get_teacher_courses(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get detailed list of courses taught by the current teacher

    Returns comprehensive course information including credits,
    enrollment, schedule details from the NEW database (lms schema).
    """

    try:
        employee_number = current_user.username

        # Connect to NEW lms database
        conn = psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get staff member
        cur.execute("""
            SELECT u.id as user_id
            FROM users u
            JOIN staff_members s ON u.id = s.user_id
            WHERE u.username = %s AND s.is_active = true
            LIMIT 1
        """, [employee_number])

        staff_record = cur.fetchone()

        if not staff_record:
            cur.close()
            conn.close()
            return TeacherCoursesListResponse(
                total_courses=0,
                courses=[]
            )

        user_id = staff_record['user_id']

        # Get detailed course information
        cur.execute("""
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
        """, [user_id])

        course_records = cur.fetchall()

        # Convert to DetailedCourseInfo objects
        courses = []
        for record in course_records:
            # Extract multilingual fields
            course_name_json = record.get('course_name_json', {})
            if isinstance(course_name_json, dict):
                course_name = course_name_json.get('az', 'Course')
            else:
                course_name = 'Course'

            course_desc_json = record.get('course_description_json', {})
            if isinstance(course_desc_json, dict):
                course_description = course_desc_json.get('az')
            else:
                course_description = None

            # Map term_type to semester
            term_type = record.get('term_type', '').lower()
            semester = "Unknown"
            if term_type == 'fall':
                semester = "Fall"
            elif term_type == 'spring':
                semester = "Spring"
            elif term_type == 'summer':
                semester = "Summer"

            courses.append(DetailedCourseInfo(
                offering_id=str(record['offering_id']),
                course_code=record['course_code'] or "UNKNOWN",
                course_name=course_name,
                course_description=course_description,
                credit_hours=int(record['credit_hours'] or 0),
                lecture_hours=int(record['lecture_hours'] or 0),
                lab_hours=int(record['lab_hours'] or 0),
                tutorial_hours=int(record['tutorial_hours'] or 0),
                course_level=record.get('course_level'),
                section_code=record.get('section_code') or "",
                semester=semester,
                academic_year=record.get('academic_year') or "Unknown",
                term_type=term_type,
                max_enrollment=int(record['max_enrollment'] or 0),
                current_enrollment=int(record['current_enrollment'] or 0),
                delivery_mode=record.get('delivery_mode'),
                enrollment_status=record.get('enrollment_status') or "open",
                language_of_instruction=(
                    record.get('language_of_instruction') or "az"
                ),
                is_published=bool(record.get('is_published', False))
            ))

        cur.close()
        conn.close()

        return TeacherCoursesListResponse(
            total_courses=len(courses),
            courses=courses
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching courses: {str(e)}"
        )


@router.get("/me/students", response_model=TeacherStudentsResponse)
def get_teacher_students(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get all students enrolled in the current teacher's courses.
    Returns students grouped by course.
    """
    try:
        employee_number = current_user.username
        
        if not employee_number:
            raise HTTPException(
                status_code=401,
                detail="Invalid user session"
            )
        
        # Connect to lms database
        conn = psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=str(settings.DB_PORT),
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()
        
        # Get teacher's user_id from staff_members
        cur.execute("""
            SELECT u.id as user_id
            FROM users u
            JOIN staff_members s ON u.id = s.user_id
            WHERE u.username = %s AND s.is_active = true
        """, [employee_number])
        
        teacher_result = cur.fetchone()
        if not teacher_result:
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=404,
                detail="Teacher not found or inactive"
            )
        
        user_id = teacher_result['user_id']
        
        # Get all courses taught by this teacher with enrolled students
        cur.execute("""
            SELECT
                co.id as offering_id,
                c.code as course_code,
                c.name as course_name_json,
                co.section_code,
                at.term_type,
                at.academic_year,
                ce.student_id,
                s.student_number,
                p.first_name,
                p.last_name,
                u.email,
                s.enrollment_date,
                ce.enrollment_status,
                ce.grade,
                ce.grade_points,
                ce.attendance_percentage,
                s.status as student_status,
                s.study_mode,
                s.gpa
            FROM course_instructors ci
            JOIN course_offerings co ON ci.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            JOIN academic_terms at ON co.academic_term_id = at.id
            LEFT JOIN course_enrollments ce 
                ON co.id = ce.course_offering_id
                AND ce.enrollment_status IN ('enrolled', 'completed')
            LEFT JOIN students s ON ce.student_id = s.id
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            WHERE ci.instructor_id = %s
            ORDER BY 
                at.academic_year DESC, 
                at.term_type, 
                c.code, 
                p.last_name, 
                p.first_name
        """, [user_id])
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        # Group students by course
        courses_dict = {}
        unique_students = set()
        
        for record in results:
            offering_id = str(record['offering_id'])
            
            # Extract course name from JSONB
            course_name_json = record.get('course_name_json', {})
            if isinstance(course_name_json, dict):
                course_name = course_name_json.get('az', 'Course')
            else:
                course_name = 'Course'
            
            # Map term_type to readable semester
            term_type = record.get('term_type', '')
            if term_type == 'fall':
                semester = "Fall"
            elif term_type == 'spring':
                semester = "Spring"
            elif term_type == 'summer':
                semester = "Summer"
            else:
                semester = term_type.title() if term_type else "Unknown"
            
            # Initialize course if not exists
            if offering_id not in courses_dict:
                courses_dict[offering_id] = {
                    'offering_id': offering_id,
                    'course_code': record['course_code'],
                    'course_name': course_name,
                    'section_code': record['section_code'],
                    'semester': semester,
                    'academic_year': record['academic_year'],
                    'students': []
                }
            
            # Add student if exists (LEFT JOIN might return null students)
            if record['student_id']:
                student_id = str(record['student_id'])
                unique_students.add(student_id)
                
                full_name = f"{record.get('first_name', '')} {record.get('last_name', '')}".strip()
                
                student_info = {
                    'student_id': student_id,
                    'student_number': record['student_number'],
                    'full_name': full_name or 'Unknown',
                    'email': record.get('email'),
                    'enrollment_date': str(record['enrollment_date']) if record.get('enrollment_date') else None,
                    'enrollment_status': record['enrollment_status'],
                    'grade': record.get('grade'),
                    'grade_points': float(record['grade_points']) if record.get('grade_points') else None,
                    'attendance_percentage': float(record['attendance_percentage']) if record.get('attendance_percentage') else None,
                    'status': record.get('student_status', 'unknown'),
                    'study_mode': record.get('study_mode'),
                    'gpa': float(record['gpa']) if record.get('gpa') else None
                }
                
                courses_dict[offering_id]['students'].append(student_info)
        
        # Convert to list and add total_enrolled count
        courses_list = []
        for course_data in courses_dict.values():
            course_data['total_enrolled'] = len(course_data['students'])
            courses_list.append(CourseStudentsInfo(**course_data))
        
        return TeacherStudentsResponse(
            total_courses=len(courses_list),
            total_unique_students=len(unique_students),
            courses=courses_list
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching students: {str(e)}"
        )


@router.get("/me/class-schedules")
def get_teacher_schedules(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all class schedules for the current teacher's courses"""
    try:
        employee_number = current_user.username

        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()

        # Get user_id from employee_number
        cur.execute("""
            SELECT sm.user_id
            FROM staff_members sm
            WHERE sm.employee_number = %s
            LIMIT 1
        """, [employee_number])

        staff_record = cur.fetchone()
        if not staff_record:
            cur.close()
            conn.close()
            return []

        user_id = staff_record['user_id']

        query = """
            SELECT
                cs.id as schedule_id,
                cs.course_offering_id,
                cs.day_of_week,
                cs.start_time,
                cs.end_time,
                cs.schedule_type,
                co.section_code,
                c.code as course_code,
                c.name as course_name,
                at.term_type as semester,
                at.academic_year
            FROM class_schedules cs
            JOIN course_offerings co ON cs.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            JOIN academic_terms at ON co.academic_term_id = at.id
            JOIN course_instructors ci
                ON co.id = ci.course_offering_id
            WHERE ci.instructor_id = %s
            AND cs.is_recurring = true
            ORDER BY
                at.academic_year DESC,
                at.term_type,
                c.code,
                cs.day_of_week,
                cs.start_time
        """

        cur.execute(query, (user_id,))
        records = cur.fetchall()

        schedules = []
        for record in records:
            course_name = record['course_name']
            if isinstance(course_name, dict):
                course_name = (course_name.get('en') or
                              course_name.get('az') or
                              str(course_name))

            schedules.append({
                'schedule_id': str(record['schedule_id']),
                'offering_id': str(record['course_offering_id']),
                'course_code': record['course_code'],
                'course_name': course_name,
                'section_code': record['section_code'],
                'semester': record['semester'],
                'academic_year': record['academic_year'],
                'day_of_week': record['day_of_week'],
                'start_time': str(record['start_time']),
                'end_time': str(record['end_time']),
                'schedule_type': record['schedule_type']
            })

        cur.close()
        conn.close()
        return schedules

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching schedules: {str(e)}"
        )


@router.get("/me/attendance/{class_schedule_id}/{attendance_date}")
def get_attendance_for_class(
    class_schedule_id: str,
    attendance_date: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get students and their attendance for a specific class and date"""
    try:
        employee_number = current_user.username

        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()

        # Get user_id from employee_number
        cur.execute("""
            SELECT sm.user_id
            FROM staff_members sm
            WHERE sm.employee_number = %s
            LIMIT 1
        """, [employee_number])

        staff_record = cur.fetchone()
        if not staff_record:
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=404,
                detail="Teacher not found"
            )

        user_id = staff_record['user_id']

        # Verify teacher owns this schedule
        verify_query = """
            SELECT cs.id
            FROM class_schedules cs
            JOIN course_instructors ci
                ON cs.course_offering_id = ci.course_offering_id
            WHERE cs.id = %s AND ci.instructor_id = %s
        """

        cur.execute(verify_query, (class_schedule_id, user_id))
        if not cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="Not authorized for this class schedule"
            )

        # Get students and attendance
        query = """
            SELECT
                s.id as student_id,
                s.student_number,
                p.first_name,
                p.last_name,
                u.email,
                ar.id as attendance_id,
                ar.status,
                ar.notes,
                ar.check_in_time,
                ar.check_out_time
            FROM class_schedules cs
            JOIN course_enrollments ce
                ON cs.course_offering_id = ce.course_offering_id
            JOIN students s ON ce.student_id = s.id
            JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            LEFT JOIN attendance_records ar
                ON ar.class_schedule_id = cs.id
                AND ar.student_id = s.id
                AND ar.attendance_date = %s
            WHERE cs.id = %s
            AND ce.enrollment_status = 'enrolled'
            ORDER BY p.last_name, p.first_name
        """

        cur.execute(query, (attendance_date, class_schedule_id))
        records = cur.fetchall()

        students = []
        for record in records:
            full_name = (f"{record.get('first_name', '')} "
                        f"{record.get('last_name', '')}").strip()

            students.append({
                'student_id': str(record['student_id']),
                'student_number': record['student_number'],
                'full_name': full_name or 'Unknown',
                'email': record.get('email'),
                'attendance_id': (str(record['attendance_id'])
                                 if record.get('attendance_id') else None),
                'status': record.get('status'),
                'notes': record.get('notes'),
                'check_in_time': (str(record['check_in_time'])
                                 if record.get('check_in_time') else None),
                'check_out_time': (str(record['check_out_time'])
                                  if record.get('check_out_time') else None)
            })

        cur.close()
        conn.close()

        return {
            'class_schedule_id': class_schedule_id,
            'attendance_date': attendance_date,
            'total_students': len(students),
            'students': students
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching attendance: {str(e)}"
        )


@router.get("/me/attendance/check")
def check_attendance_status(
    course_offering_id: str,
    attendance_date: str,  # YYYY-MM-DD format
    current_user: CurrentUser = Depends(get_current_user)
):
    """Check if attendance has been submitted for a specific course and date"""
    try:
        employee_number = current_user.username

        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()

        # Get user_id from employee_number
        cur.execute("""
            SELECT sm.user_id
            FROM staff_members sm
            WHERE sm.employee_number = %s
            LIMIT 1
        """, [employee_number])

        staff_record = cur.fetchone()
        if not staff_record:
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=404,
                detail="Teacher not found"
            )

        user_id = staff_record['user_id']

        # Verify teacher owns this course
        cur.execute("""
            SELECT ci.id
            FROM course_instructors ci
            WHERE ci.course_offering_id = %s AND ci.instructor_id = %s
        """, [course_offering_id, user_id])

        if not cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="Not authorized for this course"
            )

        # Check if attendance records exist for this date
        cur.execute("""
            SELECT 
                ar.id,
                ar.student_id,
                ar.status,
                ar.notes,
                u.username as student_number,
                p.first_name || ' ' || p.last_name as full_name
            FROM attendance_records ar
            JOIN class_schedules cs ON ar.class_schedule_id = cs.id
            JOIN users u ON ar.student_id = u.id
            JOIN persons p ON u.person_id = p.id
            WHERE cs.course_offering_id = %s
                AND ar.attendance_date = %s
            ORDER BY p.last_name, p.first_name
        """, [course_offering_id, attendance_date])

        attendance_records = cur.fetchall()

        cur.close()
        conn.close()

        # Build response
        has_attendance = len(attendance_records) > 0
        
        student_attendance = {}
        for record in attendance_records:
            student_attendance[str(record['student_id'])] = {
                'student_id': str(record['student_id']),
                'student_number': record['student_number'],
                'full_name': record['full_name'],
                'status': record['status'],
                'notes': record['notes']
            }

        return {
            'has_attendance': has_attendance,
            'attendance_date': attendance_date,
            'course_offering_id': course_offering_id,
            'total_records': len(attendance_records),
            'student_attendance': student_attendance
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking attendance status: {str(e)}"
        )


@router.post("/me/attendance")
def submit_attendance(
    attendance_data: AttendanceRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Submit or update attendance records for a class"""
    try:
        employee_number = current_user.username

        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()

        # Get user_id from employee_number
        cur.execute("""
            SELECT sm.user_id
            FROM staff_members sm
            WHERE sm.employee_number = %s
            LIMIT 1
        """, [employee_number])

        staff_record = cur.fetchone()
        if not staff_record:
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=404,
                detail="Teacher not found"
            )

        user_id = staff_record['user_id']

        # Verify teacher owns this schedule
        verify_query = """
            SELECT cs.id
            FROM class_schedules cs
            JOIN course_instructors ci
                ON cs.course_offering_id = ci.course_offering_id
            WHERE cs.id = %s AND ci.instructor_id = %s
        """

        cur.execute(verify_query,
                   (attendance_data.class_schedule_id, user_id))
        if not cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="Not authorized for this class schedule"
            )

        # Insert or update attendance records
        for record in attendance_data.records:
            upsert_query = """
                INSERT INTO attendance_records (
                    class_schedule_id,
                    student_id,
                    attendance_date,
                    status,
                    notes,
                    marked_by,
                    marked_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (class_schedule_id,
                            student_id, attendance_date)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    notes = EXCLUDED.notes,
                    marked_by = EXCLUDED.marked_by,
                    marked_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """

            cur.execute(upsert_query, (
                attendance_data.class_schedule_id,
                record['student_id'],
                attendance_data.attendance_date,
                record['status'],
                record.get('notes'),
                user_id
            ))

        conn.commit()
        cur.close()
        conn.close()

        return {
            "success": True,
            "message": (f"Attendance saved for "
                       f"{len(attendance_data.records)} students"),
            "records_updated": len(attendance_data.records)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting attendance: {str(e)}"
        )


# Grades endpoints
@router.get("/me/assessments")
def get_teacher_assessments(
    course_offering_id: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get assessments for teacher's courses
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get teacher's user ID
        cur.execute("""
            SELECT id FROM users WHERE username = %s
        """, [current_user.username])

        teacher_user = cur.fetchone()
        if not teacher_user:
            raise HTTPException(status_code=404, detail="Teacher not found")

        teacher_id = teacher_user['id']

        # Build query based on filters
        query = """
            SELECT
                a.id as assessment_id,
                a.title,
                a.assessment_type,
                a.total_marks,
                a.due_date,
                c.code as course_code,
                c.name as course_name,
                co.section_code,
                COUNT(DISTINCT ce.student_id) as student_count
            FROM assessments a
            JOIN course_offerings co ON a.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            JOIN course_instructors ci ON co.id = ci.course_offering_id
            LEFT JOIN course_enrollments ce ON co.id = ce.course_offering_id
            WHERE ci.instructor_id = %s
        """

        params = [teacher_id]

        if course_offering_id:
            query += " AND co.id = %s"
            params.append(course_offering_id)

        query += """
            GROUP BY a.id, a.title, a.assessment_type, a.total_marks,
                     a.due_date, c.code, c.name, co.section_code
            ORDER BY a.due_date DESC NULLS LAST, a.created_at DESC
        """

        cur.execute(query, params)
        assessments = cur.fetchall()

        # Format response
        result = []
        for assessment in assessments:
            result.append({
                "assessment_id": str(assessment['assessment_id']),
                "title": assessment['title']['en']
                if isinstance(assessment['title'], dict)
                else assessment['title'],
                "assessment_type": assessment['assessment_type'],
                "total_marks": float(assessment['total_marks']),
                "due_date": (
                    assessment['due_date'].isoformat()
                    if assessment['due_date']
                    else None
                ),
                "course_code": assessment['course_code'],
                "course_name": (
                    assessment['course_name']['en']
                    if isinstance(assessment['course_name'], dict)
                    else assessment['course_name']
                ),
                "section_code": assessment['section_code'],
                "student_count": assessment['student_count']
            })

        cur.close()
        conn.close()

        return {"assessments": result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching assessments: {str(e)}"
        )


@router.get("/me/grades/{assessment_id}")
def get_assessment_grades(
    assessment_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get grades for a specific assessment
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Verify teacher has access to this assessment
        cur.execute("""
            SELECT id FROM users WHERE username = %s
        """, [current_user.username])

        teacher_user = cur.fetchone()
        if not teacher_user:
            raise HTTPException(status_code=404, detail="Teacher not found")

        teacher_id = teacher_user['id']

        # Check access
        cur.execute("""
            SELECT a.id
            FROM assessments a
            JOIN course_offerings co ON a.course_offering_id = co.id
            JOIN course_instructors ci ON co.id = ci.course_offering_id
            WHERE a.id = %s AND ci.instructor_id = %s
        """, [assessment_id, teacher_id])

        if not cur.fetchone():
            raise HTTPException(
                status_code=403,
                detail="Access denied to this assessment"
            )

        # Get assessment info
        cur.execute("""
            SELECT
                a.id,
                a.title,
                a.assessment_type,
                a.total_marks,
                a.due_date,
                co.id as course_offering_id
            FROM assessments a
            JOIN course_offerings co ON a.course_offering_id = co.id
            WHERE a.id = %s
        """, [assessment_id])

        assessment = cur.fetchone()

        # Get students and their grades
        cur.execute("""
            SELECT
                s.id as student_id,
                s.student_number,
                p.first_name,
                p.last_name,
                p.middle_name,
                u.email,
                g.marks_obtained as grade_value,
                g.feedback as notes,
                g.graded_at
            FROM students s
            JOIN users u ON s.user_id = u.id
            JOIN persons p ON u.id = p.user_id
            JOIN course_enrollments ce
                ON s.id = ce.student_id
            LEFT JOIN grades g
                ON s.id = g.student_id AND g.assessment_id = %s
            WHERE ce.course_offering_id = %s
            ORDER BY p.last_name, p.first_name
        """, [assessment_id, assessment['course_offering_id']])

        students = cur.fetchall()

        # Format students
        students_data = []
        for student in students:
            full_name = f"{student['first_name']} "
            if student['middle_name']:
                full_name += f"{student['middle_name']} "
            full_name += student['last_name']

            students_data.append({
                "student_id": str(student['student_id']),
                "student_number": student['student_number'],
                "full_name": full_name.strip(),
                "email": student['email'],
                "grade_value": (
                    float(student['grade_value'])
                    if student['grade_value'] is not None
                    else None
                ),
                "notes": student['notes'],
                "graded_at": (
                    student['graded_at'].isoformat()
                    if student['graded_at']
                    else None
                )
            })

        cur.close()
        conn.close()

        return {
            "assessment": {
                "assessment_id": str(assessment['id']),
                "title": (
                    assessment['title']['en']
                    if isinstance(assessment['title'], dict)
                    else assessment['title']
                ),
                "assessment_type": assessment['assessment_type'],
                "total_marks": float(assessment['total_marks']),
                "due_date": (
                    assessment['due_date'].isoformat()
                    if assessment['due_date']
                    else None
                )
            },
            "students": students_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching grades: {str(e)}"
        )


@router.post("/me/grades")
def submit_grades(
    request: GradeSubmitRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Submit or update grades for an assessment
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get teacher's user ID
        cur.execute("""
            SELECT id FROM users WHERE username = %s
        """, [current_user.username])

        teacher_user = cur.fetchone()
        if not teacher_user:
            raise HTTPException(status_code=404, detail="Teacher not found")

        teacher_id = teacher_user['id']

        # Verify teacher has access to course offering
        cur.execute("""
            SELECT ci.id
            FROM course_instructors ci
            WHERE ci.course_offering_id = %s
                AND ci.instructor_id = %s
        """, [request.course_offering_id, teacher_id])

        if not cur.fetchone():
            raise HTTPException(
                status_code=403,
                detail="Access denied to this course"
            )

        # VALIDATION: Check if attendance has been submitted for this date
        cur.execute("""
            SELECT COUNT(*) as attendance_count
            FROM attendance_records ar
            JOIN class_schedules cs ON ar.class_schedule_id = cs.id
            WHERE cs.course_offering_id = %s
                AND ar.attendance_date = %s
        """, [request.course_offering_id, request.assessment_date])

        attendance_check = cur.fetchone()
        if not attendance_check or attendance_check['attendance_count'] == 0:
            raise HTTPException(
                status_code=400,
                detail="Attendance must be submitted before entering grades for this date"
            )

        # Create or get assessment
        assessment_id = request.assessment_id

        if not assessment_id:
            # Create new assessment
            cur.execute("""
                INSERT INTO assessments (
                    course_offering_id,
                    title,
                    assessment_type,
                    total_marks,
                    due_date,
                    created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [
                request.course_offering_id,
                {'en': request.assessment_title},
                request.assessment_type,
                request.total_marks,
                request.assessment_date,
                teacher_id
            ])

            assessment_id = cur.fetchone()['id']

        # Insert or update grades
        grades_saved = 0
        skipped_students = []
        
        for grade in request.grades:
            if grade.grade_value is not None:
                # Check student's attendance status for this date
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
                
                # Check if grade exists
                cur.execute("""
                    SELECT id FROM grades
                    WHERE assessment_id = %s AND student_id = %s
                """, [assessment_id, grade.student_id])

                existing_grade = cur.fetchone()

                if existing_grade:
                    # Update existing grade
                    cur.execute("""
                        UPDATE grades
                        SET marks_obtained = %s,
                            feedback = %s,
                            graded_by = %s,
                            graded_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, [
                        grade.grade_value,
                        grade.notes,
                        teacher_id,
                        existing_grade['id']
                    ])
                else:
                    # Insert new grade
                    cur.execute("""
                        INSERT INTO grades (
                            assessment_id,
                            student_id,
                            marks_obtained,
                            feedback,
                            graded_by
                        )
                        VALUES (%s, %s, %s, %s, %s)
                    """, [
                        assessment_id,
                        grade.student_id,
                        grade.grade_value,
                        grade.notes,
                        teacher_id
                    ])

                grades_saved += 1

        conn.commit()
        cur.close()
        conn.close()

        message = f"Successfully saved grades for {grades_saved} students"
        if skipped_students:
            message += f". Skipped {len(skipped_students)} students (absent/late)"

        return {
            "message": message,
            "assessment_id": str(assessment_id),
            "grades_saved": grades_saved,
            "skipped_students": skipped_students
        }

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting grades: {str(e)}"
        )


# ==================== SCHEDULE ENDPOINTS ====================

class ScheduleClass(BaseModel):
    """Individual class schedule information"""
    schedule_id: str
    day_of_week: int
    day_name: str
    start_time: str
    end_time: str
    course_code: str
    course_name: str
    section_code: str
    room_id: Optional[str] = None
    schedule_type: Optional[str] = None
    enrolled_count: int
    max_enrollment: int


class TeacherScheduleEvent(BaseModel):
    """Calendar event for teacher schedule"""
    id: str
    title: str
    course_code: str
    course_name: str
    section_code: str
    start: str
    end: str
    day_of_week: int
    day_name: str
    room_id: Optional[str] = None
    schedule_type: Optional[str] = None
    enrolled_count: int
    max_enrollment: int
    background_color: str = "#3788d8"


class TeacherScheduleResponse(BaseModel):
    """Teacher schedule response with calendar events"""
    teacher_id: str
    employee_number: str
    full_name: str
    schedule_events: List[TeacherScheduleEvent] = []


@router.get("/me/schedule", response_model=List[ScheduleClass])
async def get_my_schedule(
    day: Optional[int] = Query(None, ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get teacher's class schedule for the day (or specific day)
    
    - **day**: Optional day of week (0=Monday, 6=Sunday). If not provided, returns today's schedule
    - Returns list of classes with time, course, room, and enrollment information
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get instructor_id from current user
        cur.execute("""
            SELECT id FROM users WHERE username = %s
        """, [current_user.username])
        
        teacher_user = cur.fetchone()
        if not teacher_user:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        instructor_id = teacher_user['id']
        
        # Get day of week (use provided day or today)
        if day is not None:
            day_of_week = day
        else:
            from datetime import datetime
            day_of_week = datetime.now().weekday()  # 0=Monday
        
        # Get schedule for the specified day
        cur.execute("""
            SELECT 
                cs.id::text as schedule_id,
                cs.day_of_week,
                cs.start_time,
                cs.end_time,
                cs.room_id::text as room_id,
                cs.schedule_type,
                c.code as course_code,
                c.name as course_name,
                co.section_code,
                co.max_enrollment,
                co.current_enrollment as enrolled_count
            FROM course_instructors ci
            JOIN course_offerings co ON ci.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            JOIN class_schedules cs ON cs.course_offering_id = co.id
            WHERE ci.instructor_id = %s
            AND cs.day_of_week = %s
            ORDER BY cs.start_time
        """, (instructor_id, day_of_week))
        
        schedules = cur.fetchall()
        
        # Convert to response format
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        result = []
        
        for sch in schedules:
            # Extract English course name from JSONB
            course_name = sch['course_name']
            if isinstance(course_name, dict):
                course_name_en = course_name.get('en', course_name.get('az', course_name.get('ru', 'N/A')))
            else:
                course_name_en = course_name or 'N/A'
            
            result.append(ScheduleClass(
                schedule_id=sch['schedule_id'],
                day_of_week=sch['day_of_week'],
                day_name=days[sch['day_of_week']],
                start_time=str(sch['start_time']),
                end_time=str(sch['end_time']),
                course_code=sch['course_code'],
                course_name=course_name_en,
                section_code=sch['section_code'],
                room_id=sch['room_id'],
                schedule_type=sch['schedule_type'],
                enrolled_count=sch['enrolled_count'] or 0,
                max_enrollment=sch['max_enrollment'] or 0
            ))
        
        cur.close()
        conn.close()
        
        return result

    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching schedule: {str(e)}"
        )


@router.get("/me/schedule/calendar", response_model=TeacherScheduleResponse)
async def get_my_schedule_calendar(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get teacher's class schedule as calendar events for date range

    - **start_date**: Optional start date (YYYY-MM-DD). If not provided, uses current week
    - **end_date**: Optional end date (YYYY-MM-DD). If not provided, uses 4 weeks ahead
    - Returns calendar events formatted for FullCalendar with recurring weekly events
    """
    conn = None
    try:
        from datetime import datetime, timedelta

        conn = get_db_connection()
        cur = conn.cursor()

        # Get instructor info
        cur.execute("""
            SELECT
                u.id,
                u.username,
                p.first_name,
                p.last_name,
                p.middle_name
            FROM users u
            LEFT JOIN persons p ON u.id = p.user_id
            WHERE u.username = %s
        """, [current_user.username])

        teacher_user = cur.fetchone()
        if not teacher_user:
            raise HTTPException(status_code=404, detail="Teacher not found")

        instructor_id = teacher_user['id']

        # Build full name
        full_name_parts = []
        if teacher_user.get('first_name'):
            full_name_parts.append(teacher_user['first_name'])
        if teacher_user.get('middle_name'):
            full_name_parts.append(teacher_user['middle_name'])
        if teacher_user.get('last_name'):
            full_name_parts.append(teacher_user['last_name'])
        full_name = ' '.join(full_name_parts) if full_name_parts else current_user.username

        # Determine date range
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

        # Get schedule templates - group by time slot to avoid duplicates
        # When teacher teaches multiple sections at same time, combine them into one event
        cur.execute("""
            SELECT
                MIN(cs.id::text) as schedule_id,
                cs.day_of_week,
                cs.start_time,
                cs.end_time,
                cs.room_id::text as room_id,
                cs.schedule_type,
                MIN(cs.effective_from) as effective_from,
                MAX(cs.effective_until) as effective_until,
                c.code as course_code,
                c.name as course_name,
                STRING_AGG(DISTINCT co.section_code, ', ' ORDER BY co.section_code) as section_code,
                SUM(co.max_enrollment) as max_enrollment,
                SUM(co.current_enrollment) as enrolled_count,
                COUNT(DISTINCT co.id) as section_count
            FROM course_instructors ci
            JOIN course_offerings co ON ci.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            JOIN class_schedules cs ON cs.course_offering_id = co.id
            WHERE ci.instructor_id = %s
            GROUP BY cs.day_of_week, cs.start_time, cs.end_time, cs.room_id, cs.schedule_type, c.code, c.name
            ORDER BY cs.day_of_week, cs.start_time
        """, [instructor_id])

        schedules_data = cur.fetchall()

        print(f"DEBUG: Found {len(schedules_data)} unique time slots (grouped sections) for teacher")
        print(f"DEBUG: Generating events for range {range_start} to {range_end}")

        schedule_events = []
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Color palette for different courses
        course_colors = {}
        colors = ['#3788d8', '#22c55e', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6', '#f97316']
        color_index = 0

        # Generate recurring weekly events for each schedule template
        for schedule in schedules_data:
            # Assign color per course
            if schedule['course_code'] not in course_colors:
                course_colors[schedule['course_code']] = colors[color_index % len(colors)]
                color_index += 1

            # Extract course name from JSONB
            course_name = schedule['course_name']
            if isinstance(course_name, dict):
                course_name = course_name.get('en', course_name.get('az', course_name.get('ru', 'N/A')))
            else:
                course_name = course_name or 'N/A'

            # Get section info
            section_count = schedule.get('section_count', 1)
            section_display = schedule['section_code']
            
            # Log if multiple sections are grouped
            if section_count > 1:
                print(f"DEBUG: Grouping {section_count} sections at {schedule['start_time']}: {section_display}")

            # Get schedule validity period
            sched_start = schedule.get('effective_from')
            sched_end = schedule.get('effective_until')

            print(f"DEBUG: Schedule {schedule['course_code']} - effective_from: {sched_start}, effective_until: {sched_end}")

            # IMPORTANT: Ignore effective dates for now since all schedules are expired
            # Use the requested range instead
            actual_start = range_start
            actual_end = range_end

            # Find first occurrence of this day of week in range
            current_date = actual_start
            day_offset = (schedule['day_of_week'] - current_date.weekday()) % 7
            first_occurrence = current_date + timedelta(days=day_offset)

            # Generate weekly occurrences (limited to requested range only)
            occurrence_date = first_occurrence
            occurrence_count = 0

            while occurrence_date <= actual_end:
                # Create start and end datetime strings
                start_dt = f"{occurrence_date.strftime('%Y-%m-%d')}T{schedule['start_time']}"
                end_dt = f"{occurrence_date.strftime('%Y-%m-%d')}T{schedule['end_time']}"

                if occurrence_count < 2:  # Debug: Log first 2 occurrences
                    print(f"DEBUG: {schedule['course_code']} occurrence #{occurrence_count}: {start_dt} to {end_dt}")

                schedule_events.append(TeacherScheduleEvent(
                    id=f"{schedule['schedule_id']}_{occurrence_date}",
                    title=f"{schedule['course_code']}",
                    course_code=schedule['course_code'],
                    course_name=course_name,
                    section_code=schedule['section_code'],
                    start=start_dt,
                    end=end_dt,
                    day_of_week=schedule['day_of_week'],
                    day_name=day_names[schedule['day_of_week']],
                    room_id=schedule['room_id'],
                    schedule_type=schedule['schedule_type'],
                    enrolled_count=schedule['enrolled_count'] or 0,
                    max_enrollment=schedule['max_enrollment'] or 0,
                    background_color=course_colors[schedule['course_code']]
                ))

                # Move to next week
                occurrence_date += timedelta(weeks=1)
                occurrence_count += 1

        print(f"DEBUG: Generated total of {len(schedule_events)} events for teacher")

        cur.close()
        conn.close()

        return TeacherScheduleResponse(
            teacher_id=str(instructor_id),
            employee_number=current_user.username,
            full_name=full_name,
            schedule_events=schedule_events
        )

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.close()
        print(f"Error in get_my_schedule_calendar: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching calendar schedule: {str(e)}"
        )
