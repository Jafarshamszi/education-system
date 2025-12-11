from fastapi import APIRouter, HTTPException
import os
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings

router = APIRouter(tags=["class-schedule"])


class CourseInfo(BaseModel):
    id: int
    code: str
    subject_name: str
    start_date: Optional[str] = None
    m_hours: Optional[int] = 0
    s_hours: Optional[int] = 0
    l_hours: Optional[int] = 0
    fm_hours: Optional[int] = 0
    total_hours: Optional[int] = 0
    student_count: Optional[int] = 0
    teacher_count: Optional[int] = 0
    active: Optional[bool] = True


class TeacherInfo(BaseModel):
    id: int
    name: str
    organization: Optional[str] = None
    lesson_type: Optional[str] = None


class StudentInfo(BaseModel):
    id: int
    name: str
    student_id_number: Optional[int] = None


class ScheduleStats(BaseModel):
    total_courses: int
    total_students: int
    total_teachers: int
    active_periods: int


class CourseCreate(BaseModel):
    code: str
    subject_name: Optional[str] = None  # Add subject_name field
    start_date: Optional[str] = None
    m_hours: Optional[int] = 0
    s_hours: Optional[int] = 0
    l_hours: Optional[int] = 0
    fm_hours: Optional[int] = 0
    student_count: Optional[int] = 0
    note: Optional[str] = None
    education_plan_subject_id: Optional[int] = None
    semester_id: Optional[int] = None
    education_lang_id: Optional[int] = None
    education_type_id: Optional[int] = None
    education_year_id: Optional[int] = None


class CourseUpdate(BaseModel):
    code: Optional[str] = None
    subject_name: Optional[str] = None  # Add subject_name field
    start_date: Optional[str] = None
    m_hours: Optional[int] = None
    s_hours: Optional[int] = None
    l_hours: Optional[int] = None
    fm_hours: Optional[int] = None
    student_count: Optional[int] = None
    note: Optional[str] = None
    active: Optional[bool] = None


class TeacherAssignment(BaseModel):
    teacher_id: int
    lesson_type_id: Optional[int] = None


class StudentEnrollment(BaseModel):
    student_id: int


class SubjectInfo(BaseModel):
    id: int
    name: str
    code: Optional[str] = None


class EducationLanguage(BaseModel):
    id: int
    name: str


class EducationGroup(BaseModel):
    id: int
    name: str
    education_level_id: int
    education_type_id: int
    education_year_id: int
    education_lang_id: int
    level_name: Optional[str] = None
    year_name: Optional[str] = None
    student_count: Optional[int] = 0


class SemesterInfo(BaseModel):
    id: int
    name: str


class MultipleTeacherAssignment(BaseModel):
    teacher_ids: List[int]


class StudentManagement(BaseModel):
    student_ids_to_add: List[int] = []
    student_ids_to_remove: List[int] = []


class CourseStudentInfo(BaseModel):
    student_id: int
    student_name: str
    student_id_number: Optional[int] = None
    education_group_name: Optional[str] = None
    can_remove: bool = True


class AvailableStudent(BaseModel):
    student_id: int
    student_name: str
    student_id_number: Optional[int] = None
    education_group_name: Optional[str] = None


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=str(settings.DB_PORT)
        )
        return conn
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )


