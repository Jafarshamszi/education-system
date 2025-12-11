"""
Organization schemas for API responses
"""

from typing import List, Optional
from pydantic import BaseModel


class OrganizationBase(BaseModel):
    """Base organization schema"""
    id: int
    name: Optional[str] = None
    type_id: Optional[int] = None
    type_name: Optional[str] = None
    parent_id: Optional[int] = None
    nod_level: Optional[int] = None
    active: Optional[int] = None


class OrganizationWithChildren(OrganizationBase):
    """Organization schema with children for tree structure"""
    children: List['OrganizationWithChildren'] = []
    has_children: bool = False
    
    class Config:
        from_attributes = True


class OrganizationHierarchy(BaseModel):
    """Organization hierarchy response"""
    organizations: List[OrganizationWithChildren]
    total_count: int
    
    class Config:
        from_attributes = True


class OrganizationDetail(OrganizationBase):
    """Detailed organization information"""
    formula: Optional[str] = None
    logo_name: Optional[int] = None
    create_date: Optional[str] = None
    update_date: Optional[str] = None
    parent_name: Optional[str] = None
    children_count: int = 0
    
    class Config:
        from_attributes = True


# Enable forward references
OrganizationWithChildren.model_rebuild()