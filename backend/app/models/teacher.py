"""
Teacher model for the education system
"""

from sqlalchemy import BigInteger, Text, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, ActiveMixin


class Teacher(Base, TimestampMixin, ActiveMixin):
    """Teacher model mapped to teachers table"""
    
    __tablename__ = "teachers"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    
    # Foreign keys
    person_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    organization_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    
    # Action information
    in_action_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    in_action_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    out_action_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    out_action_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Position information
    staff_type_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    position_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    contract_type_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    
    # Teacher properties
    teaching: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    card_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Teacher(id={self.id}, person_id={self.person_id})>"