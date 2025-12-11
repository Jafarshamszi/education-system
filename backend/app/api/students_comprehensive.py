"""
Comprehensive Students API with detailed information
"""

from fastapi import APIRouter, HTTPException, Query
import os
from pydantic import BaseModel
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def convert_large_ints_to_strings(data):
    """Convert large integers to strings to avoid JS precision issues"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # MAX_SAFE_INTEGER = 9007199254740991
            if isinstance(value, int) and abs(value) > 9007199254740991:
                result[key] = str(value)
            elif isinstance(value, (dict, list)):
                result[key] = convert_large_ints_to_strings(value)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [convert_large_ints_to_strings(item) for item in data]
    else:
        return data


def get_db_connection():
    """Create database connection"""
    try:
        return psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )


class StudentUpdateRequest(BaseModel):
    """Request model for updating student information"""
    # Personal information (persons table)
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    patronymic: Optional[str] = None
    pincode: Optional[str] = None
    birthdate: Optional[str] = None
    gender_id: Optional[int] = None
    citizenship_id: Optional[int] = None
    nationality_id: Optional[int] = None
    marital_id: Optional[int] = None
    blood_type_id: Optional[int] = None
    
    # Academic information (students table)
    org_id: Optional[int] = None  # Organization/specialization
    score: Optional[str] = None
    card_number: Optional[str] = None
    yearly_payment: Optional[str] = None
    payment_count: Optional[str] = None
    education_line_id: Optional[int] = None
    education_type_id: Optional[int] = None
    education_payment_type_id: Optional[int] = None
    education_lang_id: Optional[int] = None


@router.get("/list")
async def get_students_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    org_id: Optional[int] = Query(None),
    education_type: Optional[str] = Query(None),
    education_level: Optional[str] = Query(None),
    active_only: bool = Query(True)
):
    """Get paginated list of students with filtering"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Build WHERE conditions
        where_conditions = []
        params = []
        
        if active_only:
            where_conditions.append("s.active = %s")
            params.append(1)
        
        if search:
            where_conditions.append("""
                (LOWER(p.firstname) LIKE LOWER(%s) 
                 OR LOWER(p.lastname) LIKE LOWER(%s)
                 OR LOWER(p.patronymic) LIKE LOWER(%s)
                 OR LOWER(p.pincode) LIKE LOWER(%s)
                 OR LOWER(s.card_number) LIKE LOWER(%s))
            """)
            search_pattern = f"%{search}%"
            params.extend([search_pattern] * 5)
        
        if org_id:
            where_conditions.append("s.org_id = %s")
            params.append(org_id)
        
        if education_type:
            where_conditions.append("LOWER(student_edu_type_dict.name_en) = LOWER(%s)")
            params.append(education_type)
        
        if education_level:
            where_conditions.append("LOWER(group_edu_dict.name_en) = LOWER(%s)")
            params.append(education_level)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Main query
        query = f"""
            SELECT DISTINCT
                s.id,
                p.firstname,
                p.lastname,
                p.patronymic,
                p.pincode,
                p.birthdate,
                p.gender_id,
                gender_dict.name_en as gender_name,
                s.card_number,
                s.score,
                s.active,
                s.create_date,
                s.org_id,
                
                -- Organization info with academic specialization
                COALESCE(org_dict.name_en, 'Unknown Organization') as organization_name,
                
                -- Academic specialization mapping
                CASE
                    -- Direct specialization lookup from org_names
                    WHEN org_names.id = 220223053906474743 THEN 'IT'
                    WHEN org_names.id = 220223110107192121 THEN 'Translation'
                    WHEN org_names.id = 220223060403889770 THEN 'Economics'
                    WHEN org_names.id = 220223063509591259 THEN 'Finance'
                    WHEN org_names.id = 220223065408917441 THEN 'Marketing'
                    WHEN org_names.id = 2202230719043010785 THEN 'Management'
                    WHEN org_names.id = 220223074000992414 THEN 'Accounting'
                    WHEN org_names.id = 220223095607479549 THEN 'Social Work'
                    WHEN org_names.id = 220223044808654357 THEN 'Business Admin'
                    WHEN org_names.id = 220223091501629830 THEN 'Accounting & Audit'
                    WHEN org_names.id = 220223043104107693 THEN 'Int Trade & Logistics'
                    WHEN org_names.id = 220223050501833647 THEN 'Public Admin'
                    WHEN org_names.id = 220223093709483260 THEN 'Industrial Management'
                    WHEN org_names.id = 220223052408185061 THEN 'World Economics'
                    -- Master's specializations
                    WHEN org_names.id = 220211034000856306 THEN 'Finance (MA)'
                    WHEN org_names.id = 230916013204247889 THEN 'Social Work (MA)'
                    WHEN org_names.id = 220211043501479568 THEN 'Management (MA)'
                    WHEN org_names.id = 220211044509326042 THEN 'Marketing (MA)'
                    WHEN org_names.id = 220211042200292305 THEN 'Economics (MA)'
                    WHEN org_names.id = 220211032207772797 THEN 'World Economics (MA)'
                    WHEN org_names.id = 220211051502179233 THEN 'Business Admin (MA)'
                    WHEN org_names.id = 220211035209269181 THEN 'Accounting & Audit (MA)'
                    WHEN org_names.id = 220211041006847435 THEN 'Public Admin (MA)'
                    -- Organization hierarchy mapping
                    WHEN parent_org.id = 220216125001718917 THEN 'Business & Economics'
                    WHEN parent_org.id = 220216120802871763 THEN 'Management & Administration'
                    WHEN parent_org.id = 220209071708305289 THEN 'Business Administration'
                    ELSE NULL
                END as specialization_name_english,
                
                -- Education group info
                eg.name as group_name,
                COALESCE(group_edu_dict.name_en, 'Unknown') as education_level,
                
                -- Education type and line
                COALESCE(student_edu_type_dict.name_en, 'Unknown') as education_type,
                COALESCE(student_edu_line_dict.name_en, 'Unknown') as education_line,
                
                -- Payment info
                s.yearly_payment,
                s.payment_count
                
            FROM students s
            LEFT JOIN persons p ON s.person_id = p.id
            LEFT JOIN dictionaries gender_dict ON p.gender_id = gender_dict.id
            LEFT JOIN organizations org ON s.org_id = org.id
            LEFT JOIN organizations parent_org ON org.parent_id = parent_org.id
            LEFT JOIN dictionaries org_dict ON org.dictionary_name_id = org_dict.id
            LEFT JOIN org_names ON (s.org_id = org_names.id OR parent_org.id = org_names.id)
            LEFT JOIN education_group_student egs ON s.id = egs.student_id AND egs.active = 1
            LEFT JOIN education_group eg ON egs.education_group_id = eg.id
            LEFT JOIN dictionaries group_edu_dict ON eg.education_level_id = group_edu_dict.id
            LEFT JOIN dictionaries student_edu_type_dict ON s.education_type_id = student_edu_type_dict.id
            LEFT JOIN dictionaries student_edu_line_dict ON s.education_line_id = student_edu_line_dict.id
            {where_clause}
            ORDER BY p.lastname, p.firstname
            LIMIT %s OFFSET %s
        """
        
        params.extend([per_page, offset])
        cursor.execute(query, params)
        students = cursor.fetchall()
        
        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(DISTINCT s.id)
            FROM students s
            LEFT JOIN persons p ON s.person_id = p.id
            LEFT JOIN organizations org ON s.org_id = org.id
            LEFT JOIN organizations parent_org ON org.parent_id = parent_org.id
            LEFT JOIN dictionaries org_dict ON org.dictionary_name_id = org_dict.id
            LEFT JOIN org_names ON (s.org_id = org_names.id OR parent_org.id = org_names.id)
            LEFT JOIN education_group_student egs ON s.id = egs.student_id AND egs.active = 1
            LEFT JOIN education_group eg ON egs.education_group_id = eg.id
            LEFT JOIN dictionaries group_edu_dict ON eg.education_level_id = group_edu_dict.id
            LEFT JOIN dictionaries student_edu_type_dict ON s.education_type_id = student_edu_type_dict.id
            LEFT JOIN dictionaries student_edu_line_dict ON s.education_line_id = student_edu_line_dict.id
            LEFT JOIN dictionaries gender_dict ON p.gender_id = gender_dict.id
            {where_clause}
        """
        
        cursor.execute(count_query, params[:-2])  # Exclude LIMIT and OFFSET params
        total_count = cursor.fetchone()['count']
        
        return convert_large_ints_to_strings({
            "students": [dict(student) for student in students],
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_students": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching students: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch students: {str(e)}")
    finally:
        if connection:
            connection.close()


@router.get("/detail/{student_id}")
async def get_student_detail(student_id: int):
    """Get comprehensive details for a specific student"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get comprehensive student information
        cursor.execute("""
            SELECT 
                s.id,
                s.person_id,
                s.user_id,
                s.org_id,
                s.card_number,
                s.score,
                s.yearly_payment,
                s.payment_count,
                s.active,
                s.create_date,
                s.update_date,
                
                -- Personal information
                p.firstname,
                p.lastname,
                p.patronymic,
                p.pincode,
                p.birthdate,
                p.balance,
                p.hobbies,
                p.sports,
                p.family_information,
                p.secondary_education_info,
                p.past_fevers,
                
                -- ID fields for editing
                p.gender_id,
                p.citizenship_id,
                p.nationality_id,
                p.marital_id,
                p.blood_type_id,
                s.education_line_id,
                s.education_type_id,
                s.education_payment_type_id,
                s.education_lang_id,
                
                -- Gender, citizenship, etc.
                gender_dict.name_en as gender_name,
                gender_dict.name_az as gender_name_az,
                citizenship_dict.name_en as citizenship_name,
                nationality_dict.name_en as nationality_name,
                marital_dict.name_en as marital_status,
                social_dict.name_en as social_status,
                orphan_dict.name_en as orphan_status,
                military_dict.name_en as military_status,
                blood_type_dict.name_en as blood_type,
                
                -- Organization and academic info
                COALESCE(org_names.name_en, org_names.name_az, 'Unknown Organization') as organization_name,
                
                -- Academic specialization
                CASE
                    WHEN org_names.id = 220223053906474743 THEN 'IT'
                    WHEN org_names.id = 220223110107192121 THEN 'Translation'
                    WHEN org_names.id = 220223060403889770 THEN 'Economics'
                    WHEN org_names.id = 220223063509591259 THEN 'Finance'
                    WHEN org_names.id = 220223065408917441 THEN 'Marketing'
                    WHEN org_names.id = 2202230719043010785 THEN 'Management'
                    WHEN org_names.id = 220223074000992414 THEN 'Accounting'
                    WHEN org_names.id = 220223095607479549 THEN 'Social Work'
                    WHEN org_names.id = 220223044808654357 THEN 'Business Admin'
                    WHEN org_names.id = 220223091501629830 THEN 'Accounting & Audit'
                    WHEN org_names.id = 220223043104107693 THEN 'Int Trade & Logistics'
                    WHEN org_names.id = 220223050501833647 THEN 'Public Admin'
                    WHEN org_names.id = 220223093709483260 THEN 'Industrial Management'
                    WHEN org_names.id = 220223052408185061 THEN 'World Economics'
                    -- Master's programs
                    WHEN org_names.id = 220211034000856306 THEN 'Finance (MA)'
                    WHEN org_names.id = 230916013204247889 THEN 'Social Work (MA)'
                    WHEN org_names.id = 220211043501479568 THEN 'Management (MA)'
                    WHEN org_names.id = 220211044509326042 THEN 'Marketing (MA)'
                    WHEN org_names.id = 220211042200292305 THEN 'Economics (MA)'
                    WHEN org_names.id = 220211032207772797 THEN 'World Economics (MA)'
                    WHEN org_names.id = 220211051502179233 THEN 'Business Admin (MA)'
                    WHEN org_names.id = 220211035209269181 THEN 'Accounting & Audit (MA)'
                    WHEN org_names.id = 220211041006847435 THEN 'Public Admin (MA)'
                    -- Hierarchy mapping
                    WHEN parent_org.id = 220216125001718917 THEN 'Business & Economics'
                    WHEN parent_org.id = 220216120802871763 THEN 'Management & Administration'
                    WHEN parent_org.id = 220209071708305289 THEN 'Business Administration'
                    ELSE NULL
                END as specialization_name_english,
                
                -- Education group info
                eg.name as group_name,
                eg.id as group_id,
                COALESCE(group_edu_dict.name_en, 'Unknown') as education_level,
                COALESCE(group_edu_type_dict.name_en, 'Unknown') as group_education_type,
                
                -- Student education details
                COALESCE(student_edu_type_dict.name_en, 'Unknown') as education_type,
                COALESCE(student_edu_line_dict.name_en, 'Unknown') as education_line,
                COALESCE(payment_type_dict.name_en, 'Unknown') as payment_type,
                COALESCE(education_lang_dict.name_en, 'Unknown') as education_language
                
            FROM students s
            LEFT JOIN persons p ON s.person_id = p.id
            LEFT JOIN dictionaries gender_dict ON p.gender_id = gender_dict.id
            LEFT JOIN dictionaries citizenship_dict ON p.citizenship_id = citizenship_dict.id
            LEFT JOIN dictionaries nationality_dict ON p.nationality_id = nationality_dict.id
            LEFT JOIN dictionaries marital_dict ON p.marital_id = marital_dict.id
            LEFT JOIN dictionaries social_dict ON p.social_id = social_dict.id
            LEFT JOIN dictionaries orphan_dict ON p.orphan_id = orphan_dict.id
            LEFT JOIN dictionaries military_dict ON p.military_id = military_dict.id
            LEFT JOIN dictionaries blood_type_dict ON p.blood_type_id = blood_type_dict.id
            LEFT JOIN organizations org ON s.org_id = org.id
            LEFT JOIN organizations parent_org ON org.parent_id = parent_org.id
            LEFT JOIN org_names ON org.dictionary_name_id = org_names.id
            LEFT JOIN education_group_student egs ON s.id = egs.student_id AND egs.active = 1
            LEFT JOIN education_group eg ON egs.education_group_id = eg.id
            LEFT JOIN dictionaries group_edu_dict ON eg.education_level_id = group_edu_dict.id
            LEFT JOIN dictionaries group_edu_type_dict ON eg.education_type_id = group_edu_type_dict.id
            LEFT JOIN dictionaries student_edu_type_dict ON s.education_type_id = student_edu_type_dict.id
            LEFT JOIN dictionaries student_edu_line_dict ON s.education_line_id = student_edu_line_dict.id
            LEFT JOIN dictionaries payment_type_dict ON s.education_payment_type_id = payment_type_dict.id
            LEFT JOIN dictionaries education_lang_dict ON s.education_lang_id = education_lang_dict.id
            WHERE s.id = %s
        """, (student_id,))
        
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Get attendance summary for this student (if attendance table exists)
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    COUNT(CASE WHEN a.status = 1 THEN 1 END) as present_count,
                    COUNT(CASE WHEN a.status = 0 THEN 1 END) as absent_count,
                    COUNT(CASE WHEN a.status = 2 THEN 1 END) as late_count,
                    ROUND(
                        (COUNT(CASE WHEN a.status = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)), 2
                    ) as attendance_percentage
                FROM attendance a
                WHERE a.student_id = %s
            """, (student_id,))
            
            attendance_summary = cursor.fetchone()
        except psycopg2.Error:
            # Attendance table doesn't exist
            attendance_summary = None
        
        # Get recent grades (if grades table exists)
        try:
            cursor.execute("""
                SELECT 
                    g.id,
                    g.score,
                    g.max_score,
                    g.grade_date,
                    g.comment,
                    COALESCE(subject_dict.name_en, 'Unknown Subject') as subject_name
                FROM grades g
                LEFT JOIN dictionaries subject_dict ON g.subject_id = subject_dict.id
                WHERE g.student_id = %s
                ORDER BY g.grade_date DESC
                LIMIT 10
            """, (student_id,))
            
            recent_grades = cursor.fetchall()
        except psycopg2.Error:
            # Grades table doesn't exist
            recent_grades = []
        
        # Get recent orders (if any)
        try:
            cursor.execute("""
                SELECT 
                    o.id,
                    o.serial,
                    o.order_date,
                    COALESCE(order_type_dict.name_en, 'Unknown') as order_type,
                    o.active
                FROM person_orders po
                LEFT JOIN orders o ON po.order_id = o.id
                LEFT JOIN dictionaries order_type_dict ON o.type_id = order_type_dict.id
                WHERE po.student_id = %s
                ORDER BY o.order_date DESC
                LIMIT 5
            """, (student_id,))
            
            recent_orders = cursor.fetchall()
        except psycopg2.Error:
            # Orders table issues
            recent_orders = []
        
        return convert_large_ints_to_strings({
            "student": dict(student),
            "attendance_summary": dict(attendance_summary) if attendance_summary else None,
            "recent_grades": [dict(grade) for grade in recent_grades],
            "recent_orders": [dict(order) for order in recent_orders]
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) without wrapping them
        raise
    except Exception as e:
        logger.error(f"Error fetching student detail: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch student details: {str(e)}"
        )
    finally:
        if connection:
            connection.close()


@router.put("/update/{student_id}")
async def update_student(student_id: str, student_data: StudentUpdateRequest):
    """Update student information"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # First, verify the student exists
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Get student's person_id for updating person table
        cursor.execute(
            "SELECT person_id FROM students WHERE id = %s",
            (student_id,)
        )
        person_result = cursor.fetchone()
        person_id = person_result['person_id']
        
        # Update students table fields
        student_updates = []
        student_params = []
        
        if student_data.org_id is not None:
            student_updates.append("org_id = %s")
            student_params.append(student_data.org_id)
        if student_data.score is not None:
            student_updates.append("score = %s")
            student_params.append(student_data.score)
        if student_data.card_number is not None:
            student_updates.append("card_number = %s")
            student_params.append(student_data.card_number)
        if student_data.yearly_payment is not None:
            student_updates.append("yearly_payment = %s")
            student_params.append(student_data.yearly_payment)
        if student_data.payment_count is not None:
            student_updates.append("payment_count = %s")
            student_params.append(student_data.payment_count)
        if student_data.education_line_id is not None:
            student_updates.append("education_line_id = %s")
            student_params.append(student_data.education_line_id)
        if student_data.education_type_id is not None:
            student_updates.append("education_type_id = %s")
            student_params.append(student_data.education_type_id)
        if student_data.education_payment_type_id is not None:
            student_updates.append("education_payment_type_id = %s")
            student_params.append(student_data.education_payment_type_id)
        if student_data.education_lang_id is not None:
            student_updates.append("education_lang_id = %s")
            student_params.append(student_data.education_lang_id)
        
        if student_updates:
            student_params.append(student_id)
            student_query = f"""
                UPDATE students
                SET {', '.join(student_updates)}, update_date = NOW()
                WHERE id = %s
            """
            cursor.execute(student_query, student_params)
        
        # Update persons table fields
        person_updates = []
        person_params = []
        
        if student_data.firstname is not None:
            person_updates.append("firstname = %s")
            person_params.append(student_data.firstname)
        if student_data.lastname is not None:
            person_updates.append("lastname = %s")
            person_params.append(student_data.lastname)
        if student_data.patronymic is not None:
            person_updates.append("patronymic = %s")
            person_params.append(student_data.patronymic)
        if student_data.pincode is not None:
            person_updates.append("pincode = %s")
            person_params.append(student_data.pincode)
        if student_data.birthdate is not None:
            person_updates.append("birthdate = %s")
            person_params.append(student_data.birthdate)
        if student_data.gender_id is not None:
            person_updates.append("gender_id = %s")
            person_params.append(student_data.gender_id)
        if student_data.citizenship_id is not None:
            person_updates.append("citizenship_id = %s")
            person_params.append(student_data.citizenship_id)
        if student_data.nationality_id is not None:
            person_updates.append("nationality_id = %s")
            person_params.append(student_data.nationality_id)
        if student_data.marital_id is not None:
            person_updates.append("marital_id = %s")
            person_params.append(student_data.marital_id)
        if student_data.blood_type_id is not None:
            person_updates.append("blood_type_id = %s")
            person_params.append(student_data.blood_type_id)
        
        if person_updates:
            person_params.append(person_id)
            person_query = f"""
                UPDATE persons
                SET {', '.join(person_updates)}
                WHERE id = %s
            """
            cursor.execute(person_query, person_params)
        
        # Commit the transaction
        connection.commit()
        
        return {
            "message": "Student updated successfully",
            "student_id": student_id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) without wrapping them
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Error updating student: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update student: {str(e)}"
        )
    finally:
        if connection:
            connection.close()


