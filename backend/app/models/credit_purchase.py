"""Credit purchase model for tracking credit pack purchases."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class CreditPurchase(Base):
    """Model for tracking credit pack purchases."""

    __tablename__ = "credit_purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Purchase details
    pack_type: Mapped[str] = mapped_column(String(50), nullable=False)  # starter, pro
    credits_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    # Stripe
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_checkout_session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)

    # Status: pending, completed, failed, refunded
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="credit_purchases")

    def complete(self) -> None:
        """Mark the purchase as completed."""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<CreditPurchase(id={self.id}, user_id={self.user_id}, pack={self.pack_type}, credits={self.credits_amount})>"
