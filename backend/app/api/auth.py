"""
Authentication API endpoints
"""

from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import User, Person
from app.schemas.auth import LoginRequest, LoginResponse, UserProfile, UserProfileDetailed, UserProfileUpdate
from app.auth import (
    create_access_token,
    get_current_user,
    CurrentUser,
    verify_password,
    hash_password
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """
    Authenticate user and return access token
    
    Supports username authentication.
    
    Args:
        login_data: Login credentials (username + password)
        db: Database session
        
    Returns:
        Login response with access token and user information
        
    Raises:
        HTTPException: If authentication fails
    """
    
    # Find user by username (case-insensitive)
    stmt = select(User).where(User.username == login_data.username)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password using bcrypt hashing
    # Check if password is hashed (bcrypt hashes start with $2b$ or $2a$)
    if user.password_hash.startswith('$2'):
        # Password is hashed, use verify_password
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
    else:
        # Legacy plain text password - verify and upgrade to hash
        # Truncate stored password to 72 bytes for comparison (bcrypt limit)
        stored_password = user.password_hash
        if len(stored_password.encode('utf-8')) > 72:
            stored_password = stored_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')

        if stored_password != login_data.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        # Upgrade password to hash for security
        password_to_hash = login_data.password
        if len(password_to_hash.encode('utf-8')) > 72:
            password_to_hash = password_to_hash.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        user.password_hash = hash_password(password_to_hash)
        db.commit()
    
    # Check if user is active and not locked
    if not user.is_active or user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled or locked"
        )
    
    # Get person information for full name
    person = None
    if user.id:
        stmt = select(Person).where(Person.user_id == user.id)
        result = db.execute(stmt)
        person = result.scalar_one_or_none()
    
    # Determine user type by checking students and staff_members tables
    user_type = "UNKNOWN"
    full_name = None
    
    if person:
        full_name = f"{person.first_name} {person.last_name}".strip()
    
    # First check if role is defined in user metadata (for SYSADMIN and special roles)
    if user.user_metadata and isinstance(user.user_metadata, dict):
        metadata_role = user.user_metadata.get('role')
        if metadata_role in ['SYSADMIN', 'ADMIN', 'TEACHER', 'STUDENT']:
            user_type = metadata_role
    
    # If not in metadata, check database tables
    if user_type == "UNKNOWN":
        # Check if user is a student
        from app.models import Student
        student_check = db.execute(
            select(Student.id).where(Student.user_id == user.id).limit(1)
        ).scalar_one_or_none()
        
        if student_check:
            user_type = "STUDENT"
        else:
            # Check if user is staff/teacher
            from app.models.staff_member import StaffMember
            staff_check = db.execute(
                select(
                    StaffMember.id,
                    StaffMember.academic_rank,
                    StaffMember.administrative_role
                )
                .where(StaffMember.user_id == user.id)
                .limit(1)
            ).fetchone()
            
            if staff_check:
                # Determine if TEACHER or ADMIN based on role
                admin_role = staff_check.administrative_role
                
                # If has administrative role, classify as ADMIN
                if admin_role and admin_role in [
                    'rector', 'vice_rector', 'dean', 'vice_dean',
                    'head_of_department'
                ]:
                    user_type = "ADMIN"
                else:
                    # All staff members are teachers by default
                    user_type = "TEACHER"
    
    # Validate user type against frontend type (role-based access control)
    if login_data.frontend_type:
        allowed_access = {
            "student": ["STUDENT"],
            "teacher": ["TEACHER", "ADMIN", "SYSADMIN"],
            "admin": ["ADMIN", "SYSADMIN"]
        }
        
        allowed_types = allowed_access.get(login_data.frontend_type, [])
        if user_type not in allowed_types:
            # Create user-friendly error messages
            error_messages = {
                ("STUDENT", "teacher"): (
                    "Students cannot access the teacher portal. "
                    "Please use the student portal to login."
                ),
                ("STUDENT", "admin"): (
                    "Students cannot access the admin portal. "
                    "Please use the student portal to login."
                ),
                ("TEACHER", "student"): (
                    "Teachers cannot access the student portal. "
                    "Please use the teacher portal to login."
                ),
                ("ADMIN", "student"): (
                    "Administrators cannot access the student portal. "
                    "Please use the admin portal to login."
                )
            }
            
            error_key = (user_type, login_data.frontend_type)
            error_message = error_messages.get(
                error_key,
                f"Access denied. {user_type}s cannot login "
                f"through the {login_data.frontend_type} portal."
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
        
    # Create access token
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    token_data = {
        "sub": str(user.id),
        "user_type": user_type,
        "username": user.username,
    }
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        username=user.username,
        user_type=user_type,
        full_name=full_name,
        email=user.email
    )