@router.get("/courses/full-schedule/")
def get_full_schedule_data():
    """Get full schedule data - combines courses and stats"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get courses data from new database structure
        courses_query = """
            SELECT
                c.id::text,
                c.code as course_code,
                c.code,
                COALESCE(c.name->>'az', c.name->>'en', 
                         'Unknown Subject') as subject_name,
                COALESCE(c.name->>'az', c.name->>'en', 
                         'Unknown Subject') as course_name,
                c.credit_hours as credits,
                c.lecture_hours as m_hours,
                c.tutorial_hours as s_hours,
                c.lab_hours as l_hours,
                0 as fm_hours,
                (COALESCE(c.lecture_hours, 0) + 
                 COALESCE(c.tutorial_hours, 0) + 
                 COALESCE(c.lab_hours, 0)) as total_hours,
                COUNT(DISTINCT ce.student_id) as student_count,
                COUNT(DISTINCT ci.instructor_id) as teacher_count,
                c.is_active as active,
                c.is_active,
                c.created_at,
                c.updated_at,
                1 as semester_id,
                1 as education_group_id,
                c.id::text as subject_id,
                1 as education_language_id,
                NULL::date as start_date
            FROM courses c
            LEFT JOIN course_offerings co ON co.course_id = c.id
            LEFT JOIN course_enrollments ce ON ce.course_offering_id = co.id
            LEFT JOIN course_instructors ci ON ci.course_offering_id = co.id
            WHERE c.is_active = true
            GROUP BY c.id, c.code, c.name, c.credit_hours, c.lecture_hours,
                     c.tutorial_hours, c.lab_hours, c.is_active, 
                     c.created_at, c.updated_at
            ORDER BY c.code
        """

        cursor.execute(courses_query)
        courses = cursor.fetchall()

        # Get stats data
        cursor.execute(
            "SELECT COUNT(*) as count FROM courses WHERE is_active = true"
        )
        total_courses = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM students")
        total_students = cursor.fetchone()['count']

        cursor.execute(
            "SELECT COUNT(DISTINCT instructor_id) as count "
            "FROM course_instructors"
        )
        total_teachers = cursor.fetchone()['count']

        active_periods = 1  # Default to 1 active period

        cursor.close()
        conn.close()

        return {
            "courses": courses,
            "stats": {
                "total_courses": total_courses,
                "active_courses": total_courses,
                "total_students": total_students,
                "total_teachers": total_teachers,
                "active_periods": active_periods,
                "courses_by_semester": {},
                "courses_by_group": {}
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch full schedule data: {str(e)}"
        )


@router.get("/courses", response_model=List[CourseInfo])
def get_current_courses():
    """Get all current semester courses"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT
                c.id,
                c.code,
                COALESCE(sd.name_az, 'Unknown Subject') as subject_name,
                c.start_date,
                c.m_hours,
                c.s_hours,
                c.l_hours,
                c.fm_hours,
                (COALESCE(c.m_hours, 0) + COALESCE(c.s_hours, 0) + 
                 COALESCE(c.l_hours, 0) + COALESCE(c.fm_hours, 0)) as total_hours,
                c.student_count,
                COUNT(DISTINCT cs.student_id) as teacher_count,
                c.active
            FROM course c
            LEFT JOIN education_plan_subject eps 
                ON eps.id = c.education_plan_subject_id
            LEFT JOIN subject_dic sd ON sd.id = eps.subject_id
            LEFT JOIN course_student cs 
                ON cs.course_id = c.id AND cs.active = 1
            LEFT JOIN course_teacher ct 
                ON ct.course_id = c.id AND ct.active = 1
            WHERE c.active = 1
            GROUP BY c.id, c.code, c.start_date, c.m_hours, c.s_hours,
                     c.l_hours, c.fm_hours, c.student_count, c.active, 
                     sd.name_az, sd.code
            ORDER BY c.code
        """
        
        cursor.execute(query)
        courses = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return courses
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch courses: {str(e)}"
        )


@router.get("/teachers/by-organization/{organization_id}", response_model=List[TeacherInfo])
def get_teachers_by_organization(organization_id: int):
    """Get teachers filtered by organization (kafedra/department) from education group"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                t.id,
                CONCAT(p.firstname, ' ', COALESCE(p.lastname, '')) as name,
                'Organization ID: ' || COALESCE(t.organization_id::text, 'N/A') as organization
            FROM teachers t
            INNER JOIN persons p ON t.person_id = p.id
            WHERE t.active = 1
              AND t.teaching = 1
              AND t.organization_id = %s
            ORDER BY p.lastname, p.firstname
        """

        cursor.execute(query, (organization_id,))
        teachers = cursor.fetchall()

        cursor.close()
        conn.close()

        return teachers

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch teachers by organization: {str(e)}"
        )


@router.get("/teachers", response_model=List[TeacherInfo])
def get_teachers():
    """Get all available teachers for course assignment"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                t.id,
                CONCAT(p.firstname, ' ', COALESCE(p.lastname, '')) as name,
                'Organization ID: ' || COALESCE(t.organization_id::text, 'N/A') as organization
            FROM teachers t
            INNER JOIN persons p ON t.person_id = p.id
            WHERE t.active = 1 AND t.teaching = 1
            ORDER BY p.lastname, p.firstname
            LIMIT 100
        """

        cursor.execute(query)
        teachers = cursor.fetchall()

        cursor.close()
        conn.close()

        return teachers

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch teachers: {str(e)}"
        )


@router.get("/students", response_model=List[StudentInfo])
def get_students():
    """Get all available students"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT DISTINCT
                s.id,
                CONCAT(p.firstname, ' ', COALESCE(p.lastname, '')) as name,
                s.id as student_id_number
            FROM students s
            LEFT JOIN persons p ON p.id = s.person_id
            WHERE s.active = 1
            ORDER BY name
        """
        
        cursor.execute(query)
        students = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return students
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch students: {str(e)}"
        )


@router.get("/courses/{course_id}/teachers", response_model=List[TeacherInfo])
def get_course_teachers(course_id: int):
    """Get teachers assigned to a specific course"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT DISTINCT
                t.id,
                CONCAT(p.firstname, ' ', COALESCE(p.lastname, '')) as name,
                'Unknown Organization' as organization,
                'Unknown Type' as lesson_type,
                p.firstname
            FROM course_teacher ct
            JOIN teachers t ON t.id = ct.teacher_id
            LEFT JOIN persons p ON p.id = t.person_id
            WHERE ct.course_id = %s AND ct.active = 1
            ORDER BY p.firstname
        """
        
        cursor.execute(query, (course_id,))
        teachers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return teachers
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch course teachers: {str(e)}"
        )


@router.get("/courses/{course_id}/students", response_model=List[StudentInfo])
def get_course_students(course_id: int):
    """Get students enrolled in a specific course"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT DISTINCT
                s.id,
                CONCAT(p.firstname, ' ', COALESCE(p.lastname, '')) as name,
                s.id as student_id_number,
                p.firstname
            FROM course_student cs
            JOIN students s ON s.id = cs.student_id
            LEFT JOIN persons p ON p.id = s.person_id
            WHERE cs.course_id = %s AND cs.active = 1
            ORDER BY p.firstname
        """
        
        cursor.execute(query, (course_id,))
        students = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return students
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch course students: {str(e)}"
        )


@router.get("/stats", response_model=ScheduleStats)
def get_schedule_stats():
    """Get class schedule statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get course count
        cursor.execute("SELECT COUNT(*) as count FROM course WHERE active = 1")
        total_courses = cursor.fetchone()['count']
        
        # Get student count
        cursor.execute("SELECT COUNT(*) as count FROM students WHERE active = 1")
        total_students = cursor.fetchone()['count']
        
        # Get teacher count
        cursor.execute("SELECT COUNT(*) as count FROM teachers WHERE active = 1")
        total_teachers = cursor.fetchone()['count']
        
        # Get active periods (use a simple count for now)
        active_periods = 1  # Default to 1 active period
        
        cursor.close()
        conn.close()
        
        return {
            "total_courses": total_courses,
            "total_students": total_students,
            "total_teachers": total_teachers,
            "active_periods": active_periods
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch statistics: {str(e)}"
        )


