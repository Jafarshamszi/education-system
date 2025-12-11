"""
Dictionary model for the education system
"""

from sqlalchemy import BigInteger, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, ActiveMixin


class Dictionary(Base, TimestampMixin, ActiveMixin):
    """Dictionary model mapped to dictionaries table"""
    
    __tablename__ = "dictionaries"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    
    # Foreign keys
    type_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    
    # Dictionary properties
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name_az: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_name_az: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_name_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_name_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Dictionary(id={self.id}, name_az={self.name_az})>"