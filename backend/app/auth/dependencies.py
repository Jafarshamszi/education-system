"""
Authentication dependencies and role-based access control
"""

from functools import wraps
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models import User, Person
from .jwt_handler import verify_token

# Security scheme
security = HTTPBearer(auto_error=False)


class CurrentUser:
    """
    Current authenticated user information
    """
    def __init__(
        self,
        user: User,
        person: Optional[Person] = None,
        user_type: str = "UNKNOWN"
    ):
        self.user = user
        self.person = person
        self._user_type = user_type
        
    @property
    def id(self) -> UUID:
        return self.user.id
        
    @property 
    def user_type(self) -> str:
        return self._user_type
        
    @property
    def username(self) -> str:
        return self.user.username or ""
        
    @property
    def email(self) -> str:
        return self.user.email or ""
        
    @property
    def full_name(self) -> str:
        if self.person:
            return f"{self.person.first_name} {self.person.last_name}".strip()
        return self.username
        
    def has_role(self, required_role: str) -> bool:
        """Check if user has a specific role"""
        return self.user_type == required_role
        
    def has_any_role(self, required_roles: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        return self.user_type in required_roles


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Get the current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        CurrentUser object with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    try:
        # Verify token and extract payload
        payload = verify_token(credentials.credentials)
        user_id_str = payload.get("sub")
        
        if user_id_str is None:
            raise credentials_exception
            
        # Convert string UUID to UUID object
        try:
            user_id = UUID(user_id_str)
        except (ValueError, AttributeError):
            raise credentials_exception
            
        # Get user from database
        user = db.get(User, user_id)
        if user is None:
            raise credentials_exception
            
        # Get person information if available
        person = None
        stmt = select(Person).where(Person.user_id == user_id)
        result = db.execute(stmt)
        person = result.scalar_one_or_none()
            
        # Determine user type
        user_type = "UNKNOWN"
        
        # Check metadata first
        if user.user_metadata and isinstance(user.user_metadata, dict):
            metadata_role = user.user_metadata.get('role')
            if metadata_role in ['SYSADMIN', 'ADMIN', 'TEACHER', 'STUDENT']:
                user_type = metadata_role
        
        if user_type == "UNKNOWN":
            # Check Student
            from app.models import Student
            student_check = db.execute(
                select(Student.id).where(Student.user_id == user_id).limit(1)
            ).scalar_one_or_none()
            
            if student_check:
                user_type = "STUDENT"
            else:
                # Check Staff
                from app.models.staff_member import StaffMember
                staff_record = db.execute(
                    select(StaffMember.administrative_role)
                    .where(StaffMember.user_id == user_id)
                    .limit(1)
                ).fetchone()
                
                if staff_record:
                    admin_role = staff_record.administrative_role
                    if admin_role and admin_role in [
                        'rector', 'vice_rector', 'dean', 'vice_dean',
                        'head_of_department'
                    ]:
                        user_type = "ADMIN"
                    else:
                        user_type = "TEACHER"

        return CurrentUser(user=user, person=person, user_type=user_type)
        
    except Exception:
        raise credentials_exception


def require_roles(*required_roles: str):
    """
    Decorator to require specific user roles for endpoint access
    
    Args:
        required_roles: List of required user roles
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
                
            if not current_user.has_any_role(list(required_roles)):
                roles_str = ', '.join(required_roles)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {roles_str}"
                )
            
            # Check if function is async
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin():
    """Decorator to require admin access"""
    return require_roles("ADMIN", "SYSADMIN", "OWNER")


def require_teacher_or_admin():
    """Decorator to require teacher or admin access"""
    return require_roles("TEACHER", "ADMIN", "SYSADMIN", "OWNER")


def require_authenticated_user():
    """Decorator to require any authenticated user"""
    return require_roles(
        "STUDENT", "TEACHER", "ADMIN", "SYSADMIN", "OWNER", "TYUTOR"
    )
