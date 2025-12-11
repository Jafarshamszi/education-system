"""
User management API endpoints - Updated for LMS database
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, CurrentUser
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def get_users(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get list of users (Admin only)"""
    if (not current_user.has_role("ADMIN") and
            not current_user.has_role("SYSADMIN")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    users = db.query(User).limit(100).all()
    return users


@router.get("/me")
def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "user_type": current_user.user_type
    }
