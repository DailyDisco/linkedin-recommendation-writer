"""Pydantic schemas for billing and subscription endpoints."""

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# Tier types (credit-based system)
TierType = Literal["free", "pro", "unlimited", "admin"]
PackType = Literal["starter", "pro"]
SubscriptionStatus = Literal["active", "past_due", "cancelled", "trialing"]


# Credit pack schemas
class CreditPack(BaseModel):
    """Credit pack available for purchase."""

    id: PackType
    name: str
    credits: int
    price_cents: int
    options_per_generation: int
    stripe_price_id: Optional[str] = None
    description: str


class CreditPacksResponse(BaseModel):
    """Response containing available credit packs."""

    packs: List[CreditPack]


class CreditBalanceResponse(BaseModel):
    """User's current credit balance."""

    credits: int
    lifetime_credits_purchased: int
    last_pack_purchased: Optional[str] = None
    has_unlimited: bool = False


class CreditPurchaseRequest(BaseModel):
    """Request to purchase a credit pack."""

    pack_id: PackType
    success_url: Optional[str] = Field(default=None, description="URL to redirect after success")
    cancel_url: Optional[str] = Field(default=None, description="URL to redirect after cancel")


class CreditPurchaseResponse(BaseModel):
    """Response for a credit purchase record."""

    id: int
    pack_type: str
    credits_amount: int
    price_cents: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Plan schemas (for unlimited subscription)
class TierLimits(BaseModel):
    """Limits for a subscription tier."""

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


# Predefined credit packs
STARTER_PACK = CreditPack(
    id="starter",
    name="Starter Pack",
    credits=10,
    price_cents=500,
    options_per_generation=1,
    description="Perfect for occasional use",
)

PRO_PACK = CreditPack(
    id="pro",
    name="Pro Pack",
    credits=50,
    price_cents=1500,
    options_per_generation=3,
    description="Best value - includes 3 options per generation",
)


# Unlimited subscription plan
UNLIMITED_PLAN = Plan(
    id="unlimited",
    name="Unlimited Monthly",
    price_cents=2900,
    interval="month",
    stripe_price_id=None,  # Set from config
    features=[
        "Unlimited recommendations",
        "3 options per generation",
        "All tones",
        "Keyword refinement",
        "API access",
        "Priority support",
    ],
    limits=TierLimits(options_per_generation=3),
    is_popular=False,
)


def get_credit_packs(
    stripe_price_id_starter: Optional[str] = None,
    stripe_price_id_pro: Optional[str] = None,
) -> List[CreditPack]:
    """Get all credit packs with Stripe price IDs populated."""
    starter = STARTER_PACK.model_copy()
    starter.stripe_price_id = stripe_price_id_starter

    pro = PRO_PACK.model_copy()
    pro.stripe_price_id = stripe_price_id_pro

    return [starter, pro]


def get_unlimited_plan(stripe_price_id: Optional[str] = None) -> Plan:
    """Get unlimited plan with Stripe price ID populated."""
    plan = UNLIMITED_PLAN.model_copy()
    plan.stripe_price_id = stripe_price_id
    return plan
