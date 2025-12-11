from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

router = APIRouter()
security = HTTPBearer()


@router.post("/login")
async def login(
    db: AsyncSession = Depends(get_async_session)
):
    """
    User login endpoint
    """
    return {"message": "Login endpoint - To be implemented"}


@router.post("/register")
async def register(
    db: AsyncSession = Depends(get_async_session)
):
    """
    User registration endpoint
    """
    return {"message": "Register endpoint - To be implemented"}


@router.post("/refresh")
async def refresh_token(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Refresh access token
    """
    return {"message": "Refresh token endpoint - To be implemented"}


@router.post("/logout")
async def logout():
    """
    User logout endpoint
    """
    return {"message": "Logout successful"}