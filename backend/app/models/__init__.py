"""
Database models for the Education System

This package contains all SQLAlchemy models mapped to the LMS PostgreSQL
database schema.
"""

from .base import Base
from .user import User, UserType
from .person import Person
from .organization import Organization
from .user_group import UserGroup
from .student import Student
from .teacher import Teacher
from .account import Account

__all__ = [
    "Base",
    "User",
    "UserType",
    "Person",
    "Organization",
    "UserGroup",
    "Student",
    "Teacher",
    "Account"
]
