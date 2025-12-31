"""Usage record model for tracking daily usage."""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UsageRecord(Base):
    """Usage record model for tracking daily generation counts."""

    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Usage data
    date = Column(Date, nullable=False)
    generation_count = Column(Integer, default=0)

    # Metadata
    tier = Column(String(50), nullable=False)  # Tier at time of usage

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="usage_records")

    # Unique constraint on user_id + date
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_usage_records_user_date"),)

    def __repr__(self) -> str:
        return f"<UsageRecord(id={self.id}, user_id={self.user_id}, date={self.date}, count={self.generation_count})>"
