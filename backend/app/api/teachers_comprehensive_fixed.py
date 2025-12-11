"""
Comprehensive Teachers API - Authentication-free version for development

This module provides comprehensive teacher management endpoints without authentication
to enable frontend development and testing.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


class Teacher(BaseModel):
    """Complete teacher model with all database fields"""
    # Core identifiers
    id: int
    person_id: Optional[int] = None
    user_id: Optional[int] = None
    organization_id: Optional[int] = None
    
    # Personal Information
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    patronymic: Optional[str] = None
    pincode: Optional[str] = None
    birthdate: Optional[str] = None
    gender_id: Optional[int] = None
    gender_name: Optional[str] = None
    citizenship_id: Optional[int] = None
    citizenship_name: Optional[str] = None
    nationality_id: Optional[int] = None
    nationality_name: Optional[str] = None
    marital_id: Optional[int] = None
    marital_status: Optional[str] = None
    blood_type_id: Optional[int] = None
    blood_type: Optional[str] = None
    military_status: Optional[str] = None
    balance: Optional[str] = None
    hobbies: Optional[str] = None
    sports: Optional[str] = None
    family_information: Optional[str] = None
    secondary_education_info: Optional[str] = None
    past_fevers: Optional[str] = None
    
    # Professional Information
    organization_name: Optional[str] = None
    position_id: Optional[str] = None
    position_name: Optional[str] = None
    staff_type_id: Optional[int] = None
    staff_type_name: Optional[str] = None
    contract_type_id: Optional[int] = None
    contract_type_name: Optional[str] = None
    teaching: bool = False
    
    # User Account Information
    username: Optional[str] = None
    email: Optional[str] = None
    user_type: Optional[str] = None
    active: bool = True
    is_blocked: bool = False
    
    # System Information
    card_number: Optional[str] = None
    create_date: Optional[str] = None
    update_date: Optional[str] = None
    
    class Config:
        from_attributes = True


class TeacherStats(BaseModel):
    """Teacher statistics"""
    total_teachers: int
    active_teachers: int
    teaching_count: int
    organizations_count: int


class TeacherListResponse(BaseModel):
    """Response model for teacher list"""
    teachers: List[Teacher]
    total: int
    page: int
    per_page: int
    total_pages: int


class FilterOptions(BaseModel):
    """Available filter options"""
    organizations: List[dict]
    positions: List[dict]
    staff_types: List[dict]
    contract_types: List[dict]


@router.get("/teachers/stats", response_model=TeacherStats)
async def get_teacher_stats(db: Session = Depends(get_db)):
    """Get comprehensive teacher statistics"""
    try:
        stats_query = text("""
            SELECT 
                COUNT(*) as total_teachers,
                COUNT(CASE WHEN u.active = 1 THEN 1 END) as active_teachers,
                COUNT(CASE WHEN t.teaching = 1 THEN 1 END) as teaching_count,
                COUNT(DISTINCT t.organization_id) as organizations_count
            FROM teachers t
            LEFT JOIN users u ON t.user_id = u.id
        """)
        
        result = db.execute(stats_query)
        stats = result.fetchone()
        
        if not stats:
            return TeacherStats(
                total_teachers=0,
                active_teachers=0,
                teaching_count=0,
                organizations_count=0
            )
        
        return TeacherStats(
            total_teachers=stats.total_teachers,
            active_teachers=stats.active_teachers,
            teaching_count=stats.teaching_count,
            organizations_count=stats.organizations_count
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve teacher statistics: {str(e)}"
        )


@router.get("/teachers/filter-options", response_model=FilterOptions)
async def get_filter_options(db: Session = Depends(get_db)):
    """Get available filter options for teachers"""
    try:
        # Get organizations
        orgs_query = text("""
            SELECT DISTINCT o.id, o.name 
            FROM organizations o 
            INNER JOIN teachers t ON o.id = t.organization_id 
            ORDER BY o.name
        """)
        orgs_result = db.execute(orgs_query)
        organizations = [{"id": row.id, "name": row.name} for row in orgs_result.fetchall()]
        
        # Get positions from dictionaries
        positions_query = text("""
            SELECT DISTINCT d.id, COALESCE(d.name_az, d.name_en, d.name_ru, 'Unknown') as name
            FROM dictionaries d 
            INNER JOIN teachers t ON d.id = t.position_id 
            WHERE d.type_id IN (SELECT id FROM dictionary_types WHERE code LIKE '%position%' OR code LIKE '%post%')
            ORDER BY name
        """)
        positions_result = db.execute(positions_query)
        positions = [{"id": row.id, "name": row.name} for row in positions_result.fetchall()]
        
        # Get staff types from dictionaries
        staff_types_query = text("""
            SELECT DISTINCT d.id, COALESCE(d.name_az, d.name_en, d.name_ru, 'Unknown') as name
            FROM dictionaries d 
            INNER JOIN teachers t ON d.id = t.staff_type_id 
            WHERE d.type_id IN (SELECT id FROM dictionary_types WHERE code LIKE '%staff%' OR code LIKE '%type%')
            ORDER BY name
        """)
        staff_types_result = db.execute(staff_types_query)
        staff_types = [{"id": row.id, "name": row.name} for row in staff_types_result.fetchall()]
        
        # Get contract types from dictionaries
        contract_types_query = text("""
            SELECT DISTINCT d.id, COALESCE(d.name_az, d.name_en, d.name_ru, 'Unknown') as name
            FROM dictionaries d 
            INNER JOIN teachers t ON d.id = t.contract_type_id 
            WHERE d.type_id IN (SELECT id FROM dictionary_types WHERE code LIKE '%contract%' OR code LIKE '%employment%')
            ORDER BY name
        """)
        contract_types_result = db.execute(contract_types_query)
        contract_types = [{"id": row.id, "name": row.name} for row in contract_types_result.fetchall()]
        
        return FilterOptions(
            organizations=organizations,
            positions=positions,
            staff_types=staff_types,
            contract_types=contract_types
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve filter options: {str(e)}"
        )


@router.get("/teachers/", response_model=TeacherListResponse)
async def get_teachers(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name or pincode"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    position_id: Optional[int] = Query(None, description="Filter by position"),
    teaching: Optional[bool] = Query(None, description="Filter by teaching status"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """Get paginated list of teachers with comprehensive information"""
    try:
        offset = (page - 1) * per_page
        
        # Build the main query
        query = text("""
            SELECT DISTINCT
                t.id,
                t.person_id,
                t.user_id,
                t.organization_id,
                p.firstname,
                p.lastname,
                p.patronymic,
                p.pincode,
                p.birthdate,
                p.gender_id,
                p.citizenship_id,
                p.nationality_id,
                p.marital_id,
                p.blood_type_id,
                p.military_status,
                p.balance,
                p.hobbies,
                p.sports,
                p.family_information,
                p.secondary_education_info,
                p.past_fevers,
                o.name as organization_name,
                t.position_id,
                COALESCE(pos.name_az, pos.name_en, pos.name_ru, 'Unknown') as position_name,
                t.staff_type_id,
                COALESCE(st.name_az, st.name_en, st.name_ru, 'Unknown') as staff_type_name,
                t.contract_type_id,
                COALESCE(ct.name_az, ct.name_en, ct.name_ru, 'Unknown') as contract_type_name,
                CASE WHEN t.teaching = 1 THEN TRUE ELSE FALSE END as teaching,
                u.username,
                u.email,
                u.user_type,
                CASE WHEN u.active = 1 THEN TRUE ELSE FALSE END as active,
                CASE WHEN u.is_blocked = 1 THEN TRUE ELSE FALSE END as is_blocked,
                t.card_number,
                t.create_date,
                t.update_date,
                COALESCE(g.name_az, g.name_en, g.name_ru, 'Unknown') as gender_name,
                COALESCE(c.name_az, c.name_en, c.name_ru, 'Unknown') as citizenship_name,
                COALESCE(n.name_az, n.name_en, n.name_ru, 'Unknown') as nationality_name,
                COALESCE(m.name_az, m.name_en, m.name_ru, 'Unknown') as marital_status,
                COALESCE(bt.name_az, bt.name_en, bt.name_ru, 'Unknown') as blood_type
            FROM teachers t
            LEFT JOIN persons p ON t.person_id = p.id
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN organizations o ON t.organization_id = o.id
            LEFT JOIN dictionaries pos ON t.position_id = pos.id
            LEFT JOIN dictionaries st ON t.staff_type_id = st.id
            LEFT JOIN dictionaries ct ON t.contract_type_id = ct.id
            LEFT JOIN dictionaries g ON p.gender_id = g.id
            LEFT JOIN dictionaries c ON p.citizenship_id = c.id
            LEFT JOIN dictionaries n ON p.nationality_id = n.id
            LEFT JOIN dictionaries m ON p.marital_id = m.id
            LEFT JOIN dictionaries bt ON p.blood_type_id = bt.id
            WHERE 1=1
            AND (:search IS NULL OR 
                 LOWER(COALESCE(p.firstname, '') || ' ' || COALESCE(p.lastname, '')) LIKE LOWER(:search_pattern) OR
                 LOWER(COALESCE(p.pincode, '')) LIKE LOWER(:search_pattern))
            AND (:organization_id IS NULL OR t.organization_id = :organization_id)
            AND (:position_id IS NULL OR t.position_id = :position_id)
            AND (:teaching IS NULL OR t.teaching = :teaching_value)
            AND (:active IS NULL OR u.active = :active_value)
            ORDER BY p.lastname, p.firstname
            LIMIT :per_page OFFSET :offset
        """)
        
        # Prepare parameters
        search_pattern = f"%{search}%" if search else None
        teaching_value = 1 if teaching else (0 if teaching is False else None)
        active_value = 1 if active else (0 if active is False else None)
        
        # Execute query
        result = db.execute(query, {
            'search': search,
            'search_pattern': search_pattern,
            'organization_id': organization_id,
            'position_id': position_id,
            'teaching': teaching,
            'teaching_value': teaching_value,
            'active': active,
            'active_value': active_value,
            'per_page': per_page,
            'offset': offset
        })
        
        teachers_data = result.fetchall()
        
        # Get total count
        count_query = text("""
            SELECT COUNT(DISTINCT t.id)
            FROM teachers t
            LEFT JOIN persons p ON t.person_id = p.id
            LEFT JOIN users u ON t.user_id = u.id
            WHERE 1=1
            AND (:search IS NULL OR 
                 LOWER(COALESCE(p.firstname, '') || ' ' || COALESCE(p.lastname, '')) LIKE LOWER(:search_pattern) OR
                 LOWER(COALESCE(p.pincode, '')) LIKE LOWER(:search_pattern))
            AND (:organization_id IS NULL OR t.organization_id = :organization_id)
            AND (:position_id IS NULL OR t.position_id = :position_id)
            AND (:teaching IS NULL OR t.teaching = :teaching_value)
            AND (:active IS NULL OR u.active = :active_value)
        """)
        
        count_result = db.execute(count_query, {
            'search': search,
            'search_pattern': search_pattern,
            'organization_id': organization_id,
            'position_id': position_id,
            'teaching': teaching,
            'teaching_value': teaching_value,
            'active': active,
            'active_value': active_value
        })
        
        total = count_result.scalar()
        total_pages = (total + per_page - 1) // per_page
        
        # Convert to Teacher objects
        teachers = []
        for row in teachers_data:
            teacher = Teacher(
                id=row.id,
                person_id=row.person_id,
                user_id=row.user_id,
                organization_id=row.organization_id,
                firstname=row.firstname,
                lastname=row.lastname,
                patronymic=row.patronymic,
                pincode=row.pincode,
                birthdate=str(row.birthdate) if row.birthdate else None,
                gender_id=row.gender_id,
                gender_name=row.gender_name,
                citizenship_id=row.citizenship_id,
                citizenship_name=row.citizenship_name,
                nationality_id=row.nationality_id,
                nationality_name=row.nationality_name,
                marital_id=row.marital_id,
                marital_status=row.marital_status,
                blood_type_id=row.blood_type_id,
                blood_type=row.blood_type,
                military_status=row.military_status,
                balance=row.balance,
                hobbies=row.hobbies,
                sports=row.sports,
                family_information=row.family_information,
                secondary_education_info=row.secondary_education_info,
                past_fevers=row.past_fevers,
                organization_name=row.organization_name,
                position_id=str(row.position_id) if row.position_id else None,
                position_name=row.position_name,
                staff_type_id=row.staff_type_id,
                staff_type_name=row.staff_type_name,
                contract_type_id=row.contract_type_id,
                contract_type_name=row.contract_type_name,
                teaching=row.teaching,
                username=row.username,
                email=row.email,
                user_type=row.user_type,
                active=row.active,
                is_blocked=row.is_blocked,
                card_number=row.card_number,
                create_date=str(row.create_date) if row.create_date else None,
                update_date=str(row.update_date) if row.update_date else None
            )
            teachers.append(teacher)
        
        return TeacherListResponse(
            teachers=teachers,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve teachers: {str(e)}"
        )


@router.get("/teachers/{teacher_id}", response_model=Teacher)
async def get_teacher_detail(teacher_id: int, db: Session = Depends(get_db)):
    """Get detailed information for a specific teacher"""
    try:
        teacher_query = text("""
            SELECT DISTINCT
                t.id,
                t.person_id,
                t.user_id,
                t.organization_id,
                p.firstname,
                p.lastname,
                p.patronymic,
                p.pincode,
                p.birthdate,
                p.gender_id,
                p.citizenship_id,
                p.nationality_id,
                p.marital_id,
                p.blood_type_id,
                p.military_status,
                p.balance,
                p.hobbies,
                p.sports,
                p.family_information,
                p.secondary_education_info,
                p.past_fevers,
                o.name as organization_name,
                t.position_id,
                COALESCE(pos.name_az, pos.name_en, pos.name_ru, 'Unknown') as position_name,
                t.staff_type_id,
                COALESCE(st.name_az, st.name_en, st.name_ru, 'Unknown') as staff_type_name,
                t.contract_type_id,
                COALESCE(ct.name_az, ct.name_en, ct.name_ru, 'Unknown') as contract_type_name,
                CASE WHEN t.teaching = 1 THEN TRUE ELSE FALSE END as teaching,
                u.username,
                u.email,
                u.user_type,
                CASE WHEN u.active = 1 THEN TRUE ELSE FALSE END as active,
                CASE WHEN u.is_blocked = 1 THEN TRUE ELSE FALSE END as is_blocked,
                t.card_number,
                t.create_date,
                t.update_date,
                COALESCE(g.name_az, g.name_en, g.name_ru, 'Unknown') as gender_name,
                COALESCE(c.name_az, c.name_en, c.name_ru, 'Unknown') as citizenship_name,
                COALESCE(n.name_az, n.name_en, n.name_ru, 'Unknown') as nationality_name,
                COALESCE(m.name_az, m.name_en, m.name_ru, 'Unknown') as marital_status,
                COALESCE(bt.name_az, bt.name_en, bt.name_ru, 'Unknown') as blood_type
            FROM teachers t
            LEFT JOIN persons p ON t.person_id = p.id
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN organizations o ON t.organization_id = o.id
            LEFT JOIN dictionaries pos ON t.position_id = pos.id
            LEFT JOIN dictionaries st ON t.staff_type_id = st.id
            LEFT JOIN dictionaries ct ON t.contract_type_id = ct.id
            LEFT JOIN dictionaries g ON p.gender_id = g.id
            LEFT JOIN dictionaries c ON p.citizenship_id = c.id
            LEFT JOIN dictionaries n ON p.nationality_id = n.id
            LEFT JOIN dictionaries m ON p.marital_id = m.id
            LEFT JOIN dictionaries bt ON p.blood_type_id = bt.id
            WHERE t.id = :teacher_id
        """)
        
        result = db.execute(teacher_query, {"teacher_id": teacher_id})
        teacher_data = result.fetchone()
        
        if not teacher_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        # Create teacher object
        teacher = Teacher(
            id=teacher_data.id,
            person_id=teacher_data.person_id,
            user_id=teacher_data.user_id,
            organization_id=teacher_data.organization_id,
            firstname=teacher_data.firstname,
            lastname=teacher_data.lastname,
            patronymic=teacher_data.patronymic,
            pincode=teacher_data.pincode,
            birthdate=str(teacher_data.birthdate) if teacher_data.birthdate else None,
            gender_id=teacher_data.gender_id,
            gender_name=teacher_data.gender_name,
            citizenship_id=teacher_data.citizenship_id,
            citizenship_name=teacher_data.citizenship_name,
            nationality_id=teacher_data.nationality_id,
            nationality_name=teacher_data.nationality_name,
            marital_id=teacher_data.marital_id,
            marital_status=teacher_data.marital_status,
            blood_type_id=teacher_data.blood_type_id,
            blood_type=teacher_data.blood_type,
            military_status=teacher_data.military_status,
            balance=teacher_data.balance,
            hobbies=teacher_data.hobbies,
            sports=teacher_data.sports,
            family_information=teacher_data.family_information,
            secondary_education_info=teacher_data.secondary_education_info,
            past_fevers=teacher_data.past_fevers,
            organization_name=teacher_data.organization_name,
            position_id=str(teacher_data.position_id) if teacher_data.position_id else None,
            position_name=teacher_data.position_name,
            staff_type_id=teacher_data.staff_type_id,
            staff_type_name=teacher_data.staff_type_name,
            contract_type_id=teacher_data.contract_type_id,
            contract_type_name=teacher_data.contract_type_name,
            teaching=teacher_data.teaching,
            username=teacher_data.username,
            email=teacher_data.email,
            user_type=teacher_data.user_type,
            active=teacher_data.active,
            is_blocked=teacher_data.is_blocked,
            card_number=teacher_data.card_number,
            create_date=str(teacher_data.create_date) if teacher_data.create_date else None,
            update_date=str(teacher_data.update_date) if teacher_data.update_date else None
        )
        
        return teacher
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve teacher details: {str(e)}"
        )