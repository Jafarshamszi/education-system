from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

router = APIRouter()


@router.get("/")
async def get_teachers(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get all teachers with pagination
    """
    return {"message": "Get teachers endpoint - To be implemented"}


@router.get("/{teacher_id}")
async def get_teacher(
    teacher_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get teacher by ID
    """
    return {"message": f"Get teacher {teacher_id} - To be implemented"}


@router.post("/")
async def create_teacher(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Create new teacher
    """
    return {"message": "Create teacher endpoint - To be implemented"}


@router.put("/{teacher_id}")
async def update_teacher(
    teacher_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update teacher by ID
    """
    return {"message": f"Update teacher {teacher_id} - To be implemented"}