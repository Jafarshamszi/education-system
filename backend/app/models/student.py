"""
Student model for the education system
"""

from sqlalchemy import BigInteger, Text, SmallInteger
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
import uuid

from .base import Base, TimestampMixin, ActiveMixin


class Student(Base, TimestampMixin, ActiveMixin):
    """Student model mapped to students table"""
    
    __tablename__ = "students"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Foreign keys
    person_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    org_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    
    # Order information
    in_order_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    yda_order_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    out_order_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    order_type_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    
    # Education information
    education_line_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    education_type_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    education_payment_type_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    education_lang_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    
    # Student properties
    score: Mapped[str | None] = mapped_column(Text, nullable=True)
    card_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    yearly_payment: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_count: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Student(id={self.id}, person_id={self.person_id})>"
