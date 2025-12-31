"""Subscription model for billing and subscription management."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Subscription(Base):
    """Subscription model for storing subscription information."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Stripe IDs
    stripe_customer_id = Column(String(255), nullable=False, unique=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_price_id = Column(String(255), nullable=True)

    # Status
    tier = Column(String(50), default="free", nullable=False, index=True)  # free, pro, team
    status = Column(String(50), default="active", nullable=False, index=True)  # active, past_due, cancelled, trialing

    # Billing period
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)

    # Trial
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)

    # Cancellation
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="subscription")

    @property
    def is_active(self) -> bool:
        """Check if subscription is active (including trialing)."""
        return self.status in ("active", "trialing")

    @property
    def is_trialing(self) -> bool:
        """Check if subscription is in trial period."""
        return self.status == "trialing"

    @property
    def is_cancelled(self) -> bool:
        """Check if subscription is cancelled."""
        return self.status == "cancelled" or self.cancel_at_period_end

    @property
    def days_until_renewal(self) -> int | None:
        """Get days until next renewal."""
        if not self.current_period_end:
            return None
        delta = self.current_period_end - datetime.now(timezone.utc)
        return max(0, delta.days)

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier={self.tier}, status={self.status})>"