# CRUD Operations

@router.post("/courses", response_model=CourseInfo)
def create_course(course_data: CourseCreate):
    """Create a new course"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        insert_query = """
            INSERT INTO course (
                id, code, start_date, m_hours, s_hours, l_hours, fm_hours, 
                student_count, note, education_plan_subject_id, 
                semester_id, education_lang_id, education_type_id, 
                education_year_id, active, create_date, create_user_id,
                update_date, update_user_id, status, copy_status, 
                course_meeting_status, close_status
            ) VALUES (
                (SELECT COALESCE(MAX(id), 0) + 1 FROM course), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, NOW(), 1,
                NOW(), 1, 1, 0, 110000057, 0
            ) RETURNING id
        """
        
        cursor.execute(insert_query, (
            course_data.code,
            course_data.start_date,
            course_data.m_hours,
            course_data.s_hours,
            course_data.l_hours,
            course_data.fm_hours,
            course_data.student_count,
            course_data.note,
            course_data.education_plan_subject_id,
            course_data.semester_id,
            course_data.education_lang_id,
            course_data.education_type_id,
            course_data.education_year_id
        ))
        
        course_id = cursor.fetchone()['id']
        conn.commit()
        
        # Fetch the created course details
        select_query = """
            SELECT
                c.id,
                c.code,
                COALESCE(sd.name_az, 'Unknown Subject') as subject_name,
                c.start_date,
                c.m_hours,
                c.s_hours,
                c.l_hours,
                c.fm_hours,
                (COALESCE(c.m_hours, 0) + COALESCE(c.s_hours, 0) + 
                 COALESCE(c.l_hours, 0) + COALESCE(c.fm_hours, 0)) as total_hours,
                c.student_count,
                0 as teacher_count,
                c.active
            FROM course c
            LEFT JOIN education_plan_subject eps 
                ON eps.id = c.education_plan_subject_id
            LEFT JOIN subject_dic sd ON sd.id = eps.subject_id
            WHERE c.id = %s
        """
        
        cursor.execute(select_query, (course_id,))
        course = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return course
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create course: {str(e)}"
        )


@router.put("/courses/{course_id}", response_model=CourseInfo)
def update_course(course_id: int, course_data: CourseUpdate):
    """Update an existing course"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build dynamic update query
        update_fields = []
        update_values = []
        
        for field, value in course_data.dict(exclude_unset=True).items():
            update_fields.append(f"{field} = %s")
            update_values.append(value)
        
        if not update_fields:
            raise HTTPException(
                status_code=400, 
                detail="No fields to update"
            )
        
        update_query = f"""
            UPDATE course 
            SET {', '.join(update_fields)}, update_date = NOW()
            WHERE id = %s
        """
        update_values.append(course_id)
        
        cursor.execute(update_query, update_values)
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404, 
                detail="Course not found"
            )
        
        conn.commit()
        
        # Fetch updated course details
        select_query = """
            SELECT
                c.id,
                c.code,
                COALESCE(sd.name_az, 'Unknown Subject') as subject_name,
                c.start_date,
                c.m_hours,
                c.s_hours,
                c.l_hours,
                c.fm_hours,
                (COALESCE(c.m_hours, 0) + COALESCE(c.s_hours, 0) + 
                 COALESCE(c.l_hours, 0) + COALESCE(c.fm_hours, 0)) as total_hours,
                c.student_count,
                COUNT(DISTINCT ct.teacher_id) as teacher_count,
                c.active
            FROM course c
            LEFT JOIN education_plan_subject eps 
                ON eps.id = c.education_plan_subject_id
            LEFT JOIN subject_dic sd ON sd.id = eps.subject_id
            LEFT JOIN course_teacher ct 
                ON ct.course_id = c.id AND ct.active = 1
            WHERE c.id = %s
            GROUP BY c.id, c.code, c.start_date, c.m_hours, c.s_hours,
                     c.l_hours, c.fm_hours, c.student_count, c.active, 
                     sd.name_az
        """
        
        cursor.execute(select_query, (course_id,))
        course = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return course
        
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update course: {str(e)}"
        )


