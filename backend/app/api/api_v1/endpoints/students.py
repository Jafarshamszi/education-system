from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

router = APIRouter()


@router.get("/")
async def get_students(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get all students with pagination
    """
    return {"message": "Get students endpoint - To be implemented"}


@router.get("/{student_id}")
async def get_student(
    student_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get student by ID
    """
    return {"message": f"Get student {student_id} - To be implemented"}


@router.post("/")
async def create_student(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Create new student
    """
    return {"message": "Create student endpoint - To be implemented"}


@router.put("/{student_id}")
async def update_student(
    student_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update student by ID
    """
    return {"message": f"Update student {student_id} - To be implemented"}


@router.delete("/{student_id}")
async def delete_student(
    student_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Delete student by ID
    """
    return {"message": f"Delete student {student_id} - To be implemented"}