"""
API router for the education system
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .students import router as students_router
from .teachers import router as teachers_router  # Updated to use new schema
from .organization import router as organization_router
from .requests import router as requests_router
from .academic_schedule import router as academic_schedule_router
from .evaluation_system import router as evaluation_system_router
from .student_orders import router as student_orders_router
from .students_comprehensive import router as students_comprehensive_router
from .education_plan import router as education_plan_router
from .student_groups import router as student_groups_router
from .curriculum_simplified import router as curriculum_router
from .class_schedule import router as class_schedule_router
from .dashboard import router as dashboard_router
from .user_preferences import router as user_preferences_router

# Create main API router
api_router = APIRouter()

# Include all routes
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(students_router)
api_router.include_router(teachers_router)  # Using updated teachers router
api_router.include_router(organization_router)
api_router.include_router(
    requests_router, prefix="/requests", tags=["requests"]
)
api_router.include_router(
    academic_schedule_router, tags=["academic-schedule"]
)
api_router.include_router(
    evaluation_system_router, tags=["evaluation-system"]
)
api_router.include_router(
    student_orders_router, prefix="/student-orders", tags=["student-orders"]
)
api_router.include_router(
    students_comprehensive_router, prefix="/students-comprehensive",
    tags=["students-comprehensive"]
)
api_router.include_router(
    education_plan_router, prefix="/education-plans", tags=["education-plans"]
)
api_router.include_router(
    student_groups_router, prefix="/student-groups", tags=["student-groups"]
)
api_router.include_router(
    curriculum_router, prefix="/curriculum", tags=["curriculum"]
)
api_router.include_router(
    class_schedule_router, tags=["class-schedule"]
)
api_router.include_router(
    dashboard_router, tags=["dashboard"]
)
api_router.include_router(
    user_preferences_router, tags=["user-preferences"]
)


@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Education System API is running"}
