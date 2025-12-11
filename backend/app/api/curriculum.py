from fastapi import APIRouter, HTTPException, Query
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

from app.core.config import settings

router = APIRouter()


def get_db_connection():
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME, 
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=500,    
            detail="Database connection failed"
        )


# Pydantic models
class CurriculumStats(BaseModel):
    active_curricula: int
    unique_subjects: int
    total_subject_dictionary: int
    active_courses: int
    student_enrollments: int
    teaching_assignments: int
    organizations_with_curricula: int
    total_teaching_hours: int
    avg_course_hours: float
    avg_students_per_course: float

class SubjectInfo(BaseModel):
    id: int
    code: str
    name_az: str
    name_en: Optional[str] = None
    name_ru: Optional[str] = None
    used_in_curricula: int
    catalog_entries: int

class OrganizationInfo(BaseModel):
    id: int
    name_az: str
    curricula_count: int

class CurriculumOverview(BaseModel):
    id: str  # UUID
    name: str
    organization_name: str
    subjects_count: int
    courses_count: int
    students_enrolled: int
    create_date: datetime

class CurriculumDetail(BaseModel):
    id: str  # UUID
    name: str
    code: Optional[str] = None
    organization_name: str
    subjects_count: int
    courses_count: int
    total_hours: int
    create_date: datetime

class CurriculumSubject(BaseModel):
    subject_code: str
    subject_name: str
    create_date: Optional[str] = None

class CourseInfo(BaseModel):
    id: int
    code: str
    subject_name: str
    semester_id: int
    m_hours: int
    s_hours: int
    l_hours: int
    fm_hours: int
    total_hours: int
    student_count: int
    status: str
    create_date: datetime

class CurriculumCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = None
    organization_id: int
    education_level_id: Optional[int] = None
    education_type_id: Optional[int] = None
    year_started: Optional[int] = None
    year_ended: Optional[int] = None
    max_semester: Optional[int] = None
    note: Optional[str] = None

class CurriculumUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = None
    organization_id: Optional[int] = None
    education_level_id: Optional[int] = None
    education_type_id: Optional[int] = None
    year_started: Optional[int] = None
    year_ended: Optional[int] = None
    max_semester: Optional[int] = None
    note: Optional[str] = None
    active: Optional[int] = None

# API Endpoints

@router.get("/stats", response_model=CurriculumStats)
async def get_curriculum_stats():
    """Get comprehensive curriculum system statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get comprehensive statistics
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM education_plan WHERE active = 1) as active_curricula,
                (SELECT COUNT(DISTINCT subject_id) FROM education_plan_subject WHERE active = 1) as unique_subjects,
                (SELECT COUNT(*) FROM subject_dic WHERE active = 1) as total_subject_dictionary,
                (SELECT COUNT(*) FROM course WHERE active = 1) as active_courses,
                (SELECT COUNT(*) FROM course_student WHERE active = 1) as student_enrollments,
                (SELECT COUNT(*) FROM course_teacher WHERE active = 1) as teaching_assignments,
                (SELECT COUNT(DISTINCT organization_id) FROM education_plan WHERE active = 1) as organizations_with_curricula
        """)
        stats = cursor.fetchone()
        
        # Get course hour statistics
        cursor.execute("""
            SELECT 
                COALESCE(SUM(m_hours + s_hours + l_hours + fm_hours), 0) as total_teaching_hours,
                COALESCE(AVG(m_hours + s_hours + l_hours + fm_hours), 0) as avg_course_hours,
                COALESCE(AVG(student_count), 0) as avg_students_per_course
            FROM course 
            WHERE active = 1 AND (m_hours + s_hours + l_hours + fm_hours) > 0
        """)
        course_hours = cursor.fetchone()
        
        conn.close()
        
        return CurriculumStats(
            active_curricula=stats["active_curricula"],
            unique_subjects=stats["unique_subjects"],
            total_subject_dictionary=stats["total_subject_dictionary"],
            active_courses=stats["active_courses"],
            student_enrollments=stats["student_enrollments"],
            teaching_assignments=stats["teaching_assignments"],
            organizations_with_curricula=stats["organizations_with_curricula"],
            total_teaching_hours=int(course_hours["total_teaching_hours"]),
            avg_course_hours=float(course_hours["avg_course_hours"]),
            avg_students_per_course=float(course_hours["avg_students_per_course"])
        )
    except Exception as e:
        conn.close()
        logging.error(f"Error getting curriculum stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get curriculum statistics: {str(e)}")

