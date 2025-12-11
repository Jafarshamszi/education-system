from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

router = APIRouter()


@router.get("/")
async def get_courses(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get all courses with pagination
    """
    return {"message": "Get courses endpoint - To be implemented"}


@router.get("/{course_id}")
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get course by ID
    """
    return {"message": f"Get course {course_id} - To be implemented"}