@router.get("/me", response_model=UserProfile)
def get_current_user_profile(
    current_user: CurrentUser = Depends(get_current_user)
) -> UserProfile:
    """
    Get current user profile information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile information
    """
    return UserProfile(
        id=str(current_user.id),
        username=current_user.username,
        user_type=current_user.user_type,
        email=current_user.email,
        full_name=current_user.full_name,
        organization_id=None,  # To be updated based on lms structure
        is_active=current_user.user.is_active
    )


@router.post("/refresh")
def refresh_token(
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Refresh the access token for current user

    Args:
        current_user: Current authenticated user

    Returns:
        New access token
    """
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    token_data = {
        "sub": str(current_user.id),
        "user_type": current_user.user_type,
        "username": current_user.username,
    }
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/user/", response_model=UserProfileDetailed)
def get_user_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserProfileDetailed:
    """
    Get detailed user profile with separated name fields

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Detailed user profile information
    """
    # Get person information
    stmt = select(Person).where(Person.user_id == current_user.user.id)
    result = db.execute(stmt)
    person = result.scalar_one_or_none()

    # Determine role from user_type
    role = current_user.user_type.lower() if current_user.user_type != "UNKNOWN" else "user"

    return UserProfileDetailed(
        id=int(str(current_user.user.id).replace('-', '')[:9], 16),  # Convert UUID to int for frontend
        username=current_user.user.username,
        email=current_user.user.email or "",
        first_name=person.first_name if person else "",
        last_name=person.last_name if person else "",
        role=role,
        is_active=current_user.user.is_active,
        created_at=current_user.user.created_at.isoformat() if current_user.user.created_at else "",
        updated_at=current_user.user.updated_at.isoformat() if current_user.user.updated_at else ""
    )


@router.put("/user/", response_model=UserProfileDetailed)
def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserProfileDetailed:
    """
    Update user profile information

    Args:
        profile_update: Updated profile data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user profile
    """
    # Update user email if provided
    if profile_update.email is not None:
        current_user.user.email = profile_update.email

    # Get or create person record
    stmt = select(Person).where(Person.user_id == current_user.user.id)
    result = db.execute(stmt)
    person = result.scalar_one_or_none()

    if not person:
        # Create new person record if it doesn't exist
        person = Person(
            user_id=current_user.user.id,
            first_name=profile_update.first_name or "",
            last_name=profile_update.last_name or ""
        )
        db.add(person)
    else:
        # Update existing person record
        if profile_update.first_name is not None:
            person.first_name = profile_update.first_name
        if profile_update.last_name is not None:
            person.last_name = profile_update.last_name

    db.commit()
    db.refresh(current_user.user)
    if person:
        db.refresh(person)

    # Determine role from user_type
    role = current_user.user_type.lower() if current_user.user_type != "UNKNOWN" else "user"

    return UserProfileDetailed(
        id=int(str(current_user.user.id).replace('-', '')[:9], 16),
        username=current_user.user.username,
        email=current_user.user.email or "",
        first_name=person.first_name if person else "",
        last_name=person.last_name if person else "",
        role=role,
        is_active=current_user.user.is_active,
        created_at=current_user.user.created_at.isoformat() if current_user.user.created_at else "",
        updated_at=current_user.user.updated_at.isoformat() if current_user.user.updated_at else ""
    )
