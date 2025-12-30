"""Stripe webhook event model for idempotency and debugging."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text

from app.core.database import Base


class StripeWebhookEvent(Base):
    """Stripe webhook event model for storing and tracking webhook events."""

    __tablename__ = "stripe_webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    stripe_event_id = Column(String(255), nullable=False, unique=True, index=True)
    event_type = Column(String(255), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    @property
    def is_processed(self) -> bool:
        """Check if event has been processed."""
        return self.processed_at is not None

    @property
    def has_error(self) -> bool:
        """Check if event processing resulted in error."""
        return self.error is not None

    def mark_processed(self) -> None:
        """Mark event as processed."""
        self.processed_at = datetime.now(timezone.utc)

    def mark_error(self, error_message: str) -> None:
        """Mark event as having an error."""
        self.error = error_message
        self.processed_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<StripeWebhookEvent(id={self.id}, event_id={self.stripe_event_id}, type={self.event_type})>"
