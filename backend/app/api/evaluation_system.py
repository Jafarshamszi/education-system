from fastapi import APIRouter, HTTPException
import os
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

from app.core.config import settings

router = APIRouter()


def get_db_connection():
    """Create database connection"""
    try:
        connection = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        return connection
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )


@router.get("/evaluation-systems", response_model=List[Dict[str, Any]])
async def get_evaluation_systems():
    """Get all evaluation systems (assessment types) with their details from LMS database"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Query assessment types and their usage from the LMS database
        query = """
        SELECT
            assessment_type as name,
            COUNT(*) as variant_count,
            MIN(passing_marks::float / NULLIF(total_marks::float, 0) * 100) as min_pass_percent,
            MAX(passing_marks::float / NULLIF(total_marks::float, 0) * 100) as max_pass_percent,
            STRING_AGG(DISTINCT
                CONCAT('Weight: ', weight_percentage::text, '%'),
                ' | '
            ) as formulas
        FROM assessments
        WHERE assessment_type IS NOT NULL
        GROUP BY assessment_type
        ORDER BY assessment_type
        """

        cursor.execute(query)
        systems = cursor.fetchall()

        result = []
        for system in systems:
            result.append({
                "name": system["name"] or "Unknown",
                "variant_count": system["variant_count"] or 0,
                "min_pass_percent": round(system["min_pass_percent"], 2) if system["min_pass_percent"] else None,
                "max_pass_percent": round(system["max_pass_percent"], 2) if system["max_pass_percent"] else None,
                "formulas": system["formulas"] or "N/A"
            })

        cursor.close()
        connection.close()

        return result

    except Exception as e:
        logging.error(f"Error fetching evaluation systems: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching evaluation systems: {str(e)}"
        )


@router.get("/evaluation-systems/{system_name}/details")
async def get_evaluation_system_details(system_name: str):
    """Get detailed information for a specific evaluation system (assessment type)"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        SELECT
            a.id::text,
            a.assessment_type as name,
            CONCAT(
                COALESCE(a.total_marks::text, 'N/A'),
                ' (',
                COALESCE(a.passing_marks::text, '0'),
                ' to pass)'
            ) as points,
            CASE
                WHEN a.total_marks > 0 THEN
                    ROUND((a.passing_marks / a.total_marks * 100)::numeric, 2)
                ELSE NULL
            END as successful_pass_percent,
            CONCAT('Weight: ', a.weight_percentage, '%') as formula_with_cw,
            CONCAT('Total: ', a.total_marks, ' marks') as formula_without_cw,
            NULL::integer as colloquium_status,
            a.submission_type as type
        FROM assessments a
        WHERE a.assessment_type = %s
        ORDER BY a.id
        LIMIT 50
        """

        cursor.execute(query, (system_name,))
        details = cursor.fetchall()

        if not details:
            raise HTTPException(
                status_code=404,
                detail=f"Evaluation system '{system_name}' not found"
            )

        result = []
        for detail in details:
            # Parse points to get grade scale
            parsed_points = await parse_points_from_assessment(
                detail["id"],
                connection
            )

            result.append({
                "id": detail["id"],
                "name": detail["name"],
                "points": detail["points"],
                "parsed_points": parsed_points,
                "successful_pass_percent": float(detail["successful_pass_percent"]) if detail["successful_pass_percent"] else None,
                "formula_with_cw": detail["formula_with_cw"],
                "formula_without_cw": detail["formula_without_cw"],
                "colloquium_status": detail["colloquium_status"],
                "type": detail["type"]
            })

        cursor.close()
        connection.close()

        return result

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching evaluation system details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching evaluation system details: {str(e)}"
        )


async def parse_points_from_assessment(assessment_id: str, connection) -> List[Dict[str, Any]]:
    """Get grade scale points used for an assessment"""
    try:
        cursor = connection.cursor()

        # Get grade point scale (letter grades available)
        query = """
        SELECT
            id::text,
            letter_grade as code,
            description->>'en' as name_en,
            description->>'ru' as name_ru,
            'dictionary' as type
        FROM grade_point_scale
        WHERE is_active = true
        ORDER BY display_order
        """

        cursor.execute(query)
        grade_points = cursor.fetchall()

        if grade_points:
            return [dict(point) for point in grade_points]

        # Fallback to numeric scale if no letter grades
        return [
            {"id": None, "code": "100", "name_en": "Maximum", "name_ru": "Максимум", "type": "numeric"},
            {"id": None, "code": "0", "name_en": "Minimum", "name_ru": "Минимум", "type": "numeric"}
        ]

    except Exception as e:
        logging.error(f"Error parsing assessment points: {e}")
        return []


@router.get("/grade-dictionary", response_model=List[Dict[str, Any]])
async def get_grade_dictionary():
    """Get all grade point scale entries from LMS database"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        SELECT
            id::text,
            letter_grade as code,
            description->>'en' as name_en,
            description->>'ru' as name_ru,
            NULL::text as type_id,
            CASE
                WHEN letter_grade ~ '^[A-F][+-]?$' THEN 'letter'
                ELSE 'numeric'
            END as category
        FROM grade_point_scale
        WHERE is_active = true
        ORDER BY display_order
        """

        cursor.execute(query)
        grades = cursor.fetchall()

        result = [dict(grade) for grade in grades]

        cursor.close()
        connection.close()

        return result

    except Exception as e:
        logging.error(f"Error fetching grade dictionary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching grade dictionary: {str(e)}"
        )


@router.get("/evaluation-statistics", response_model=Dict[str, Any])
async def get_evaluation_statistics():
    """Get statistics about evaluation system usage from LMS database"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Total grades recorded
        cursor.execute("""
        SELECT COUNT(*) as total_records
        FROM grades
        WHERE is_final = true
        """)
        grade_stats = cursor.fetchone()

        # Usage by assessment type
        cursor.execute("""
        SELECT
            a.assessment_type as name,
            COUNT(g.id) as usage_count
        FROM grades g
        JOIN assessments a ON g.assessment_id = a.id
        WHERE g.is_final = true
        GROUP BY a.assessment_type
        ORDER BY usage_count DESC
        """)
        usage_stats = cursor.fetchall()

        # Grade distribution by letter grade
        cursor.execute("""
        SELECT
            CASE
                WHEN g.letter_grade IS NOT NULL THEN g.letter_grade
                WHEN g.percentage >= 90 THEN 'A (90-100%)'
                WHEN g.percentage >= 80 THEN 'B (80-89%)'
                WHEN g.percentage >= 70 THEN 'C (70-79%)'
                WHEN g.percentage >= 60 THEN 'D (60-69%)'
                ELSE 'F (<60%)'
            END as grade_type,
            COUNT(*) as count
        FROM grades g
        WHERE g.is_final = true
        GROUP BY grade_type
        ORDER BY count DESC
        """)
        grade_distribution = cursor.fetchall()

        cursor.close()
        connection.close()

        return {
            "total_records": grade_stats["total_records"] if grade_stats else 0,
            "usage_by_system": [dict(stat) for stat in usage_stats],
            "grade_distribution": [dict(dist) for dist in grade_distribution]
        }

    except Exception as e:
        logging.error(f"Error fetching evaluation statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching evaluation statistics: {str(e)}"
        )
