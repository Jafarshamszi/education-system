"""
Account model for the education system
"""

from sqlalchemy import BigInteger, Text, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, ActiveMixin


class Account(Base, TimestampMixin, ActiveMixin):
    """Account model mapped to accounts table"""
    
    __tablename__ = "accounts"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    
    # Foreign keys
    person_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    lang_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    default_user_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    
    # Authentication properties
    username: Mapped[str | None] = mapped_column(Text, nullable=True)
    password: Mapped[str | None] = mapped_column(Text, nullable=True)
    other_username: Mapped[str | None] = mapped_column(Text, nullable=True)
    other_password: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # System properties
    in_system: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    auth_type: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    fail_login_count: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<Account(id={self.id}, username={self.username})>"