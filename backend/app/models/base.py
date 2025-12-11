"""
Base model class for all database models
"""

from datetime import datetime

from sqlalchemy import DateTime, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class TimestampMixin:
    """Mixin for models with create/update timestamps"""
    
    create_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    create_user_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    update_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    update_user_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )


class ActiveMixin:
    """Mixin for models with active status"""
    
    active: Mapped[int | None] = mapped_column(nullable=True, default=1)