@router.get("/stats")
async def get_students_stats():
    """Get statistics about students"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Total students
        cursor.execute("SELECT COUNT(*) as total FROM students WHERE active = 1")
        total_students = cursor.fetchone()['total']
        
        # By education level
        cursor.execute("""
            SELECT 
                COALESCE(group_edu_dict.name_en, 'Unknown') as education_level,
                COUNT(DISTINCT s.id) as count
            FROM students s
            LEFT JOIN education_group_student egs ON s.id = egs.student_id AND egs.active = 1
            LEFT JOIN education_group eg ON egs.education_group_id = eg.id
            LEFT JOIN dictionaries group_edu_dict ON eg.education_level_id = group_edu_dict.id
            WHERE s.active = 1
            GROUP BY group_edu_dict.name_en
            ORDER BY count DESC
        """)
        by_education_level = cursor.fetchall()
        
        # By specialization
        cursor.execute("""
            SELECT 
                CASE
                    WHEN org_names.id = 220223053906474743 THEN 'IT'
                    WHEN org_names.id = 220223110107192121 THEN 'Translation'
                    WHEN org_names.id = 220223060403889770 THEN 'Economics'
                    WHEN org_names.id = 220223063509591259 THEN 'Finance'
                    WHEN org_names.id = 220223065408917441 THEN 'Marketing'
                    WHEN org_names.id = 2202230719043010785 THEN 'Management'
                    WHEN org_names.id = 220223074000992414 THEN 'Accounting'
                    WHEN org_names.id = 220223095607479549 THEN 'Social Work'
                    WHEN org_names.id = 220223044808654357 THEN 'Business Admin'
                    WHEN org_names.id = 220223091501629830 THEN 'Accounting & Audit'
                    WHEN org_names.id = 220223043104107693 THEN 'Int Trade & Logistics'
                    WHEN org_names.id = 220223050501833647 THEN 'Public Admin'
                    WHEN org_names.id = 220223093709483260 THEN 'Industrial Management'
                    WHEN org_names.id = 220223052408185061 THEN 'World Economics'
                    WHEN org_names.id = 220211034000856306 THEN 'Finance (MA)'
                    WHEN org_names.id = 230916013204247889 THEN 'Social Work (MA)'
                    WHEN org_names.id = 220211043501479568 THEN 'Management (MA)'
                    WHEN org_names.id = 220211044509326042 THEN 'Marketing (MA)'
                    WHEN org_names.id = 220211042200292305 THEN 'Economics (MA)'
                    WHEN org_names.id = 220211032207772797 THEN 'World Economics (MA)'
                    WHEN org_names.id = 220211051502179233 THEN 'Business Admin (MA)'
                    WHEN org_names.id = 220211035209269181 THEN 'Accounting & Audit (MA)'
                    WHEN org_names.id = 220211041006847435 THEN 'Public Admin (MA)'
                    WHEN parent_org.id = 220216125001718917 THEN 'Business & Economics'
                    WHEN parent_org.id = 220216120802871763 THEN 'Management & Administration'
                    WHEN parent_org.id = 220209071708305289 THEN 'Business Administration'
                    ELSE 'Other'
                END as specialization,
                COUNT(DISTINCT s.id) as count
            FROM students s
            LEFT JOIN organizations org ON s.org_id = org.id
            LEFT JOIN organizations parent_org ON org.parent_id = parent_org.id
            LEFT JOIN org_names ON (s.org_id = org_names.id OR parent_org.id = org_names.id)
            WHERE s.active = 1
            GROUP BY specialization
            ORDER BY count DESC
        """)
        by_specialization = cursor.fetchall()
        
        return convert_large_ints_to_strings({
            "total_students": total_students,
            "by_education_level": [dict(row) for row in by_education_level],
            "by_specialization": [dict(row) for row in by_specialization]
        })
        
    except Exception as e:
        logger.error(f"Error fetching student stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch student statistics: {str(e)}")
    finally:
        if connection:
            connection.close()


@router.get("/filters")
async def get_filter_options():
    """Get available filter options for students"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get unique education types
        cursor.execute("""
            SELECT DISTINCT 
                COALESCE(student_edu_type_dict.name_en, 'Unknown') as education_type
            FROM students s
            LEFT JOIN dictionaries student_edu_type_dict ON s.education_type_id = student_edu_type_dict.id
            WHERE s.active = 1 AND student_edu_type_dict.name_en IS NOT NULL
            ORDER BY education_type
        """)
        education_types = [row['education_type'] for row in cursor.fetchall()]
        
        # Get unique education levels
        cursor.execute("""
            SELECT DISTINCT 
                COALESCE(group_edu_dict.name_en, 'Unknown') as education_level
            FROM students s
            LEFT JOIN education_group_student egs ON s.id = egs.student_id AND egs.active = 1
            LEFT JOIN education_group eg ON egs.education_group_id = eg.id
            LEFT JOIN dictionaries group_edu_dict ON eg.education_level_id = group_edu_dict.id
            WHERE s.active = 1 AND group_edu_dict.name_en IS NOT NULL
            ORDER BY education_level
        """)
        education_levels = [row['education_level'] for row in cursor.fetchall()]
        
        # Get unique organizations
        cursor.execute("""
            SELECT DISTINCT 
                s.org_id,
                COALESCE(org_dict.name_en, org_dict.name_az, 'Unknown') as organization_name
            FROM students s
            LEFT JOIN organizations org ON s.org_id = org.id
            LEFT JOIN dictionaries org_dict ON org.dictionary_name_id = org_dict.id
            WHERE s.active = 1 AND s.org_id IS NOT NULL
            ORDER BY organization_name
            LIMIT 50
        """)
        organizations = [{"id": row['org_id'], "name": row['organization_name']} for row in cursor.fetchall()]
        
        return convert_large_ints_to_strings({
            "education_types": education_types,
            "education_levels": education_levels,
            "organizations": organizations
        })
        
    except Exception as e:
        logger.error(f"Error fetching filter options: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch filter options: {str(e)}")
    finally:
        if connection:
            connection.close()


