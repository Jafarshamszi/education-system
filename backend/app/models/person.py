"""
Person model for the education system - Updated for LMS database
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Text, Date, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Person(Base):
    """Person model mapped to persons table in lms database"""
    
    __tablename__ = "persons"
    
    # Primary key - UUID in new structure
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    # Foreign key to user
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        unique=True
    )
    
    # Personal information - English
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Personal information - Azerbaijani
    first_name_az: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_name_az: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Personal information - Russian
    first_name_ru: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_name_ru: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Personal details
    date_of_birth: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    gender: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Identification
    national_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    passport_number: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # Contact information
    phone_primary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone_secondary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # Address and emergency contact (JSONB)
    address: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    emergency_contact: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )
    
    # Photo
    photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP")
    )
    
    @property
    def full_name(self) -> str:
        """Get full name combining first, last, and middle names"""
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(part for part in parts if part)
    
    def __repr__(self) -> str:
        return f"<Person(id={self.id}, name={self.full_name})>"
