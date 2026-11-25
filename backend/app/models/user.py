"""User model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.api_key import ApiKey
    from app.models.github_profile import GitHubProfile
    from app.models.recommendation import Recommendation
    from app.models.subscription import Subscription
    from app.models.usage_record import UsageRecord


# Tier limits configuration (credits-based system)
# -1 means unlimited (for subscription users)
TIER_LIMITS = {
    "anonymous": {"options_per_generation": 1},
    "free": {"options_per_generation": 1},
    "pro": {"options_per_generation": 3},  # Pro credit pack buyers
    "unlimited": {"options_per_generation": 3},  # $29/mo subscription
    "team": {"options_per_generation": 5},
    "admin": {"options_per_generation": 5},
}

# Credit pack definitions
CREDIT_PACKS = {
    "starter": {"credits": 10, "price_cents": 500, "options_per_generation": 1},
    "pro": {"credits": 50, "price_cents": 1500, "options_per_generation": 3},
}

# Default credits for new users
DEFAULT_FREE_CREDITS = 3


class User(Base):
    """User model for storing user information."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Recommendation limits
    recommendation_count: Mapped[int] = mapped_column(Integer, default=0)  # Number of recommendations created today
    last_recommendation_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Last date a recommendation was created
    daily_limit: Mapped[int] = mapped_column(Integer, default=5)  # Daily recommendation limit (5 for registered users)
    role: Mapped[str] = mapped_column(String, default="free", index=True)  # User role: admin, premium, or free
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Add bio field
    email_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)  # New field for email notifications
    default_tone: Mapped[str] = mapped_column(String, default="professional")  # New field for default recommendation tone
    language: Mapped[str] = mapped_column(String, default="en")  # New field for user language preference (e.g., "en", "es")

    # Credits system (pay-as-you-go)
    credits: Mapped[int] = mapped_column(Integer, default=DEFAULT_FREE_CREDITS, nullable=False)  # Current credit balance
    lifetime_credits_purchased: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Track total purchases
    last_credit_pack: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Last pack purchased: starter, pro

    # Stripe / Subscription fields
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    subscription_tier: Mapped[str] = mapped_column(String(50), default="free", nullable=False, index=True)  # free, unlimited
    subscription_status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # active, past_due, cancelled, trialing

    # Relationships
    github_profiles: Mapped[list["GitHubProfile"]] = relationship("GitHubProfile", back_populates="user")
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="user")
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="user", uselist=False)
    usage_records: Mapped[list["UsageRecord"]] = relationship("UsageRecord", back_populates="user")
    api_keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="user")

    @property
    def effective_tier(self) -> str:
        """Get effective tier based on subscription or credit pack history."""
        if self.role == "admin":
            return "admin"
        # Unlimited monthly subscribers
        if self.subscription_tier == "unlimited" and self.subscription_status == "active":
            return "unlimited"
        # Users who bought pro pack get pro features
        if self.last_credit_pack == "pro":
            return "pro"
        return "free"

    @property
    def tier_limits(self) -> dict:
        """Get limits for user's current tier."""
        return TIER_LIMITS.get(self.effective_tier, TIER_LIMITS["free"])

    @property
    def options_per_generation(self) -> int:
        """Get number of options per generation based on tier."""
        return self.tier_limits["options_per_generation"]

    @property
    def has_unlimited_generations(self) -> bool:
        """Check if user has unlimited generations (subscription)."""
        return self.subscription_tier == "unlimited" and self.subscription_status == "active"

    @property
    def effective_daily_limit(self) -> int:
        """Daily generation limit: unlimited subscriptions report -1."""
        if self.has_unlimited_generations or self.role == "admin":
            return -1
        return self.daily_limit or 0

    @property
    def has_credits(self) -> bool:
        """Check if user has credits available."""
        return self.credits > 0 or self.has_unlimited_generations

    @property
    def can_generate(self) -> bool:
        """Check if user can generate a recommendation."""
        return self.has_credits or self.has_unlimited_generations or self.role == "admin"

    @property
    def is_subscriber(self) -> bool:
        """Check if user has active unlimited subscription."""
        return self.subscription_tier == "unlimited" and self.subscription_status == "active"

    @property
    def can_use_api(self) -> bool:
        """Check if user can use API (subscription or purchased credits)."""
        return self.is_subscriber or self.lifetime_credits_purchased >= 50

    @property
    def can_use_keyword_refinement(self) -> bool:
        """Check if user can use keyword refinement (pro pack or subscriber)."""
        return self.last_credit_pack == "pro" or self.is_subscriber or self.role == "admin"

    def use_credit(self) -> bool:
        """Deduct one credit. Returns True if successful, False if no credits."""
        if self.has_unlimited_generations or self.role == "admin":
            return True
        if self.credits > 0:
            self.credits -= 1
            return True
        return False

    def add_credits(self, amount: int, pack_type: str | None = None) -> None:
        """Add credits to user's balance."""
        self.credits += amount
        self.lifetime_credits_purchased += amount
        if pack_type:
            self.last_credit_pack = pack_type

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email}, tier={self.effective_tier})>"