@router.delete("/courses/{course_id}")
def delete_course(course_id: int):
    """Soft delete a course (set active = 0)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Soft delete course
        cursor.execute(
            "UPDATE course SET active = 0, update_date = NOW() WHERE id = %s",
            (course_id,)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404, 
                detail="Course not found"
            )
        
        # Soft delete related assignments
        cursor.execute(
            "UPDATE course_teacher SET active = 0 WHERE course_id = %s",
            (course_id,)
        )
        cursor.execute(
            "UPDATE course_student SET active = 0 WHERE course_id = %s",
            (course_id,)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Course deleted successfully"}
        
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete course: {str(e)}"
        )


@router.post("/courses/{course_id}/teachers")
def assign_teacher(course_id: int, assignment: TeacherAssignment):
    """Assign a teacher to a course"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if assignment already exists
        cursor.execute(
            """SELECT id FROM course_teacher 
               WHERE course_id = %s AND teacher_id = %s AND active = 1""",
            (course_id, assignment.teacher_id)
        )
        
        if cursor.fetchone():
            raise HTTPException(
                status_code=400, 
                detail="Teacher already assigned to this course"
            )
        
        # Insert new assignment
        cursor.execute(
            """INSERT INTO course_teacher 
               (id, course_id, teacher_id, lesson_type_id, active, create_date, create_user_id, update_date, update_user_id, close_status)
               VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM course_teacher), %s, %s, %s, 1, NOW(), 1, NOW(), 1, 0)""",
            (course_id, assignment.teacher_id, 1)  # Using default lesson_type_id = 1
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Teacher assigned successfully"}
        
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to assign teacher: {str(e)}"
        )


