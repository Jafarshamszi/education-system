from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# For now, we'll use sync database operations since asyncpg doesn't work with Python 3.13
# We can add async support later when asyncpg is compatible

# Sync engine for all operations
sync_engine = create_engine(
    settings.database_url,
    echo=settings.DEBUG
)

# Sync session maker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# Dependency to get database session
def get_db():
    """Get database session for sync operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# For async operations when needed (will implement later)
async def get_async_session():
    """Placeholder for async session - not implemented yet."""
    raise NotImplementedError("Async sessions not available with current setup")