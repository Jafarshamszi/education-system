"""
Student Groups API endpoints - Updated for LMS database
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import math

from app.core.config import settings

router = APIRouter()


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=settings.DB_HOST,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=RealDictCursor
    )


class StudentGroupResponse(BaseModel):
    """Student group response model"""
    id: str
    group_name: str
    student_count: int
    organization_name: Optional[str] = None
    education_level: Optional[str] = None
    education_type: Optional[str] = None
    language: Optional[str] = None
    tutor_full_name: Optional[str] = None
    create_date: Optional[str] = None


class StudentGroupListResponse(BaseModel):
    """Paginated student group list"""
    count: int
    total_pages: int
    current_page: int
    results: List[StudentGroupResponse]


class StudentGroupStatsResponse(BaseModel):
    """Student group statistics"""
    total_groups: int
    total_students: int
    average_group_size: float


@router.get("/", response_model=StudentGroupListResponse)
def get_student_groups(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None
):
    """Get student cohorts from LMS database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        offset = (page - 1) * limit

        # Build WHERE clause
        where_conditions = ["sc.is_active = true"]
        params = []

        if search:
            where_conditions.append("sc.name ILIKE %s")
            params.append(f"%{search}%")

        where_clause = " AND ".join(where_conditions)

        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM student_cohorts sc WHERE {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['count']

        # Get cohorts with member count and related info
        query = f"""
            SELECT
                sc.id::text,
                sc.name as group_name,
                TO_CHAR(sc.created_at, 'YYYY-MM-DD HH24:MI:SS') as create_date,
                COALESCE(ou.name->>'az', 'N/A') as organization_name,
                sc.education_level,
                sc.education_type,
                sc.language,
                '' as tutor_full_name,
                COUNT(DISTINCT scm.student_id) as student_count
            FROM student_cohorts sc
            LEFT JOIN organization_units ou ON sc.organization_unit_id = ou.id
            LEFT JOIN student_cohort_members scm ON sc.id = scm.cohort_id AND scm.is_active = true
            WHERE {where_clause}
            GROUP BY sc.id, sc.name, sc.created_at, ou.name,
                     sc.education_level, sc.education_type, sc.language
            ORDER BY sc.created_at DESC NULLS LAST
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, params + [limit, offset])
        groups = cursor.fetchall()

        total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

        return StudentGroupListResponse(
            count=total_count,
            total_pages=total_pages,
            current_page=page,
            results=[dict(g) for g in groups]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/stats", response_model=StudentGroupStatsResponse)
def get_student_group_stats():
    """Get student group statistics from LMS database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT
                COUNT(DISTINCT sc.id) as total_groups,
                COUNT(DISTINCT scm.student_id) as total_students
            FROM student_cohorts sc
            LEFT JOIN student_cohort_members scm ON sc.id = scm.cohort_id AND scm.is_active = true
            WHERE sc.is_active = true
        """

        cursor.execute(query)
        result = cursor.fetchone()

        total_groups = result['total_groups'] or 0
        total_students = result['total_students'] or 0
        avg_size = (total_students / total_groups) if total_groups > 0 else 0.0

        return StudentGroupStatsResponse(
            total_groups=total_groups,
            total_students=total_students,
            average_group_size=avg_size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


class StudentInfo(BaseModel):
    """Student information in a group"""
    id: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    pincode: Optional[str] = None
    joined_group_date: Optional[str] = None


class StudentGroupDetail(BaseModel):
    """Detailed student group information"""
    id: str
    group_name: str
    student_count: int
    organization_name: Optional[str] = None
    education_level: Optional[str] = None
    education_type: Optional[str] = None
    language: Optional[str] = None
    tutor_full_name: Optional[str] = None
    create_date: Optional[str] = None
    students: List[StudentInfo] = []


@router.get("/{group_id}", response_model=StudentGroupDetail)
def get_student_group_detail(group_id: str):
    """Get detailed information about a specific student group"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get group details
        group_query = """
            SELECT
                sc.id::text,
                sc.name as group_name,
                TO_CHAR(sc.created_at, 'YYYY-MM-DD HH24:MI:SS') as create_date,
                COALESCE(ou.name->>'az', 'N/A') as organization_name,
                sc.education_level,
                sc.education_type,
                sc.language,
                '' as tutor_full_name
            FROM student_cohorts sc
            LEFT JOIN organization_units ou ON sc.organization_unit_id = ou.id
            WHERE sc.id::text = %s AND sc.is_active = true
        """

        cursor.execute(group_query, (group_id,))
        group = cursor.fetchone()

        if not group:
            raise HTTPException(status_code=404, detail="Student group not found")

        # Get students in this group
        students_query = """
            SELECT
                s.id::text,
                p.first_name as firstname,
                p.last_name as lastname,
                '' as pincode,
                TO_CHAR(scm.created_at, 'YYYY-MM-DD') as joined_group_date
            FROM student_cohort_members scm
            JOIN students s ON scm.student_id = s.id
            JOIN persons p ON s.person_id = p.id
            WHERE scm.cohort_id::text = %s AND scm.is_active = true
            ORDER BY p.last_name, p.first_name
        """

        cursor.execute(students_query, (group_id,))
        students = cursor.fetchall()

        return StudentGroupDetail(
            **dict(group),
            student_count=len(students),
            students=[dict(s) for s in students]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


class StudentGroupCreate(BaseModel):
    """Create student group request"""
    name: str
    organization_id: Optional[int] = None
    education_level_id: Optional[int] = None
    education_type_id: Optional[int] = None
    education_lang_id: Optional[int] = None
    tyutor_id: Optional[int] = None


class StudentGroupUpdate(BaseModel):
    """Update student group request"""
    name: Optional[str] = None
    organization_id: Optional[int] = None
    education_level_id: Optional[int] = None
    education_type_id: Optional[int] = None
    education_lang_id: Optional[int] = None
    tyutor_id: Optional[int] = None
    active: Optional[int] = None


@router.post("/", response_model=StudentGroupResponse)
def create_student_group(group_data: StudentGroupCreate):
    """Create a new student group"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Generate unique code from name (e.g., "TEST-GROUP-2025")
        code = group_data.name.upper().replace(" ", "-")[:50]

        # For now, use default text values since dictionaries
        # don't exist in lms
        # Frontend should send actual text values in future
        education_level = "Bakalavr"  # Default
        education_type = "Əyani"  # Default
        language = "Azərbaycan dili"  # Default

        # Convert organization_id to UUID if needed
        organization_uuid = None
        if group_data.organization_id:
            cursor.execute(
                """SELECT id FROM organization_units
                   WHERE id::text = %s OR id = %s::uuid LIMIT 1""",
                (str(group_data.organization_id),
                 str(group_data.organization_id))
            )
            org_result = cursor.fetchone()
            if org_result:
                organization_uuid = org_result['id']

        # Convert tutor_id to UUID if needed
        tutor_uuid = None
        if group_data.tyutor_id:
            cursor.execute(
                """SELECT id FROM staff_members
                   WHERE id::text = %s OR id = %s::uuid LIMIT 1""",
                (str(group_data.tyutor_id), str(group_data.tyutor_id))
            )
            tutor_result = cursor.fetchone()
            if tutor_result:
                tutor_uuid = tutor_result['id']

        insert_query = """
            INSERT INTO student_cohorts (
                code, name, organization_unit_id,
                education_level, education_type,
                language, tutor_id, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, true)
            RETURNING id::text, name as group_name
        """

        cursor.execute(insert_query, (
            code,
            group_data.name,
            organization_uuid,
            education_level,
            education_type,
            language,
            tutor_uuid
        ))

        result = cursor.fetchone()
        conn.commit()

        return StudentGroupResponse(
            id=result['id'],
            group_name=result['group_name'],
            student_count=0
        )

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.put("/{group_id}", response_model=StudentGroupResponse)
def update_student_group(group_id: str, group_data: StudentGroupUpdate):
    """Update an existing student group"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Build update fields
        update_fields = []
        params = []

        if group_data.name is not None:
            update_fields.append("name = %s")
            params.append(group_data.name)
            # Also update code based on name
            update_fields.append("code = %s")
            params.append(group_data.name.upper().replace(" ", "-")[:50])

        if group_data.organization_id is not None:
            # Convert to UUID
            cursor.execute(
                """SELECT id FROM organization_units 
                   WHERE id::text = %s OR id = %s::uuid""",
                (str(group_data.organization_id),
                 str(group_data.organization_id))
            )
            org_result = cursor.fetchone()
            if org_result:
                update_fields.append("organization_unit_id = %s")
                params.append(org_result['id'])

        # Note: education_level, education_type, education_lang
        # are kept as-is for now since dictionaries table
        # doesn't exist in lms database
        # Frontend should send text values directly in future

        if group_data.tyutor_id is not None:
            # Convert to UUID
            cursor.execute(
                """SELECT id FROM staff_members 
                   WHERE id::text = %s OR id = %s::uuid""",
                (str(group_data.tyutor_id), str(group_data.tyutor_id))
            )
            tutor_result = cursor.fetchone()
            if tutor_result:
                update_fields.append("tutor_id = %s")
                params.append(tutor_result['id'])

        if group_data.active is not None:
            # Convert active (0/1) to is_active (boolean)
            update_fields.append("is_active = %s")
            params.append(group_data.active == 1)

        if not update_fields:
            raise HTTPException(
                status_code=400,
                detail="No fields to update"
            )

        params.append(group_id)

        update_query = f"""
            UPDATE student_cohorts
            SET {', '.join(update_fields)}
            WHERE id::text = %s OR id = %s::uuid
            RETURNING id::text, name as group_name
        """
        params.append(group_id)  # Add again for OR condition

        cursor.execute(update_query, params)
        result = cursor.fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Student group not found"
            )

        conn.commit()

        # Get student count from student_cohort_members
        cursor.execute(
            """SELECT COUNT(*) as count 
               FROM student_cohort_members 
               WHERE cohort_id::text = %s AND is_active = true""",
            (result['id'],)
        )
        count = cursor.fetchone()['count']

        return StudentGroupResponse(
            id=result['id'],
            group_name=result['group_name'],
            student_count=count
        )

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.delete("/{group_id}")
def delete_student_group(group_id: str):
    """Delete (deactivate) a student group"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """UPDATE student_cohorts 
               SET is_active = false 
               WHERE id::text = %s OR id = %s::uuid 
               RETURNING id""",
            (group_id, group_id)
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Student group not found"
            )

        conn.commit()

        return {"message": "Student group deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/lookup/organizations")
def get_organizations_lookup():
    """Get organizations for dropdown"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT
                id::text,
                name
            FROM organization_units
            WHERE is_active = true
            ORDER BY name
            LIMIT 200
        """
        cursor.execute(query)
        results = cursor.fetchall()
        # Return in multi-language format with same name for all languages
        return [
            {
                "id": r["id"],
                "name": {
                    "az": r["name"],
                    "en": r["name"],
                    "ru": r["name"]
                }
            } for r in results
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/lookup/education-levels")
def get_education_levels_lookup():
    """Get education levels for dropdown"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Return predefined education levels
        education_levels = [
            {"id": "bachelor", "name": {"az": "Bakalavr", "en": "Bachelor", "ru": "Бакалавр"}},
            {"id": "master", "name": {"az": "Magistr", "en": "Master", "ru": "Магистр"}},
            {"id": "doctorate", "name": {"az": "Doktorantura", "en": "Doctorate", "ru": "Докторантура"}},
        ]
        return education_levels

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/lookup/education-types")
def get_education_types_lookup():
    """Get education types for dropdown"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Return predefined education types
        education_types = [
            {
                "id": "fulltime",
                "name": {
                    "az": "Tam vaxtlı",
                    "en": "Full-time",
                    "ru": "Очное"
                }
            },
            {
                "id": "parttime",
                "name": {
                    "az": "Qiyabi",
                    "en": "Part-time",
                    "ru": "Заочное"
                }
            },
            {
                "id": "distance",
                "name": {
                    "az": "Distant",
                    "en": "Distance",
                    "ru": "Дистанционное"
                }
            },
        ]
        return education_types

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/lookup/languages")
def get_languages_lookup():
    """Get languages for dropdown"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT
                id::text,
                COALESCE(name_az, name_ru, name_en) as name
            FROM dictionaries
            WHERE type_id = (SELECT id FROM dictionary_types WHERE code = 'EDU_LANG')
            ORDER BY name_az
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/lookup/tutors")
def get_tutors_lookup():
    """Get tutors (teachers) for dropdown"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT
                t.id::text,
                CONCAT(COALESCE(p.firstname, ''), ' ', COALESCE(p.lastname, '')) as name
            FROM teachers t
            JOIN persons p ON t.person_id = p.id
            WHERE t.active = 1
            ORDER BY p.lastname, p.firstname
            LIMIT 500
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return [{"id": r["id"], "name": r["name"].strip()} for r in results if r["name"].strip()]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
