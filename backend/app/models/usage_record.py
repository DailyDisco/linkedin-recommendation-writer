"""Usage record model for tracking daily usage."""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UsageRecord(Base):
    """Usage record model for tracking daily generation counts."""

    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Usage data
    date: Mapped[date] = mapped_column(Date, nullable=False)
    generation_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    tier: Mapped[str] = mapped_column(String(50), nullable=False)  # Tier at time of usage

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="usage_records")
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_usage_records_user_date"),)

    def __repr__(self) -> str:
        return f"<UsageRecord(id={self.id}, user_id={self.user_id}, date={self.date}, count={self.generation_count})>"
