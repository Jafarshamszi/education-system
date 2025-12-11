"""
Pydantic schemas for the education system
"""

from .auth import LoginRequest, LoginResponse, UserProfile, TokenPayload

__all__ = [
    "LoginRequest",
    "LoginResponse", 
    "UserProfile",
    "TokenPayload"
]