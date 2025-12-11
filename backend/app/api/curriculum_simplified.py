"""
Curriculum API - Updated for LMS database structure
"""

from fastapi import APIRouter, HTTPException, Query
import os
from typing import List, Optional
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings

router = APIRouter()


def get_db():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"DB connection failed: {str(e)}"
        )


class CurriculumStats(BaseModel):
    """Curriculum statistics"""
    active_courses: int
    total_enrollments: int
    unique_students: int


class CourseInfo(BaseModel):
    """Course information"""
    id: str
    code: str
    name: dict  # JSONB with translations
    credit_hours: int
    is_active: bool


class CurriculumOverview(BaseModel):
    """Curriculum/Academic Program overview"""
    id: str
    code: str
    name: dict  # JSONB with translations
    degree_type: str
    total_credits: int
    is_active: bool


class CurriculumDetail(BaseModel):
    """Detailed curriculum/academic program information"""
    id: str
    code: str
    name: dict
    degree_type: str
    total_credits: int
    is_active: bool
    organization_name: str
    subjects_count: int
    courses_count: int


class CurriculumSubject(BaseModel):
    """Subject/course in a curriculum"""
    subject_code: str
    subject_name: str
    credit_hours: int


@router.get("/stats")
def get_stats():
    """Get curriculum statistics from courses and enrollments"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE is_active = true) as active_courses,
                (SELECT COUNT(*) FROM course_enrollments) as total_enrollments,
                (SELECT COUNT(DISTINCT student_id) FROM course_enrollments) 
                    as unique_students
            FROM courses
        """)
        
        stats = cursor.fetchone()
        
        return CurriculumStats(
            active_courses=stats['active_courses'] or 0,
            total_enrollments=stats['total_enrollments'] or 0,
            unique_students=stats['unique_students'] or 0
        )
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/courses", response_model=List[CourseInfo])
def get_courses(
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of courses"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append(
                "(code ILIKE %s OR name->>'az' ILIKE %s OR " +
                "name->>'en' ILIKE %s)"
            )
            search_param = f"%{search}%"
            params.extend([search_param] * 3)
        
        if is_active is not None:
            where_conditions.append("is_active = %s")
            params.append(is_active)
        
        where_clause = (
            " AND ".join(where_conditions) if where_conditions
            else "1=1"
        )
        
        params.extend([limit, offset])
        
        query = f"""
            SELECT
                id::text,
                code,
                name,
                credit_hours,
                is_active
            FROM courses
            WHERE {where_clause}
            ORDER BY code
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, params)
        courses = cursor.fetchall()
        
        return [dict(row) for row in courses]
        
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/courses/{course_id}")
def get_course_detail(course_id: str):
    """Get detailed course information"""
    conn = get_db()
    try:
        cursor = conn.cursor()

        query = """
            SELECT
                id::text,
                code,
                name,
                description,
                credits,
                lecture_hours,
                lab_hours,
                tutorial_hours,
                prerequisites,
                is_active,
                created_at::text,
                updated_at::text
            FROM courses
            WHERE id = %s::uuid
        """

        cursor.execute(query, (course_id,))
        course = cursor.fetchone()

        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Course not found: {course_id}"
            )

        return dict(course)

    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/curricula/", response_model=List[CurriculumOverview])
def get_curricula(
    search: Optional[str] = Query(None),
    degree_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of curricula (academic programs)"""
    conn = get_db()
    try:
        cursor = conn.cursor()

        where_conditions = []
        params = []

        if search:
            where_conditions.append(
                "(code ILIKE %s OR name->>'az' ILIKE %s OR " +
                "name->>'en' ILIKE %s)"
            )
            search_param = f"%{search}%"
            params.extend([search_param] * 3)

        if degree_type:
            where_conditions.append("degree_type = %s")
            params.append(degree_type)

        if is_active is not None:
            where_conditions.append("is_active = %s")
            params.append(is_active)

        where_clause = (
            " AND ".join(where_conditions) if where_conditions
            else "1=1"
        )

        params.extend([limit, offset])

        query = f"""
            SELECT
                id::text,
                code,
                name,
                degree_type,
                total_credits,
                is_active
            FROM academic_programs
            WHERE {where_clause}
            ORDER BY code
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, params)
        programs = cursor.fetchall()

        return [dict(row) for row in programs]

    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/curricula/{curriculum_id}", response_model=CurriculumDetail)
def get_curriculum_detail(curriculum_id: str):
    """Get detailed information about a specific curriculum (academic program)"""
    conn = get_db()
    cursor = None
    try:
        cursor = conn.cursor()

        query = """
            SELECT
                ap.id::text,
                ap.code,
                ap.name,
                ap.degree_type,
                ap.total_credits,
                ap.is_active,
                COALESCE(
                    ou.name->>'en',
                    ou.name->>'az',
                    ou.name->>'ru',
                    'N/A'
                ) as organization_name,
                COUNT(DISTINCT c.id) as subjects_count,
                COUNT(DISTINCT co.id) as courses_count
            FROM academic_programs ap
            LEFT JOIN organization_units ou ON ou.id = ap.organization_unit_id
            LEFT JOIN courses c ON c.code LIKE ap.code || '%%'
            LEFT JOIN course_offerings co ON co.course_id = c.id
            WHERE ap.id = %s::uuid
            GROUP BY ap.id, ap.code, ap.name, ap.degree_type, ap.total_credits,
                     ap.is_active, ou.name
        """

        cursor.execute(query, (curriculum_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Curriculum not found")

        return dict(result)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error getting curriculum detail: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        conn.close()


@router.get("/curricula/{curriculum_id}/subjects", response_model=List[CurriculumSubject])
def get_curriculum_subjects(curriculum_id: str):
    """Get all courses/subjects for a specific academic program"""
    conn = get_db()
    try:
        cursor = conn.cursor()

        query = """
            SELECT
                c.code as subject_code,
                COALESCE(
                    c.name->>'en',
                    c.name->>'az',
                    c.name->>'ru',
                    c.name::text
                ) as subject_name,
                c.credit_hours
            FROM courses c
            WHERE c.code LIKE (
                SELECT ap.code || '%%'
                FROM academic_programs ap
                WHERE ap.id = %s::uuid
            )
            AND c.is_active = true
            ORDER BY c.code
            LIMIT 100
        """

        cursor.execute(query, (curriculum_id,))
        subjects = cursor.fetchall()

        return [dict(row) for row in subjects]

    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/subjects/top/")
def get_top_subjects(limit: int = Query(10, le=50)):
    """Get top subjects/courses by enrollment"""
    conn = get_db()
    try:
        cursor = conn.cursor()

        query = """
            SELECT
                c.id::text,
                c.code,
                c.name,
                c.credit_hours,
                COUNT(DISTINCT ce.student_id) as student_count
            FROM courses c
            LEFT JOIN course_offerings co ON c.id = co.course_id
            LEFT JOIN course_enrollments ce ON co.id = ce.course_offering_id
            WHERE c.is_active = true
            GROUP BY c.id, c.code, c.name, c.credit_hours
            ORDER BY student_count DESC, c.code
            LIMIT %s
        """

        cursor.execute(query, (limit,))
        subjects = cursor.fetchall()

        return [dict(row) for row in subjects]

    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()
