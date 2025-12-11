"""
Dashboard API endpoints
"""

import os
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.database import get_db
from app.core.config import settings
from app.auth import get_current_user, CurrentUser

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host=settings.DB_HOST,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=RealDictCursor
    )


@router.get("/stats")
def get_dashboard_stats(
    lang: str = 'en',
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get dashboard statistics

    Args:
        lang: Language code (en, ru, az) for localized content

    Returns:
        Dictionary with various statistics
    """
    # Validate language parameter
    if lang not in ['en', 'ru', 'az']:
        lang = 'en'

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get total students
        cur.execute("""
            SELECT COUNT(*) as total
            FROM students
            WHERE status = 'active'
        """)
        total_students = cur.fetchone()['total']

        # Get total teachers (staff members)
        cur.execute("""
            SELECT COUNT(*) as total
            FROM staff_members
            WHERE is_active = true
        """)
        total_teachers = cur.fetchone()['total']

        # Get total courses
        cur.execute("""
            SELECT COUNT(*) as total
            FROM courses
            WHERE is_active = true
        """)
        total_courses = cur.fetchone()['total']

        # Get active enrollments
        cur.execute("""
            SELECT COUNT(*) as total
            FROM course_enrollments
            WHERE enrollment_status = 'active'
        """)
        active_enrollments = cur.fetchone()['total']

        # Get pending requests
        cur.execute("""
            SELECT COUNT(*) as total
            FROM transcript_requests
            WHERE status = 'pending'
        """)
        pending_requests = cur.fetchone()['total']

        # Get recent activity
        cur.execute("""
            SELECT
                'enrollment' as type,
                ce.id,
                ce.enrollment_date as timestamp,
                p.first_name || ' ' || p.last_name as student_name,
                COALESCE(c.name->>%s, c.name->>'en', c.name->>'az') as course_name
            FROM course_enrollments ce
            LEFT JOIN students s ON ce.student_id = s.id
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN persons p ON u.id = p.user_id
            LEFT JOIN course_offerings co ON ce.course_offering_id = co.id
            LEFT JOIN courses c ON co.course_id = c.id
            WHERE ce.enrollment_date IS NOT NULL
            ORDER BY ce.enrollment_date DESC
            LIMIT 5
        """, (lang,))
        recent_enrollments = cur.fetchall()

        # Get organization structure stats
        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN type = 'faculty' THEN 1 ELSE 0 END) as faculties,
                SUM(CASE WHEN type = 'department' THEN 1 ELSE 0 END) as departments
            FROM organization_units
            WHERE is_active = true
        """)
        org_stats = cur.fetchone()

        return {
            "stats": {
                "total_students": total_students,
                "total_teachers": total_teachers,
                "total_courses": total_courses,
                "active_enrollments": active_enrollments,
                "pending_requests": pending_requests,
                "total_faculties": org_stats['faculties'] or 0,
                "total_departments": org_stats['departments'] or 0,
            },
            "recent_activity": [
                {
                    "type": item['type'],
                    "description": f"{item['student_name']} enrolled in {item['course_name']}" if item['student_name'] and item['course_name'] else "Enrollment activity",
                    "timestamp": item['timestamp'].isoformat() if item['timestamp'] else None
                }
                for item in recent_enrollments
            ]
        }

    finally:
        cur.close()
        conn.close()


@router.get("/quick-stats")
def get_quick_stats(
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get quick statistics for progress bars

    Returns:
        Dictionary with percentage statistics
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Student attendance rate (mock calculation - can be updated with real data)
        cur.execute("""
            SELECT
                COUNT(CASE WHEN status = 'present' THEN 1 END)::float /
                NULLIF(COUNT(*)::float, 0) * 100 as attendance_rate
            FROM attendance_records
            WHERE attendance_date >= CURRENT_DATE - INTERVAL '30 days'
        """)
        result = cur.fetchone()
        attendance_rate = round(result['attendance_rate'], 1) if result and result['attendance_rate'] else 0

        # Course completion rate
        cur.execute("""
            SELECT
                COUNT(CASE WHEN enrollment_status = 'completed' THEN 1 END)::float /
                NULLIF(COUNT(*)::float, 0) * 100 as completion_rate
            FROM course_enrollments
        """)
        result = cur.fetchone()
        completion_rate = round(result['completion_rate'], 1) if result and result['completion_rate'] else 0

        # Faculty utilization (teachers with active courses)
        cur.execute("""
            SELECT
                COUNT(DISTINCT CASE WHEN ci.instructor_id IS NOT NULL THEN sm.id END)::float /
                NULLIF(COUNT(DISTINCT sm.id)::float, 0) * 100 as utilization_rate
            FROM staff_members sm
            LEFT JOIN course_instructors ci ON ci.instructor_id = sm.user_id
            WHERE sm.is_active = true
        """)
        result = cur.fetchone()
        utilization_rate = round(result['utilization_rate'], 1) if result and result['utilization_rate'] else 0

        return {
            "attendance_rate": attendance_rate,
            "completion_rate": completion_rate,
            "utilization_rate": utilization_rate
        }

    finally:
        cur.close()
        conn.close()