@router.get("/form-data")
async def get_form_data():
    """Get dropdown data for student edit form"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get organizations from org_names table
        cursor.execute("""
            SELECT org.id, COALESCE(names.name_en, names.name_az, 'Unknown') as name
            FROM organizations org 
            LEFT JOIN org_names names ON org.dictionary_name_id = names.id
            WHERE org.active = 1 
            ORDER BY names.name_en
        """)
        organizations = cursor.fetchall()
        
        # Get genders (type_id = 100000001)
        cursor.execute("""
            SELECT id, name_en as name
            FROM dictionaries 
            WHERE type_id = 100000001 AND active = 1
            ORDER BY name_en
        """)
        genders = cursor.fetchall()
        
        # Get citizenships (type_id = 100000007)
        cursor.execute("""
            SELECT id, name_en as name
            FROM dictionaries 
            WHERE type_id = 100000007 AND active = 1
            ORDER BY name_en
        """)
        citizenships = cursor.fetchall()
        
        # Get nationalities (type_id = 100000006, 100000022, 100000071)
        cursor.execute("""
            SELECT id, name_en as name
            FROM dictionaries 
            WHERE type_id IN (100000006, 100000022, 100000071) AND active = 1
            ORDER BY name_en
        """)
        nationalities = cursor.fetchall()
        
        # Get marital statuses - let me find the correct type_id
        cursor.execute("""
            SELECT id, name_en as name
            FROM dictionaries 
            WHERE name_en IN ('Single', 'Married') AND active = 1
            ORDER BY name_en
        """)
        marital_statuses = cursor.fetchall()
        
        # Get blood types - they are stored as "I qrup", "II qrup", etc.
        cursor.execute("""
            SELECT id, name_en as name
            FROM dictionaries 
            WHERE name_en LIKE '%qrup' AND active = 1
            ORDER BY name_en
        """)
        blood_types = cursor.fetchall()
        
        # Get education types - find the appropriate type_id
        cursor.execute("""
            SELECT id, name_en as name
            FROM dictionaries 
            WHERE name_en IN ('Intramural', 'Extramural', 'Evening') AND active = 1
            ORDER BY name_en
        """)
        education_types = cursor.fetchall()
        
        return convert_large_ints_to_strings({
            "organizations": organizations,
            "genders": genders,
            "citizenships": citizenships,
            "nationalities": nationalities,
            "marital_statuses": marital_statuses,
            "blood_types": blood_types,
            "education_types": education_types
        })

    except Exception as e:
        logger.error(f"Error fetching form data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch form data: {str(e)}"
        )
    finally:
        if connection:
            connection.close()