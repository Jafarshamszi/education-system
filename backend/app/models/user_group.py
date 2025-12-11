"""
UserGroup model for the education system
"""

from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, ActiveMixin


class UserGroup(Base, TimestampMixin, ActiveMixin):
    """UserGroup model mapped to user_groups table"""
    
    __tablename__ = "user_groups"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    
    # Multilingual names
    name_az: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Hierarchy
    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Additional properties
    position_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    access_ip_list: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<UserGroup(id={self.id}, name_en={self.name_en})>"