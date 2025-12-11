from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, students, teachers, accounts, courses

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(teachers.router, prefix="/teachers", tags=["teachers"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])