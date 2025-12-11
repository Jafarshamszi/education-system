"""
Authentication-related Pydantic schemas - Updated for LMS database
"""

from typing import Optional, Literal
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Request schema for user login - username or email + password"""
    username: str  # Can be username or email
    password: str
    frontend_type: Optional[Literal["student", "teacher", "admin"]] = None


class LoginResponse(BaseModel):
    """Response schema for successful login"""
    access_token: str
    token_type: str = "bearer"
    user_id: str  # UUID as string
    username: str
    user_type: str
    full_name: Optional[str] = None
    email: Optional[str] = None


class UserProfile(BaseModel):
    """User profile information"""
    id: str  # UUID as string
    username: str
    user_type: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    organization_id: Optional[str] = None  # UUID as string
    is_active: bool = True

    class Config:
        from_attributes = True


class UserProfileDetailed(BaseModel):
    """Detailed user profile with separated name fields"""
    id: int  # Use int for frontend compatibility
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


class TokenPayload(BaseModel):
    """JWT token payload schema"""
    sub: str  # subject (user ID as UUID string)
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    user_type: str
    username: str
