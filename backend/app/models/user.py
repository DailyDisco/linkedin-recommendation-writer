"""User model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.api_key import ApiKey
    from app.models.subscription import Subscription
    from app.models.usage_record import UsageRecord


# Tier limits configuration
TIER_LIMITS = {
    "anonymous": {"daily_generations": 3, "options_per_generation": 1},
    "free": {"daily_generations": 3, "options_per_generation": 1},
    "pro": {"daily_generations": 50, "options_per_generation": 3},
    "team": {"daily_generations": -1, "options_per_generation": 5},  # -1 = unlimited
    "admin": {"daily_generations": -1, "options_per_generation": 5},
}


class User(Base):
    """User model for storing user information."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Recommendation limits
    recommendation_count = Column(Integer, default=0)  # Number of recommendations created today
    last_recommendation_date = Column(DateTime, nullable=True)  # Last date a recommendation was created
    daily_limit = Column(Integer, default=5)  # Daily recommendation limit (5 for registered users)
    role = Column(String, default="free", index=True)  # User role: admin, premium, or free
    bio = Column(Text, nullable=True)  # Add bio field
    email_notifications_enabled = Column(Boolean, default=True)  # New field for email notifications
    default_tone = Column(String, default="professional")  # New field for default recommendation tone
    language = Column(String, default="en")  # New field for user language preference (e.g., "en", "es")

    # Stripe / Subscription fields
    stripe_customer_id = Column(String(255), unique=True, nullable=True, index=True)
    subscription_tier = Column(String(50), default="free", nullable=False, index=True)  # free, pro, team
    subscription_status = Column(String(50), default="active", nullable=False)  # active, past_due, cancelled, trialing

    # Relationships
    github_profiles = relationship("GitHubProfile", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    usage_records = relationship("UsageRecord", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")

    @property
    def effective_tier(self) -> str:
        """Get effective subscription tier (considers admin role)."""
        if self.role == "admin":
            return "admin"
        return self.subscription_tier or "free"

    @property
    def tier_limits(self) -> dict:
        """Get limits for user's current tier."""
        return TIER_LIMITS.get(self.effective_tier, TIER_LIMITS["free"])

    @property
    def effective_daily_limit(self) -> int:
        """Get effective daily generation limit based on tier."""
        return self.tier_limits["daily_generations"]

    @property
    def options_per_generation(self) -> int:
        """Get number of options per generation based on tier."""
        return self.tier_limits["options_per_generation"]

    @property
    def has_unlimited_generations(self) -> bool:
        """Check if user has unlimited generations."""
        return self.effective_daily_limit == -1

    @property
    def is_pro_or_higher(self) -> bool:
        """Check if user has Pro tier or higher."""
        return self.effective_tier in ("pro", "team", "admin")

    @property
    def is_team_or_higher(self) -> bool:
        """Check if user has Team tier or higher."""
        return self.effective_tier in ("team", "admin")

    @property
    def can_use_api(self) -> bool:
        """Check if user can use API (Team tier feature)."""
        return self.is_team_or_higher

    @property
    def can_use_keyword_refinement(self) -> bool:
        """Check if user can use keyword refinement (Pro+ feature)."""
        return self.is_pro_or_higher

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email}, tier={self.effective_tier})>"
