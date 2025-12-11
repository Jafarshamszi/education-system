from typing import AsyncGenerator
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager
    """
    # Startup
    print("🚀 Starting Education Management System API...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🔗 Database: {settings.database_url}")
    
    try:
        yield
    except Exception as e:
        print(f"❌ Error during lifespan: {e}")
        raise
    
    # Shutdown
    print("🛑 Shutting down Education Management System API...")

def create_application() -> FastAPI:
    """
    Create and configure FastAPI application
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="A comprehensive education management system API",
        version=settings.VERSION,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # Set all CORS enabled origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:3003",
            "http://localhost:3004",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
            "http://127.0.0.1:3003",
            "http://127.0.0.1:3004",
            "https://localhost:3000",
            "https://localhost:3001",
            "https://localhost:3002",
            "https://localhost:3003",
            "https://localhost:3004"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"]
    )

    # Security middleware
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    # Simple health check endpoint (no external dependencies)
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }

    # Add only the requests router for testing
    try:
        from app.api.requests import router as requests_router
        app.include_router(requests_router, prefix=f"{settings.API_PREFIX}/requests", tags=["requests"])
        print("✅ Requests router included successfully")
    except Exception as e:
        print(f"❌ Error including requests router: {e}")

    return app

app = create_application()