@router.get("/subjects/top", response_model=List[SubjectInfo])
async def get_top_subjects(limit: int = Query(20, ge=1, le=100)):
    """Get top subjects by usage in curricula"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                sd.id,
                sd.code,
                sd.name_az,
                sd.name_en,
                sd.name_ru,
                COUNT(DISTINCT sc.id) as catalog_entries,
                COUNT(DISTINCT eps.subject_group_id) as used_in_curricula
            FROM subject_dic sd
            LEFT JOIN subject_catalog sc ON sc.subject_name_id = sd.id AND sc.active = 1
            LEFT JOIN education_plan_subject eps ON eps.subject_id = sc.id AND eps.active = 1
            WHERE sd.active = 1 AND sd.code IS NOT NULL
            GROUP BY sd.id, sd.code, sd.name_az, sd.name_en, sd.name_ru
            HAVING COUNT(DISTINCT sc.id) > 0
            ORDER BY used_in_curricula DESC, catalog_entries DESC
            LIMIT %s
        """, (limit,))
        
        subjects = cursor.fetchall()
        conn.close()
        
        return [
            SubjectInfo(
                id=subject["id"],
                code=subject["code"],
                name_az=subject["name_az"],
                name_en=subject["name_en"],
                name_ru=subject["name_ru"],
                used_in_curricula=subject["used_in_curricula"],
                catalog_entries=subject["catalog_entries"]
            ) for subject in subjects
        ]
    except Exception as e:
        conn.close()
        logging.error(f"Error getting top subjects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get top subjects: {str(e)}")

@router.get("/organizations", response_model=List[OrganizationInfo])
async def get_organizations_with_curricula(limit: int = Query(50, ge=1, le=100)):
    """Get organizations with their curricula counts"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                o.id,
                on1.name_az,
                COUNT(DISTINCT ep.id) as curricula_count
            FROM organisations o
            JOIN org_names on1 ON on1.id = o.org_name_id AND on1.active = 1
            LEFT JOIN education_plan ep ON ep.organization_id = o.id AND ep.active = 1
            WHERE o.active = 1
            GROUP BY o.id, on1.name_az
            HAVING COUNT(DISTINCT ep.id) > 0
            ORDER BY curricula_count DESC
            LIMIT %s
        """, (limit,))
        
        orgs = cursor.fetchall()
        conn.close()
        
        return [
            OrganizationInfo(
                id=org["id"],
                name_az=org["name_az"],
                curricula_count=org["curricula_count"]
            ) for org in orgs
        ]
    except Exception as e:
        conn.close()
        logging.error(f"Error getting organizations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get organizations: {str(e)}")

