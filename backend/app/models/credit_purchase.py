"""Credit purchase model for tracking credit pack purchases."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class CreditPurchase(Base):
    """Model for tracking credit pack purchases."""

    __tablename__ = "credit_purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Purchase details
    pack_type = Column(String(50), nullable=False)  # starter, pro
    credits_amount = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=False)

    # Stripe
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_checkout_session_id = Column(String(255), nullable=True, unique=True, index=True)

    # Status: pending, completed, failed, refunded
    status = Column(String(50), nullable=False, default="pending")

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", backref="credit_purchases")

    def complete(self) -> None:
        """Mark the purchase as completed."""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<CreditPurchase(id={self.id}, user_id={self.user_id}, pack={self.pack_type}, credits={self.credits_amount})>"