@router.delete("/courses/{course_id}/teachers/{teacher_id}")
def remove_teacher(course_id: int, teacher_id: int):
    """Remove a teacher from a course"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE course_teacher 
               SET active = 0, update_date = NOW()
               WHERE course_id = %s AND teacher_id = %s""",
            (course_id, teacher_id)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404, 
                detail="Teacher assignment not found"
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Teacher removed successfully"}
        
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to remove teacher: {str(e)}"
        )


@router.post("/courses/{course_id}/students")
def enroll_student(course_id: int, enrollment: StudentEnrollment):
    """Enroll a student in a course"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if enrollment already exists
        cursor.execute(
            """SELECT id FROM course_student 
               WHERE course_id = %s AND student_id = %s AND active = 1""",
            (course_id, enrollment.student_id)
        )
        
        if cursor.fetchone():
            raise HTTPException(
                status_code=400, 
                detail="Student already enrolled in this course"
            )
        
        # Insert new enrollment
        cursor.execute(
            """INSERT INTO course_student 
               (id, course_id, student_id, active, create_date, create_user_id, 
                update_date, update_user_id, course_work)
               VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM course_student), %s, %s, 1, NOW(), 1, NOW(), 1, 0)""",
            (course_id, enrollment.student_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Student enrolled successfully"}
        
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to enroll student: {str(e)}"
        )


@router.delete("/courses/{course_id}/students/{student_id}")
def remove_student(course_id: int, student_id: int):
    """Remove a student from a course"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE course_student 
               SET active = 0, update_date = NOW()
               WHERE course_id = %s AND student_id = %s""",
            (course_id, student_id)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404, 
                detail="Student enrollment not found"
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Student removed successfully"}
        
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to remove student: {str(e)}"
        )


@router.get("/subjects", response_model=List[SubjectInfo])
def get_available_subjects():
    """Get all available subjects from the university system"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get subjects from subject_dic table (primary subjects)
        query = """
            SELECT 
                sd.id,
                sd.name_az as name,
                sd.code
            FROM subject_dic sd
            WHERE sd.name_az IS NOT NULL 
            AND sd.name_az != ''
            UNION
            SELECT 
                asubc.id,
                asubc.subject as name,
                NULL as code
            FROM a_subject_catalog asubc
            WHERE asubc.subject IS NOT NULL 
            AND asubc.subject != ''
            AND asubc.subject NOT IN (
                SELECT sd.name_az FROM subject_dic sd WHERE sd.name_az IS NOT NULL
            )
            ORDER BY name
            LIMIT 100
        """
        
        cursor.execute(query)
        subjects = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return subjects
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch subjects: {str(e)}"
        )


