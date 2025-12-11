"""
Education Plan API endpoints - Updated for LMS database (academic_programs)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os

router = APIRouter()


def get_db_connection():
    """Get database connection - using LMS database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "lms"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "1111"),
            cursor_factory=RealDictCursor
        )
        return conn
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )


class AcademicProgram(BaseModel):
    """Academic program model matching lms database"""
    id: str
    organization_unit_id: Optional[str] = None
    code: str
    name: dict  # JSONB field with translations
    degree_type: str
    duration_years: Optional[float] = None
    total_credits: int
    language_of_instruction: Optional[List[str]] = None
    is_active: bool
    created_at: Optional[str] = None


class EducationPlanListResponse(BaseModel):
    """Paginated education plan (academic programs) list response"""
    count: int
    results: List[AcademicProgram]


@router.get("/", response_model=EducationPlanListResponse)
def get_education_plans(
    search: Optional[str] = Query(
        None,
        description="Search in program names and codes"
    ),
    degree_type: Optional[str] = Query(
        None,
        description="Filter by degree type"
    ),
    is_active: Optional[bool] = Query(
        None,
        description="Filter by active status"
    ),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0)
) -> EducationPlanListResponse:
    """
    Get list of academic programs (education plans) from lms database
    
    Args:
        search: Search term for program names and codes
        degree_type: Filter by degree type
        is_active: Filter by active status
        limit: Maximum number of programs to return
        offset: Number of programs to skip
        
    Returns:
        List of academic programs
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append(
                "(code ILIKE %s OR name->>'az' ILIKE %s OR " +
                "name->>'en' ILIKE %s OR name->>'ru' ILIKE %s)"
            )
            search_param = f"%{search}%"
            params.extend([search_param] * 4)
        
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
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM academic_programs
            WHERE {where_clause}
        """
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total'] or 0
        
        # Get paginated results
        params.extend([limit, offset])
        query = f"""
            SELECT
                id::text,
                organization_unit_id::text,
                code,
                name,
                degree_type,
                duration_years,
                total_credits,
                language_of_instruction,
                is_active,
                created_at::text
            FROM academic_programs
            WHERE {where_clause}
            ORDER BY created_at DESC, code
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, params)
        programs = cursor.fetchall()
        
        return EducationPlanListResponse(
            count=total_count,
            results=[dict(row) for row in programs]
        )
        
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/{program_id}")
def get_education_plan_detail(program_id: str):
    """
    Get detailed information about a specific academic program
    
    Args:
        program_id: Academic program UUID
        
    Returns:
        Academic program details
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT
                id::text,
                organization_unit_id::text,
                code,
                name,
                degree_type,
                duration_years,
                total_credits,
                language_of_instruction,
                accreditation_info,
                curriculum,
                admission_requirements,
                is_active,
                created_at::text,
                updated_at::text
            FROM academic_programs
            WHERE id = %s::uuid
        """
        
        cursor.execute(query, (program_id,))
        program = cursor.fetchone()
        
        if not program:
            raise HTTPException(
                status_code=404,
                detail=f"Academic program not found: {program_id}"
            )
        
        return dict(program)
        
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/stats")
def get_education_plan_stats():
    """
    Get statistics about academic programs

    Returns:
        Statistics summary
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        query = """
            SELECT
                COUNT(*) as total_programs,
                COUNT(*) FILTER (WHERE is_active = true) as active_programs,
                COUNT(DISTINCT degree_type) as degree_types,
                SUM(total_credits) FILTER (
                    WHERE is_active = true
                ) as total_credits_all_programs
            FROM academic_programs
        """

        cursor.execute(query)
        stats = cursor.fetchone()

        # Get programs by degree type
        cursor.execute("""
            SELECT degree_type, COUNT(*) as count
            FROM academic_programs
            WHERE is_active = true
            GROUP BY degree_type
            ORDER BY count DESC
        """)
        by_degree = {
            row['degree_type']: row['count']
            for row in cursor.fetchall()
        }

        return {
            "total_programs": stats['total_programs'] or 0,
            "active_programs": stats['active_programs'] or 0,
            "degree_types_count": stats['degree_types'] or 0,
            "programs_by_degree_type": by_degree,
            "total_credits_all_programs": int(
                stats['total_credits_all_programs'] or 0
            )
        }

    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()
