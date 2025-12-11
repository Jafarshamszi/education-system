"""
User model for the education system - Updated for LMS database
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from sqlalchemy import Boolean, Integer, DateTime, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserType(str, Enum):
    """User types enumeration"""
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ADMIN = "ADMIN"
    SYSADMIN = "SYSADMIN"
    OWNER = "OWNER"
    TYUTOR = "TYUTOR"


class User(Base):
    """User model mapped to users table in lms database"""
    
    __tablename__ = "users"
    
    # Primary key - UUID in new structure
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    # Authentication fields
    username: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    
    # MFA fields
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status fields
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP")
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # User metadata (custom field) - using 'user_metadata' to avoid conflict
    user_metadata: Mapped[dict] = mapped_column(
        "metadata",  # Map to database column 'metadata'
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb")
    )
    
    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, username={self.username}, "
            f"email={self.email})>"
        )
