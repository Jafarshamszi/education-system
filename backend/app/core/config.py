from typing import List, Union, Any
import json
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields from .env file
    )
    
    # Application
    PROJECT_NAME: str = "Education Management System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "1111"
    DB_NAME: str = "lms"
    
    @property
    def database_url(self) -> str:
        """Get the database URL for SQLAlchemy (sync version for Alembic)."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property 
    def async_database_url(self) -> str:
        """Get the async database URL for SQLAlchemy."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    JWT_SECRET_KEY: str = "your-jwt-secret-key-here-in-production-use-a-real-secret"
    JWT_ALGORITHM: str = "HS256"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS - Can be set via environment variable as comma-separated list
    BACKEND_CORS_ORIGINS: Union[List[str], str] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            # Handle both comma-separated and JSON array formats
            v = v.strip()
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        raise ValueError(f"Cannot parse CORS origins: {v}")
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security & Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


settings = Settings()
