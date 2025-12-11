"""
Organization API endpoints - Implementation using organization_units table
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.organization_unit import OrganizationUnit


router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrganizationWithChildren(BaseModel):
    id: str  # UUID as string
    code: str
    name: dict  # JSONB with {az, en, ru}
    name_localized: Optional[str] = None  # Localized name
    type: str  # university, faculty, department, etc.
    parent_id: Optional[str] = None  # UUID as string
    is_active: bool = True
    children: List['OrganizationWithChildren'] = []
    has_children: bool = False


def get_localized_value(jsonb_field: Optional[dict], lang: str = 'en') -> Optional[str]:
    """Get localized value from JSONB field with fallback"""
    if not jsonb_field:
        return None
    return jsonb_field.get(lang) or jsonb_field.get('en') or jsonb_field.get('az') or next(iter(jsonb_field.values()), None)


class OrganizationHierarchy(BaseModel):
    organizations: List[OrganizationWithChildren]
    total_count: int


class OrganizationDetail(BaseModel):
    id: str  # UUID as string
    code: str
    name: dict  # JSONB
    description: Optional[dict] = None  # JSONB
    type: str
    parent_id: Optional[str] = None
    head_user_id: Optional[str] = None
    deputy_user_ids: Optional[List[str]] = None
    established_date: Optional[str] = None
    contact_info: Optional[dict] = None
    settings: Optional[dict] = None
    is_active: bool = True
    children_count: int = 0


@router.get("/hierarchy", response_model=OrganizationHierarchy)
def get_organization_hierarchy(
    include_inactive: bool = Query(
        False, description="Include inactive"
    ),
    include_children: bool = Query(
        False, description="Include children"
    ),
    lang: str = Query('en', regex='^(en|ru|az)$'),
    db: Session = Depends(get_db)
):
    """
    Get complete organization hierarchy from organization_units table

    Args:
        lang: Language code for localized content (en, ru, az)
    """
    try:
        # Build query
        query = db.query(OrganizationUnit)
        
        if not include_inactive:
            query = query.filter(OrganizationUnit.is_active == True)
        
        # Get all organizations
        org_units = query.all()
        
        # Convert to response format
        def build_org_dict(org):
            name_dict = org.name or {"en": f"Organization {org.code}"}
            return {
                "id": str(org.id),
                "code": org.code,
                "name": name_dict,
                "name_localized": get_localized_value(name_dict, lang),
                "type": org.type,
                "parent_id": str(org.parent_id) if org.parent_id else None,
                "is_active": org.is_active if org.is_active is not None else True,
                "children": [],
                "has_children": False
            }
        
        org_list = [build_org_dict(org) for org in org_units]
        
        # Build hierarchy if requested
        if include_children:
            org_map = {org["id"]: org for org in org_list}
            root_orgs = []
            
            for org in org_list:
                if org["parent_id"] and org["parent_id"] in org_map:
                    parent = org_map[org["parent_id"]]
                    parent["children"].append(org)
                    parent["has_children"] = True
                else:
                    root_orgs.append(org)
            
            return OrganizationHierarchy(
                organizations=root_orgs,
                total_count=len(org_units)
            )
        else:
            # Flat list
            return OrganizationHierarchy(
                organizations=org_list,
                total_count=len(org_units)
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve organizations: {str(e)}"
        )


@router.get("/{organization_id}", response_model=OrganizationDetail)
def get_organization_detail(
    organization_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific organization unit
    """
    try:
        from uuid import UUID
        org_uuid = UUID(organization_id)
        
        org = db.query(OrganizationUnit).filter(
            OrganizationUnit.id == org_uuid
        ).first()
        
        if not org:
            raise HTTPException(
                status_code=404,
                detail="Organization not found"
            )
        
        # Count children
        children_count = db.query(OrganizationUnit).filter(
            OrganizationUnit.parent_id == org_uuid
        ).count()
        
        return OrganizationDetail(
            id=str(org.id),
            code=org.code,
            name=org.name or {"en": f"Organization {org.code}"},
            description=org.description,
            type=org.type,
            parent_id=str(org.parent_id) if org.parent_id else None,
            head_user_id=str(org.head_user_id) if org.head_user_id else None,
            deputy_user_ids=[str(uid) for uid in org.deputy_user_ids] if org.deputy_user_ids else None,
            established_date=str(org.established_date) if org.established_date else None,
            contact_info=org.contact_info,
            settings=org.settings,
            is_active=org.is_active if org.is_active is not None else True,
            children_count=children_count
        )
    
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid organization ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve organization: {str(e)}"
        )


@router.get(
    "/{organization_id}/children",
    response_model=List[OrganizationWithChildren]
)
def get_organization_children(
    organization_id: str,
    active_only: bool = Query(
        True, description="Return only active children"
    ),
    db: Session = Depends(get_db)
):
    """
    Get children of a specific organization unit
    """
    try:
        from uuid import UUID
        org_uuid = UUID(organization_id)
        
        # Build query
        query = db.query(OrganizationUnit).filter(
            OrganizationUnit.parent_id == org_uuid
        )
        
        if active_only:
            query = query.filter(OrganizationUnit.is_active.is_(True))
        
        children = query.all()
        
        return [
            OrganizationWithChildren(
                id=str(child.id),
                code=child.code,
                name=child.name or {"en": f"Organization {child.code}"},
                type=child.type,
                parent_id=str(child.parent_id) if child.parent_id else None,
                is_active=child.is_active if child.is_active is not None else True,
                children=[],
                has_children=False
            )
            for child in children
        ]
    
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid organization ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve children: {str(e)}"
        )
