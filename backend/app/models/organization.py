"""
Organization model for the education system
"""

from sqlalchemy import BigInteger, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, ActiveMixin


class Organization(Base, TimestampMixin, ActiveMixin):
    """Organization model mapped to organizations table"""
    
    __tablename__ = "organizations"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    
    # Foreign keys
    type_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    dictionary_name_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    
    # Organization properties
    formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    nod_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    logo_name: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, level={self.nod_level})>"