@router.get("/education-languages", response_model=List[EducationLanguage])
def get_education_languages():
    """Get all available education languages"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get languages from dictionary table
        query = """
            SELECT DISTINCT 
                sd.id,
                sd.name_az as name
            FROM subject_dic sd
            INNER JOIN course c ON sd.id = c.education_lang_id
            WHERE sd.name_az IS NOT NULL 
            AND sd.name_az != ''
            UNION
            SELECT 
                110000065 as id,
                'Azərbaycan dili' as name
            UNION
            SELECT 
                110000066 as id,
                'İngilis dili' as name
            UNION
            SELECT 
                110000067 as id,
                'Rus dili' as name
            ORDER BY name
        """
        
        cursor.execute(query)
        languages = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return languages
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch education languages: {str(e)}"
        )


@router.get("/education-groups/{education_group_id}/organization")
def get_education_group_organization(education_group_id: int):
    """Get organization_id for an education group (used to filter teachers)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                eg.organization_id,
                CONCAT('Organization ', eg.organization_id) as organization_name
            FROM education_group eg
            WHERE eg.id = %s AND eg.active = 1
        """

        cursor.execute(query, (education_group_id,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Education group not found"
            )

        return {
            "organization_id": result['organization_id'],
            "organization_name": result['organization_name']
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch education group organization: {str(e)}"
        )


@router.get("/education-groups", response_model=List[EducationGroup])
def get_education_groups(
    education_level_id: Optional[int] = None,
    education_year_id: Optional[int] = None
):
    """Get education groups (classes) with student counts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query with proper student count calculation
        query = """
            SELECT 
                eg.id,
                eg.name,
                eg.education_level_id,
                eg.education_type_id,
                eg.education_year_id,
                eg.education_lang_id,
                'Level ' || COALESCE(eg.education_level_id::text, 'Unknown') as level_name,
                'Year ' || COALESCE(eg.education_year_id::text, 'Unknown') as year_name,
                COUNT(egs.student_id) as student_count
            FROM education_group eg
            LEFT JOIN education_group_student egs 
                ON eg.id = egs.education_group_id AND egs.active = 1
            WHERE eg.active = 1
        """
        
        params = []
        
        if education_level_id:
            query += " AND eg.education_level_id = %s"
            params.append(education_level_id)
            
        if education_year_id:
            query += " AND eg.education_year_id = %s"
            params.append(education_year_id)
        
        query += """
            GROUP BY eg.id, eg.name, eg.education_level_id, eg.education_type_id, 
                     eg.education_year_id, eg.education_lang_id
            ORDER BY eg.name
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Convert to proper format
        groups = []
        for row in results:
            row_dict = dict(row)
            group_data = {
                'id': row_dict['id'],
                'name': row_dict['name'],
                'education_level_id': row_dict['education_level_id'] or 0,
                'education_type_id': row_dict['education_type_id'] or 0,
                'education_year_id': row_dict['education_year_id'] or 0,
                'education_lang_id': row_dict['education_lang_id'] or 0,
                'level_name': row_dict.get('level_name'),
                'year_name': row_dict.get('year_name'),
                'student_count': row_dict.get('student_count', 0)
            }
            groups.append(group_data)
        
        cursor.close()
        conn.close()
        
        return groups
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch education groups: {str(e)}"
        )


@router.get("/semesters", response_model=List[SemesterInfo])
def get_semesters():
    """Get available semester periods"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Try to get actual semester data, or provide common ones
        query = """
            SELECT DISTINCT 
                semester_id as id,
                CASE 
                    WHEN semester_id = 1 THEN 'Payız semestri'
                    WHEN semester_id = 2 THEN 'Yaz semestri'
                    WHEN semester_id = 3 THEN 'Bahar semestri'
                    ELSE CONCAT('Semestr ', semester_id::text)
                END as name
            FROM course 
            WHERE semester_id IS NOT NULL
            UNION
            SELECT 1 as id, 'Payız semestri' as name
            UNION  
            SELECT 2 as id, 'Yaz semestri' as name
            UNION
            SELECT 3 as id, 'Bahar semestri' as name
            ORDER BY id
        """
        
        cursor.execute(query)
        semesters = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return semesters
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch semesters: {str(e)}"
        )


# Enhanced endpoints for multiple teacher assignment and student management

@router.post("/courses/{course_id}/teachers/multiple")
def assign_multiple_teachers_to_course(
    course_id: int,
    assignment: MultipleTeacherAssignment
):
    """Assign multiple teachers to a course"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Remove existing teacher assignments
        cursor.execute(
            "UPDATE course_teacher SET active = 0 WHERE course_id = %s",
            (course_id,)
        )
        
        # Add new teacher assignments
        for teacher_id in assignment.teacher_ids:
            # Generate unique ID for course_teacher
            cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM course_teacher")
            new_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO course_teacher 
                (id, course_id, teacher_id, lesson_type_id, active, create_date, create_user_id, update_date, update_user_id, close_status)
                VALUES (%s, %s, %s, 1, 1, NOW(), 1, NOW(), 1, 0)
            """, (new_id, course_id, teacher_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "message": f"Successfully assigned {len(assignment.teacher_ids)} teachers to course"
        }
    
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to assign teachers: {str(e)}"
        )


@router.get("/courses/{course_id}/students/detailed", response_model=List[CourseStudentInfo])
def get_course_students_detailed(course_id: int):
    """Get detailed student information for a course"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                cs.student_id,
                CONCAT(p.firstname, ' ', COALESCE(p.lastname, '')) as student_name,
                s.id as student_id_number,
                eg.name as education_group_name
            FROM course_student cs
            JOIN students s ON cs.student_id = s.id
            JOIN persons p ON s.person_id = p.id
            LEFT JOIN education_group_student egs ON s.id = egs.student_id AND egs.active = 1
            LEFT JOIN education_group eg ON egs.education_group_id = eg.id
            WHERE cs.course_id = %s AND cs.active = 1
            ORDER BY p.firstname, p.lastname
        """, (course_id,))
        
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            CourseStudentInfo(
                student_id=student['student_id'],
                student_name=student['student_name'],
                student_id_number=student['student_id_number'],
                education_group_name=student['education_group_name'],
                can_remove=True
            ) for student in students
        ]
    
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get course students: {str(e)}"
        )


