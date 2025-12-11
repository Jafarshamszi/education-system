"""
StaffMember model for the education system - New LMS Schema
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import Text, Date, DateTime, Boolean, ForeignKey, ARRAY, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class StaffMember(Base):
    """Staff member model mapped to staff_members table"""

    __tablename__ = "staff_members"

    # Primary key - UUID
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    # Foreign keys
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )

    organization_unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organization_units.id"),
        nullable=True
    )

    # Employee information
    employee_number: Mapped[str] = mapped_column(Text, nullable=False)

    # Position information (JSONB for multilingual support)
    position_title: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Employment details
    employment_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    contract_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Academic information
    academic_rank: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    administrative_role: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Office and contact
    office_location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    office_hours: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Research and qualifications
    research_interests: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text), nullable=True
    )
    qualifications: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Status
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

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
    def position_title_en(self) -> Optional[str]:
        """Get position title in English"""
        if self.position_title and isinstance(self.position_title, dict):
            return self.position_title.get('en')
        return None

    @property
    def position_title_az(self) -> Optional[str]:
        """Get position title in Azerbaijani"""
        if self.position_title and isinstance(self.position_title, dict):
            return self.position_title.get('az')
        return None

    def __repr__(self) -> str:
        return f"<StaffMember(id={self.id}, employee_number={self.employee_number})>"
