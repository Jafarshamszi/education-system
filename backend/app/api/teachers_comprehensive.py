"""
Teachers comprehensive API router for FastAPI service
Migrated from Django to provide unified FastAPI backend
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, distinct
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.teacher import Teacher
from app.models.person import Person
from app.models.user import User
from app.models.account import Account
from app.models.organization import Organization
from app.models.dictionary import Dictionary

# Create router for teachers comprehensive endpoints
router = APIRouter(prefix="/teachers", tags=["teachers"])


# Pydantic models for responses
class TeacherBase(BaseModel):
    id: int
    person_id: Optional[int] = None
    user_id: Optional[int] = None
    organization_id: Optional[int] = None
    staff_type_id: Optional[int] = None
    position_id: Optional[int] = None
    contract_type_id: Optional[int] = None
    teaching: Optional[int] = None
    card_number: Optional[str] = None

    class Config:
        from_attributes = True


class PersonInfo(BaseModel):
    id: int
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    patronymic: Optional[str] = None
    pincode: Optional[str] = None
    birthdate: Optional[str] = None

    class Config:
        from_attributes = True


class OrganizationInfo(BaseModel):
    id: int
    name: Optional[str] = None

    class Config:
        from_attributes = True


class DictionaryInfo(BaseModel):
    id: int
    name_en: Optional[str] = None
    name_az: Optional[str] = None
    code: Optional[str] = None

    class Config:
        from_attributes = True


class TeacherListResponse(BaseModel):
    id: int
    person: Optional[PersonInfo] = None
    organization: Optional[OrganizationInfo] = None
    position: Optional[DictionaryInfo] = None
    staff_type: Optional[DictionaryInfo] = None
    contract_type: Optional[DictionaryInfo] = None
    teaching: Optional[int] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class TeacherStatsResponse(BaseModel):
    total_teachers: int
    active_teachers: int
    teaching_count: int
    organizations_count: int


class FilterOptionsResponse(BaseModel):
    organizations: List[OrganizationInfo]
    positions: List[DictionaryInfo]
    staff_types: List[DictionaryInfo]
    contract_types: List[DictionaryInfo]


class PaginatedTeachersResponse(BaseModel):
    count: int
    total_pages: int
    current_page: int
    per_page: int
    results: List[TeacherListResponse]


@router.get("/", response_model=PaginatedTeachersResponse)
async def get_teachers(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    organization_id: Optional[int] = Query(None),
    position_id: Optional[int] = Query(None),
    teaching: Optional[bool] = Query(None),
    active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of teachers with filtering
    """
    try:
        # Base query with joins
        query = db.query(Teacher).join(
            Person, Teacher.person_id == Person.id
        ).join(
            User, Teacher.user_id == User.id
        ).outerjoin(
            Account, User.account_id == Account.id
        ).outerjoin(
            Organization, Teacher.organization_id == Organization.id
        )

        # Apply search filter
        if search:
            search_filter = or_(
                Person.firstname.ilike(f"%{search}%"),
                Person.lastname.ilike(f"%{search}%"),
                Person.pincode.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        # Apply filters
        if organization_id:
            query = query.filter(Teacher.organization_id == organization_id)
        
        if position_id:
            query = query.filter(Teacher.position_id == position_id)
        
        if teaching is not None:
            teaching_value = 1 if teaching else 0
            query = query.filter(Teacher.teaching == teaching_value)
        
        if active is not None:
            active_value = 1 if active else 0
            query = query.filter(User.active == active_value)

        # Count total records
        total_count = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        teachers = query.order_by(Person.lastname, Person.firstname).offset(offset).limit(per_page).all()

        # Build response data
        results = []
        for teacher in teachers:
            # Get related data
            person = db.query(Person).filter(Person.id == teacher.person_id).first()
            user = db.query(User).filter(User.id == teacher.user_id).first()
            organization = db.query(Organization).filter(Organization.id == teacher.organization_id).first() if teacher.organization_id else None
            position = db.query(Dictionary).filter(Dictionary.id == teacher.position_id).first() if teacher.position_id else None
            staff_type = db.query(Dictionary).filter(Dictionary.id == teacher.staff_type_id).first() if teacher.staff_type_id else None
            contract_type = db.query(Dictionary).filter(Dictionary.id == teacher.contract_type_id).first() if teacher.contract_type_id else None

            teacher_data = TeacherListResponse(
                id=teacher.id,
                person=PersonInfo(
                    id=person.id,
                    firstname=person.firstname,
                    lastname=person.lastname,
                    patronymic=person.patronymic,
                    pincode=person.pincode,
                    birthdate=person.birthdate
                ) if person else None,
                organization=OrganizationInfo(
                    id=organization.id,
                    name=getattr(organization, 'name', str(organization.id))
                ) if organization else None,
                position=DictionaryInfo(
                    id=position.id,
                    name_en=position.name_en,
                    name_az=position.name_az,
                    code=position.code
                ) if position else None,
                staff_type=DictionaryInfo(
                    id=staff_type.id,
                    name_en=staff_type.name_en,
                    name_az=staff_type.name_az,
                    code=staff_type.code
                ) if staff_type else None,
                contract_type=DictionaryInfo(
                    id=contract_type.id,
                    name_en=contract_type.name_en,
                    name_az=contract_type.name_az,
                    code=contract_type.code
                ) if contract_type else None,
                teaching=teacher.teaching,
                is_active=bool(user.active) if user else None
            )
            results.append(teacher_data)

        total_pages = (total_count + per_page - 1) // per_page

        return PaginatedTeachersResponse(
            count=total_count,
            total_pages=total_pages,
            current_page=page,
            per_page=per_page,
            results=results
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve teachers: {str(e)}")


@router.get("/stats", response_model=TeacherStatsResponse)
async def get_teacher_stats(db: Session = Depends(get_db)):
    """
    Get teacher statistics
    """
    try:
        total_teachers = db.query(Teacher).count()
        active_teachers = db.query(Teacher).join(User, Teacher.user_id == User.id).filter(User.active == 1).count()
        teaching_count = db.query(Teacher).filter(Teacher.teaching == 1).count()
        organizations_count = db.query(func.count(distinct(Teacher.organization_id))).scalar()

        return TeacherStatsResponse(
            total_teachers=total_teachers,
            active_teachers=active_teachers,
            teaching_count=teaching_count,
            organizations_count=organizations_count
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve teacher statistics: {str(e)}")


@router.get("/filter-options", response_model=FilterOptionsResponse)
async def get_filter_options(db: Session = Depends(get_db)):
    """
    Get available filter options for teachers
    """
    try:
        # Get organizations that have teachers
        org_ids = db.query(distinct(Teacher.organization_id)).filter(Teacher.organization_id.isnot(None)).all()
        org_ids = [org_id[0] for org_id in org_ids]
        organizations = db.query(Organization).filter(Organization.id.in_(org_ids)).all()

        # Get positions from dictionaries that are used by teachers
        pos_ids = db.query(distinct(Teacher.position_id)).filter(Teacher.position_id.isnot(None)).all()
        pos_ids = [pos_id[0] for pos_id in pos_ids]
        positions = db.query(Dictionary).filter(Dictionary.id.in_(pos_ids)).all()

        # Get staff types from dictionaries that are used by teachers
        staff_ids = db.query(distinct(Teacher.staff_type_id)).filter(Teacher.staff_type_id.isnot(None)).all()
        staff_ids = [staff_id[0] for staff_id in staff_ids]
        staff_types = db.query(Dictionary).filter(Dictionary.id.in_(staff_ids)).all()

        # Get contract types from dictionaries that are used by teachers
        contract_ids = db.query(distinct(Teacher.contract_type_id)).filter(Teacher.contract_type_id.isnot(None)).all()
        contract_ids = [contract_id[0] for contract_id in contract_ids]
        contract_types = db.query(Dictionary).filter(Dictionary.id.in_(contract_ids)).all()

        return FilterOptionsResponse(
            organizations=[
                OrganizationInfo(
                    id=org.id,
                    name=getattr(org, 'name', str(org.id))
                ) for org in organizations
            ],
            positions=[
                DictionaryInfo(
                    id=pos.id,
                    name_en=pos.name_en,
                    name_az=pos.name_az,
                    code=pos.code
                ) for pos in positions
            ],
            staff_types=[
                DictionaryInfo(
                    id=st.id,
                    name_en=st.name_en,
                    name_az=st.name_az,
                    code=st.code
                ) for st in staff_types
            ],
            contract_types=[
                DictionaryInfo(
                    id=ct.id,
                    name_en=ct.name_en,
                    name_az=ct.name_az,
                    code=ct.code
                ) for ct in contract_types
            ]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve filter options: {str(e)}")


@router.get("/{teacher_id}", response_model=TeacherListResponse)
async def get_teacher_detail(teacher_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information for a specific teacher
    """
    try:
        teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
        
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")

        # Get related data
        person = db.query(Person).filter(Person.id == teacher.person_id).first()
        user = db.query(User).filter(User.id == teacher.user_id).first()
        organization = db.query(Organization).filter(Organization.id == teacher.organization_id).first() if teacher.organization_id else None
        position = db.query(Dictionary).filter(Dictionary.id == teacher.position_id).first() if teacher.position_id else None
        staff_type = db.query(Dictionary).filter(Dictionary.id == teacher.staff_type_id).first() if teacher.staff_type_id else None
        contract_type = db.query(Dictionary).filter(Dictionary.id == teacher.contract_type_id).first() if teacher.contract_type_id else None

        return TeacherListResponse(
            id=teacher.id,
            person=PersonInfo(
                id=person.id,
                firstname=person.firstname,
                lastname=person.lastname,
                patronymic=person.patronymic,
                pincode=person.pincode,
                birthdate=person.birthdate
            ) if person else None,
            organization=OrganizationInfo(
                id=organization.id,
                name=getattr(organization, 'name', str(organization.id))
            ) if organization else None,
            position=DictionaryInfo(
                id=position.id,
                name_en=position.name_en,
                name_az=position.name_az,
                code=position.code
            ) if position else None,
            staff_type=DictionaryInfo(
                id=staff_type.id,
                name_en=staff_type.name_en,
                name_az=staff_type.name_az,
                code=staff_type.code
            ) if staff_type else None,
            contract_type=DictionaryInfo(
                id=contract_type.id,
                name_en=contract_type.name_en,
                name_az=contract_type.name_az,
                code=contract_type.code
            ) if contract_type else None,
            teaching=teacher.teaching,
            is_active=bool(user.active) if user else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve teacher: {str(e)}")
