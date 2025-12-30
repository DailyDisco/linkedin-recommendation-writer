"""Pydantic schemas for billing and subscription endpoints."""

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# Tier types
TierType = Literal["free", "pro", "team"]
SubscriptionStatus = Literal["active", "past_due", "cancelled", "trialing"]


# Plan schemas
class TierLimits(BaseModel):
    """Limits for a subscription tier."""

    daily_generations: int = Field(description="Daily generation limit (-1 for unlimited)")
    options_per_generation: int = Field(description="Number of options per generation")


class PlanFeature(BaseModel):
    """A feature included in a plan."""

    name: str
    included: bool = True
    description: Optional[str] = None


class Plan(BaseModel):
    """Subscription plan details."""

    id: TierType
    name: str
    price_cents: int
    interval: Optional[Literal["month", "year"]] = None
    stripe_price_id: Optional[str] = None
    features: List[str]
    limits: TierLimits
    is_popular: bool = False


class PlansResponse(BaseModel):
    """Response containing available plans."""

    plans: List[Plan]


# Checkout schemas
class CheckoutRequest(BaseModel):
    """Request to create a checkout session."""

    price_id: str = Field(description="Stripe Price ID for the plan")
    success_url: Optional[str] = Field(default=None, description="URL to redirect after success")
    cancel_url: Optional[str] = Field(default=None, description="URL to redirect after cancel")


class CheckoutResponse(BaseModel):
    """Response with checkout session details."""

    checkout_url: str
    session_id: str


# Portal schemas
class PortalResponse(BaseModel):
    """Response with customer portal session details."""

    portal_url: str


# Subscription schemas
class SubscriptionResponse(BaseModel):
    """Current subscription details."""

    id: Optional[int] = None
    tier: TierType
    status: SubscriptionStatus
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    trial_end: Optional[datetime] = None

    class Config:
        from_attributes = True


# Usage schemas
class UsageHistoryItem(BaseModel):
    """Single day usage record."""

    date: date
    count: int


class UsageResponse(BaseModel):
    """Usage statistics for the current period."""

    tier: TierType
    period_start: datetime
    period_end: datetime
    generations_used: int
    generations_limit: int = Field(description="-1 for unlimited")
    generations_remaining: int = Field(description="-1 for unlimited")
    resets_at: datetime
    history: List[UsageHistoryItem] = []


# API Key schemas
class ApiKeyCreateRequest(BaseModel):
    """Request to create a new API key."""

    name: str = Field(min_length=1, max_length=255, description="Name for the API key")
    scopes: List[str] = Field(default=["recommendations:read", "recommendations:write"])
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365, description="Days until expiration")


class ApiKeyResponse(BaseModel):
    """API key details (without the full key)."""

    id: int
    name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    last_used_at: Optional[datetime] = None
    usage_count: int
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(BaseModel):
    """Response after creating an API key (includes full key, shown only once)."""

    id: int
    name: str
    key: str = Field(description="Full API key - store securely, shown only once")
    key_prefix: str
    scopes: List[str]
    expires_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyListResponse(BaseModel):
    """List of API keys."""

    keys: List[ApiKeyResponse]


# Webhook schemas
class WebhookEventRecord(BaseModel):
    """Record of a processed webhook event."""

    id: int
    stripe_event_id: str
    event_type: str
    processed_at: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Error schemas
class BillingError(BaseModel):
    """Billing-related error response."""

    detail: str
    error_code: str
    upgrade_url: Optional[str] = None


# Feature gating
class FeatureAccess(BaseModel):
    """Feature access for current user."""

    tier: TierType
    features: dict = Field(default_factory=dict)


# Predefined plans
FREE_PLAN = Plan(
    id="free",
    name="Free",
    price_cents=0,
    interval=None,
    stripe_price_id=None,
    features=[
        "3 recommendations per day",
        "1 option per generation",
        "Basic tones",
    ],
    limits=TierLimits(daily_generations=3, options_per_generation=1),
)

PRO_PLAN = Plan(
    id="pro",
    name="Pro",
    price_cents=900,
    interval="month",
    stripe_price_id=None,  # Set from config
    features=[
        "50 recommendations per day",
        "3 options per generation",
        "All tones",
        "Keyword refinement",
        "Version history",
    ],
    limits=TierLimits(daily_generations=50, options_per_generation=3),
    is_popular=True,
)

TEAM_PLAN = Plan(
    id="team",
    name="Team",
    price_cents=2900,
    interval="month",
    stripe_price_id=None,  # Set from config
    features=[
        "Unlimited recommendations",
        "5 options per generation",
        "All tones",
        "Keyword refinement",
        "Version history",
        "API access",
        "Priority support",
    ],
    limits=TierLimits(daily_generations=-1, options_per_generation=5),
)


def get_plans(stripe_price_id_pro: str, stripe_price_id_team: str) -> List[Plan]:
    """Get all plans with Stripe price IDs populated."""
    pro = PRO_PLAN.model_copy()
    pro.stripe_price_id = stripe_price_id_pro

    team = TEAM_PLAN.model_copy()
    team.stripe_price_id = stripe_price_id_team

    return [FREE_PLAN, pro, team]
