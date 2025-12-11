"""
OrganizationUnit model for the education system - New LMS Schema
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import Text, DateTime, ForeignKey, text, Boolean, ARRAY, Date
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class OrganizationUnit(Base):
    """Organization unit model mapped to organization_units table"""

    __tablename__ = "organization_units"

    # Primary key - UUID
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    # Parent organization unit (for hierarchy)
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organization_units.id"),
        nullable=True
    )

    # Organization unit type (e.g., 'department', 'faculty', 'university')
    type: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Code for the organization unit
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    # Name (JSONB for multilingual support)
    name: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Description (JSONB for multilingual support)
    description: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Established date
    established_date: Mapped[Optional[datetime]] = mapped_column(
        Date,
        nullable=True
    )

    # Head of unit
    head_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )

    # Deputy user IDs (array)
    deputy_user_ids: Mapped[Optional[List[UUID]]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)),
        nullable=True
    )

    # Contact info (JSONB)
    contact_info: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )

    # Settings (JSONB)
    settings: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )

    # Status
    is_active: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, default=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )
    
    @property
    def name_en(self) -> Optional[str]:
        """Get name in English"""
        if self.name and isinstance(self.name, dict):
            return self.name.get('en')
        return None
    
    @property
    def name_az(self) -> Optional[str]:
        """Get name in Azerbaijani"""
        if self.name and isinstance(self.name, dict):
            return self.name.get('az')
        return None

    def __repr__(self) -> str:
        if self.name:
            name_display = (
                self.name_en or self.name_az or str(self.name)
            )
        else:
            name_display = "N/A"
        return f"<OrganizationUnit(id={self.id}, name={name_display})>"