@router.get("/", response_model=List[CurriculumOverview])
async def get_curricula_overview(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    organization_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get curricula overview with pagination and filtering"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Build WHERE clause for LMS database
        where_conditions = ["ap.is_active = true"]
        params = []

        if organization_id:
            where_conditions.append("ap.organization_unit_id = %s::uuid")
            params.append(organization_id)

        if search:
            where_conditions.append("(ap.code ILIKE %s OR ap.name::text ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        where_clause = " AND ".join(where_conditions)

        cursor.execute(f"""
            SELECT
                ap.id::text,
                COALESCE(
                    ap.name->>'en',
                    ap.name->>'az',
                    ap.name->>'ru',
                    ap.name::text
                ) as name,
                COALESCE(
                    ou.name->>'en',
                    ou.name->>'az',
                    ou.name->>'ru',
                    'N/A'
                ) as organization_name,
                COUNT(DISTINCT c.id) as subjects_count,
                COUNT(DISTINCT co.id) as courses_count,
                COUNT(DISTINCT s.id) as students_enrolled,
                ap.created_at as create_date
            FROM academic_programs ap
            LEFT JOIN organization_units ou ON ou.id = ap.organization_unit_id
            LEFT JOIN courses c ON c.code LIKE ap.code || '%'
            LEFT JOIN course_offerings co ON co.course_id = c.id
            LEFT JOIN students s ON s.academic_program_id = ap.id
            WHERE {where_clause}
            GROUP BY ap.id, ap.name, ou.name, ap.created_at
            ORDER BY ap.created_at DESC, COALESCE(ap.name->>'en', ap.name->>'az', ap.name->>'ru')
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        curricula = cursor.fetchall()
        conn.close()

        return [
            CurriculumOverview(
                id=curr["id"],
                name=curr["name"],
                organization_name=curr["organization_name"],
                subjects_count=curr["subjects_count"] or 0,
                courses_count=curr["courses_count"] or 0,
                students_enrolled=curr["students_enrolled"] or 0,
                create_date=curr["create_date"]
            ) for curr in curricula
        ]
    except Exception as e:
        conn.close()
        logging.error(f"Error getting curricula overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get curricula: {str(e)}")

@router.get("/{curriculum_id}", response_model=CurriculumDetail)
async def get_curriculum_detail(curriculum_id: str):
    """Get detailed information about a specific curriculum (academic program)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                ap.id::text,
                COALESCE(
                    ap.name->>'en',
                    ap.name->>'az',
                    ap.name->>'ru',
                    ap.name::text
                ) as name,
                ap.code,
                COALESCE(
                    ou.name->>'en',
                    ou.name->>'az',
                    ou.name->>'ru',
                    'N/A'
                ) as organization_name,
                COUNT(DISTINCT c.id) as subjects_count,
                COUNT(DISTINCT co.id) as courses_count,
                0 as total_hours,
                ap.created_at as create_date
            FROM academic_programs ap
            LEFT JOIN organization_units ou ON ou.id = ap.organization_unit_id
            LEFT JOIN courses c ON c.code LIKE ap.code || '%'
            LEFT JOIN course_offerings co ON co.course_id = c.id
            WHERE ap.id = %s::uuid
            GROUP BY ap.id, ap.name, ap.code, ou.name, ap.created_at
        """, (curriculum_id,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            raise HTTPException(status_code=404, detail="Curriculum not found")

        return CurriculumDetail(
            id=result["id"],
            name=result["name"],
            code=result["code"],
            organization_name=result["organization_name"],
            subjects_count=result["subjects_count"] or 0,
            courses_count=result["courses_count"] or 0,
            total_hours=int(result["total_hours"]) if result["total_hours"] else 0,
            create_date=result["create_date"]
        )
    except HTTPException:
        raise
    except Exception as e:
        conn.close()
        logging.error(f"Error getting curriculum detail: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get curriculum detail: {str(e)}")

@router.get("/{curriculum_id}/subjects", response_model=List[CurriculumSubject])
async def get_curriculum_subjects(curriculum_id: str):
    """Get all courses/subjects for a specific academic program"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Query courses related to this academic program
        cursor.execute("""
            SELECT
                c.id::text as subject_id,
                c.code as subject_code,
                COALESCE(
                    c.name->>'en',
                    c.name->>'az',
                    c.name->>'ru',
                    c.name::text
                ) as subject_name,
                c.credits as credit_hours,
                NOW() as create_date
            FROM courses c
            WHERE c.code LIKE (
                SELECT ap.code || '%'
                FROM academic_programs ap
                WHERE ap.id = %s::uuid
            )
            ORDER BY c.code
            LIMIT 100
        """, (curriculum_id,))

        subjects = cursor.fetchall()
        conn.close()

        if not subjects:
            # Return empty list if no subjects found
            return []

        return [
            CurriculumSubject(
                subject_code=subj["subject_code"] or "N/A",
                subject_name=subj["subject_name"] or "Unknown Subject",
                create_date=str(subj["create_date"]) if subj.get("create_date") else None
            ) for subj in subjects
        ]
    except Exception as e:
        conn.close()
        logging.error(f"Error getting curriculum subjects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get curriculum subjects: {str(e)}")

@router.get("/{curriculum_id}/courses", response_model=List[CourseInfo])
async def get_curriculum_courses(curriculum_id: int):
    """Get all courses for a specific curriculum"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                c.id,
                c.code,
                COALESCE(sd.name_az, 'Unknown Subject') as subject_name,
                c.semester_id,
                c.m_hours,
                c.s_hours,
                c.l_hours,
                c.fm_hours,
                (c.m_hours + c.s_hours + c.l_hours + c.fm_hours) as total_hours,
                c.student_count,
                CASE 
                    WHEN c.active = 1 THEN 'Active'
                    ELSE 'Inactive'
                END as status,
                c.create_date
            FROM course c
            JOIN education_plan_subject eps ON eps.id = c.education_plan_subject_id
            LEFT JOIN subject_catalog sc ON sc.id = eps.subject_id AND sc.active = 1
            LEFT JOIN subject_dic sd ON sd.id = sc.subject_name_id AND sd.active = 1
            WHERE eps.subject_group_id = %s AND c.active = 1
            ORDER BY c.semester_id, c.create_date DESC
        """, (curriculum_id,))
        
        courses = cursor.fetchall()
        conn.close()
        
        return [
            CourseInfo(
                id=course["id"],
                code=course["code"] or f"COURSE-{course['id']}",
                subject_name=course["subject_name"],
                semester_id=course["semester_id"],
                m_hours=course["m_hours"] or 0,
                s_hours=course["s_hours"] or 0,
                l_hours=course["l_hours"] or 0,
                fm_hours=course["fm_hours"] or 0,
                total_hours=course["total_hours"] or 0,
                student_count=course["student_count"] or 0,
                status=course["status"],
                create_date=course["create_date"]
            ) for course in courses
        ]
    except Exception as e:
        conn.close()
        logging.error(f"Error getting curriculum courses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get curriculum courses: {str(e)}")

@router.post("/", response_model=Dict[str, Any])
async def create_curriculum(curriculum: CurriculumCreate):
    """Create a new curriculum"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Generate a unique ID (using timestamp-based approach)
        import time
        new_id = int(time.time() * 1000000) % 9223372036854775807  # Keep within bigint range
        
        cursor.execute("""
            INSERT INTO education_plan (
                id, name, code, organization_id, education_level_id, education_type_id,
                year_started, year_ended, max_semester, note, active, create_date, update_date
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, NOW(), NOW()
            )
            RETURNING id, name, create_date
        """, (
            new_id,
            curriculum.name,
            curriculum.code,
            curriculum.organization_id,
            curriculum.education_level_id,
            curriculum.education_type_id,
            curriculum.year_started,
            curriculum.year_ended,
            curriculum.max_semester,
            curriculum.note
        ))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            "success": True,
            "message": "Curriculum created successfully",
            "curriculum_id": result["id"],
            "name": result["name"],
            "create_date": result["create_date"]
        }
    except Exception as e:
        conn.close()
        logging.error(f"Error creating curriculum: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create curriculum: {str(e)}")

@router.put("/{curriculum_id}", response_model=Dict[str, Any])
async def update_curriculum(curriculum_id: int, curriculum: CurriculumUpdate):
    """Update an existing curriculum"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if curriculum exists
        cursor.execute("SELECT id FROM education_plan WHERE id = %s", (curriculum_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Curriculum not found")
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        if curriculum.name is not None:
            update_fields.append("name = %s")
            params.append(curriculum.name)
        if curriculum.code is not None:
            update_fields.append("code = %s")
            params.append(curriculum.code)
        if curriculum.organization_id is not None:
            update_fields.append("organization_id = %s")
            params.append(curriculum.organization_id)
        if curriculum.education_level_id is not None:
            update_fields.append("education_level_id = %s")
            params.append(curriculum.education_level_id)
        if curriculum.education_type_id is not None:
            update_fields.append("education_type_id = %s")
            params.append(curriculum.education_type_id)
        if curriculum.year_started is not None:
            update_fields.append("year_started = %s")
            params.append(curriculum.year_started)
        if curriculum.year_ended is not None:
            update_fields.append("year_ended = %s")
            params.append(curriculum.year_ended)
        if curriculum.max_semester is not None:
            update_fields.append("max_semester = %s")
            params.append(curriculum.max_semester)
        if curriculum.note is not None:
            update_fields.append("note = %s")
            params.append(curriculum.note)
        if curriculum.active is not None:
            update_fields.append("active = %s")
            params.append(curriculum.active)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("update_date = NOW()")
        params.append(curriculum_id)
        
        query = f"UPDATE education_plan SET {', '.join(update_fields)} WHERE id = %s RETURNING name, update_date"
        cursor.execute(query, params)
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            "success": True,
            "message": "Curriculum updated successfully",
            "curriculum_id": curriculum_id,
            "name": result["name"],
            "update_date": result["update_date"]
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.close()
        logging.error(f"Error updating curriculum: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update curriculum: {str(e)}")

@router.delete("/{curriculum_id}", response_model=Dict[str, Any])
async def delete_curriculum(curriculum_id: int):
    """Soft delete a curriculum (set active = 0)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if curriculum exists
        cursor.execute("""
            SELECT id, COALESCE(name->>'en', name->>'az', name->>'ru', name::text) as name
            FROM education_plan
            WHERE id = %s AND active = 1
        """, (curriculum_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Curriculum not found or already deleted")
        
        # Soft delete
        cursor.execute("""
            UPDATE education_plan 
            SET active = 0, update_date = NOW() 
            WHERE id = %s
        """, (curriculum_id,))
        
        conn.close()
        
        return {
            "success": True,
            "message": f"Curriculum '{result['name']}' deleted successfully",
            "curriculum_id": curriculum_id
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.close()
        logging.error(f"Error deleting curriculum: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete curriculum: {str(e)}")