@router.post("/courses/{course_id}/students/manage")
def manage_course_students(
    course_id: int,
    management: StudentManagement
):
    """Manage course student enrollment (add/remove multiple students)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Remove students
        for student_id in management.student_ids_to_remove:
            cursor.execute("""
                UPDATE course_student 
                SET active = 0, update_date = NOW()
                WHERE course_id = %s AND student_id = %s
            """, (course_id, student_id))
        
        # Add students
        for student_id in management.student_ids_to_add:
            # Check if student is already enrolled
            cursor.execute("""
                SELECT id FROM course_student 
                WHERE course_id = %s AND student_id = %s
            """, (course_id, student_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Reactivate if exists
                cursor.execute("""
                    UPDATE course_student 
                    SET active = 1, update_date = NOW()
                    WHERE course_id = %s AND student_id = %s
                """, (course_id, student_id))
            else:
                # Create new enrollment
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM course_student")
                new_id = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO course_student 
                    (id, course_id, student_id, active, create_date, create_user_id, update_date, update_user_id, course_work)
                    VALUES (%s, %s, %s, 1, NOW(), 1, NOW(), 1, 0)
                """, (new_id, course_id, student_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "message": f"Successfully managed students: {len(management.student_ids_to_add)} added, {len(management.student_ids_to_remove)} removed"
        }
    
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to manage students: {str(e)}"
        )


@router.get("/students/available", response_model=List[AvailableStudent])
def get_available_students(
    search: Optional[str] = None,
    education_group_id: Optional[int] = None,
    exclude_course_id: Optional[int] = None,
    limit: int = 50
):
    """Get available students for enrollment from all education groups"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                s.id as student_id,
                CONCAT(p.firstname, ' ', COALESCE(p.lastname, '')) as student_name,
                s.id as student_id_number,
                eg.name as education_group_name
            FROM students s
            JOIN persons p ON s.person_id = p.id
            LEFT JOIN education_group_student egs ON s.id = egs.student_id AND egs.active = 1
            LEFT JOIN education_group eg ON egs.education_group_id = eg.id
            WHERE s.active = 1
        """
        
        params = []
        
        # Exclude students already in the course
        if exclude_course_id:
            query += """ AND s.id NOT IN (
                SELECT student_id FROM course_student 
                WHERE course_id = %s AND active = 1
            )"""
            params.append(exclude_course_id)
        
        # Filter by education group
        if education_group_id:
            query += " AND egs.education_group_id = %s"
            params.append(education_group_id)
        
        # Search filter
        if search and len(search) >= 2:
            query += " AND (p.firstname ILIKE %s OR p.lastname ILIKE %s OR s.id::text ILIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        query += " ORDER BY p.firstname, p.lastname LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            AvailableStudent(
                student_id=student['student_id'],
                student_name=student['student_name'],
                student_id_number=student['student_id_number'],
                education_group_name=student['education_group_name']
            ) for student in students
        ]
    
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get available students: {str(e)}"
        )


@router.get("/education-groups/{group_id}/students", response_model=List[AvailableStudent])
def get_education_group_students(group_id: int):
    """Get all students in a specific education group"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                s.id as student_id,
                CONCAT(p.firstname, ' ', COALESCE(p.lastname, '')) as student_name,
                s.id as student_id_number,
                eg.name as education_group_name
            FROM education_group_student egs
            JOIN students s ON egs.student_id = s.id
            JOIN persons p ON s.person_id = p.id
            JOIN education_group eg ON egs.education_group_id = eg.id
            WHERE egs.education_group_id = %s AND egs.active = 1 AND s.active = 1
            ORDER BY p.firstname, p.lastname
        """, (group_id,))
        
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            AvailableStudent(
                student_id=student['student_id'],
                student_name=student['student_name'],
                student_id_number=student['student_id_number'],
                education_group_name=student['education_group_name']
            ) for student in students
        ]
    
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get education group students: {str(e)}"
        )