"""
Authentication utilities for the education system
"""

from .jwt_handler import create_access_token, verify_token
from .password import hash_password, verify_password, verify_legacy_password
from .dependencies import (
    get_current_user, 
    require_roles, 
    CurrentUser, 
    require_admin,
    require_teacher_or_admin
)

__all__ = [
    "create_access_token",
    "verify_token", 
    "hash_password",
    "verify_password",
    "verify_legacy_password",
    "get_current_user",
    "require_roles",
    "CurrentUser",
    "require_admin",
    "require_teacher_or_admin"
]