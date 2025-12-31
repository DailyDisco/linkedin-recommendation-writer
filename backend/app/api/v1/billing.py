"""Billing API endpoints for subscription and payment management."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.core.dependencies import get_database_session
from app.models.api_key import ApiKey
from app.models.credit_purchase import CreditPurchase
from app.models.user import CREDIT_PACKS, User
from app.schemas.billing import (
    ApiKeyCreatedResponse,
    ApiKeyCreateRequest,
    ApiKeyListResponse,
    ApiKeyResponse,
    CheckoutRequest,
    CheckoutResponse,
    CreditBalanceResponse,
    CreditPack,
    CreditPacksResponse,
    CreditPurchaseRequest,
    CreditPurchaseResponse,
    PlansResponse,
    PortalResponse,
    SubscriptionResponse,
    UsageResponse,
    get_credit_packs,
    get_unlimited_plan,
)
from app.services.billing.stripe_service import StripeService
from app.services.billing.subscription_service import SubscriptionService
from app.services.billing.usage_service import UsageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


# Dependency injection for services
def get_stripe_service() -> StripeService:
    """Get Stripe service instance."""
    return StripeService()


def get_subscription_service() -> SubscriptionService:
    """Get subscription service instance."""
    return SubscriptionService()


def get_usage_service() -> UsageService:
    """Get usage service instance."""
    return UsageService()


@router.get("/plans", response_model=PlansResponse)
async def get_plans() -> PlansResponse:
    """Get available subscription plans (unlimited monthly only).

    This endpoint is public and does not require authentication.
    """
    if not settings.BILLING_ENABLED:
        raise HTTPException(status_code=503, detail="Billing is not enabled")

    unlimited = get_unlimited_plan(settings.STRIPE_PRICE_ID_UNLIMITED)
    return PlansResponse(plans=[unlimited])


@router.get("/credit-packs", response_model=CreditPacksResponse)
async def get_available_credit_packs() -> CreditPacksResponse:
    """Get available credit packs for purchase.

    This endpoint is public and does not require authentication.
    Credit packs are one-time purchases (not subscriptions).
    """
    if not settings.BILLING_ENABLED:
        raise HTTPException(status_code=503, detail="Billing is not enabled")

    packs = get_credit_packs(
        stripe_price_id_starter=settings.STRIPE_PRICE_ID_STARTER,
        stripe_price_id_pro=settings.STRIPE_PRICE_ID_PRO_PACK,
    )
    return CreditPacksResponse(packs=packs)


@router.get("/credits", response_model=CreditBalanceResponse)
async def get_credit_balance(
    current_user: User = Depends(get_current_user),
) -> CreditBalanceResponse:
    """Get the current user's credit balance."""
    return CreditBalanceResponse(
        credits=current_user.credits,
        lifetime_credits_purchased=current_user.lifetime_credits_purchased,
        last_pack_purchased=current_user.last_credit_pack,
        has_unlimited=current_user.has_unlimited_generations,
    )


@router.post("/credits/purchase", response_model=CheckoutResponse)
async def purchase_credit_pack(
    request: CreditPurchaseRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session),
    stripe_service: StripeService = Depends(get_stripe_service),
) -> CheckoutResponse:
    """Purchase a credit pack (one-time payment).

    Creates a Stripe Checkout session for a one-time credit pack purchase.
    After successful payment, credits are added to the user's account.
    """
    if not settings.BILLING_ENABLED:
        raise HTTPException(status_code=503, detail="Billing is not enabled")

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Payment processing not configured")

    # Get referer for URLs
    referer = http_request.headers.get("referer", "http://localhost:5173")
    base_url = referer.rstrip("/")

    success_url = request.success_url or f"{base_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = request.cancel_url or f"{base_url}/checkout/cancel"

    try:
        result = await stripe_service.create_credit_pack_checkout(
            user=current_user,
            pack_type=request.pack_id,
            success_url=success_url,
            cancel_url=cancel_url,
            db=db,
        )
        return CheckoutResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Credit pack checkout failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/credits/history", response_model=List[CreditPurchaseResponse])
async def get_credit_purchase_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session),
) -> List[CreditPurchaseResponse]:
    """Get the user's credit purchase history."""
    result = await db.execute(select(CreditPurchase).where(CreditPurchase.user_id == current_user.id).order_by(CreditPurchase.created_at.desc()))
    purchases = result.scalars().all()

    return [
        CreditPurchaseResponse(
            id=p.id,
            pack_type=p.pack_type,
            credits_amount=p.credits_amount,
            price_cents=p.price_cents,
            status=p.status,
            created_at=p.created_at,
            completed_at=p.completed_at,
        )
        for p in purchases
    ]


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session),
    stripe_service: StripeService = Depends(get_stripe_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> CheckoutResponse:
    """Create a Stripe Checkout session for upgrading subscription.

    Requires authentication. Returns a URL to redirect the user to.
    """
    if not settings.BILLING_ENABLED:
        raise HTTPException(status_code=503, detail="Billing is not enabled")

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Payment processing not configured")

    # Determine tier from price ID
    tier = await subscription_service.get_tier_for_price(request.price_id)

    # Validate upgrade
    is_valid, error = await subscription_service.validate_upgrade(current_user, tier)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Build URLs
    base_url = request.success_url or "http://localhost:5173"
    if base_url.endswith("/"):
        base_url = base_url[:-1]

    success_url = f"{base_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = request.cancel_url or f"{base_url}/checkout/cancel"

    try:
        result = await stripe_service.create_checkout_session(
            user=current_user,
            price_id=request.price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            db=db,
        )
        return CheckoutResponse(**result)
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session),
    stripe_service: StripeService = Depends(get_stripe_service),
) -> PortalResponse:
    """Create a Stripe Customer Portal session for managing subscription.

    Requires authentication and an existing Stripe customer.
    """
    if not settings.BILLING_ENABLED:
        raise HTTPException(status_code=503, detail="Billing is not enabled")

    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No subscription found. Please upgrade first.")

    # Get return URL from referer or default
    referer = request.headers.get("referer", "http://localhost:5173")
    return_url = f"{referer.rstrip('/')}/settings/billing"

    try:
        result = await stripe_service.create_portal_session(
            user=current_user,
            return_url=return_url,
            db=db,
        )
        return PortalResponse(**result)
    except Exception as e:
        logger.error(f"Portal creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    """Get current subscription details for the authenticated user."""
    return await subscription_service.get_user_subscription(current_user, db)


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session),
    usage_service: UsageService = Depends(get_usage_service),
) -> UsageResponse:
    """Get usage statistics for the authenticated user."""
    return await usage_service.get_usage(current_user, db)


@router.post("/webhooks")
async def handle_webhook(
    request: Request,
    db: AsyncSession = Depends(get_database_session),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """Handle Stripe webhook events.

    This endpoint is called by Stripe to notify us of subscription changes.
    It verifies the webhook signature before processing.
    """
    if not settings.BILLING_ENABLED:
        raise HTTPException(status_code=503, detail="Billing is not enabled")

    # Get raw body for signature verification
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    try:
        event = stripe_service.construct_webhook_event(payload, signature)
    except ValueError as e:
        logger.warning(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        await stripe_service.process_webhook_event(event, db)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        # Still return 200 to prevent Stripe from retrying
        return {"status": "error", "message": str(e)}


# API Keys endpoints (Team tier only)
@router.post("/api-keys", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    request: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session),
) -> ApiKeyCreatedResponse:
    """Create a new API key for the authenticated user.

    Requires Team tier or higher. The full API key is only shown once.
    """
    if not current_user.can_use_api:
        raise HTTPException(
            status_code=403,
            detail="API access requires Team tier or higher",
        )

    # Generate new API key
    full_key, key_hash, key_prefix = ApiKey.generate_key()

    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)

    # Create API key record
    api_key = ApiKey(
        user_id=current_user.id,
        name=request.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=request.scopes,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info(f"Created API key {key_prefix}... for user {current_user.id}")

    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key=full_key,  # Only shown once
        key_prefix=key_prefix,
        scopes=api_key.scopes or [],
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.get("/api-keys", response_model=ApiKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session),
) -> ApiKeyListResponse:
    """List all API keys for the authenticated user.

    Requires Team tier or higher.
    """
    if not current_user.can_use_api:
        raise HTTPException(
            status_code=403,
            detail="API access requires Team tier or higher",
        )

    result = await db.execute(select(ApiKey).where(ApiKey.user_id == current_user.id).order_by(ApiKey.created_at.desc()))
    keys = result.scalars().all()

    return ApiKeyListResponse(
        keys=[
            ApiKeyResponse(
                id=k.id,
                name=k.name,
                key_prefix=k.key_prefix,
                scopes=k.scopes or [],
                is_active=k.is_active,
                last_used_at=k.last_used_at,
                usage_count=k.usage_count,
                expires_at=k.expires_at,
                created_at=k.created_at,
            )
            for k in keys
        ]
    )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session),
):
    """Revoke an API key.

    Requires Team tier or higher. Can only revoke own keys.
    """
    if not current_user.can_use_api:
        raise HTTPException(
            status_code=403,
            detail="API access requires Team tier or higher",
        )

    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.user_id == current_user.id,
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.is_active = False
    await db.commit()

    logger.info(f"Revoked API key {api_key.key_prefix}... for user {current_user.id}")

    return {"status": "success", "message": "API key revoked"}


# Feature access endpoint
@router.get("/features")
async def get_feature_access(
    current_user: User = Depends(get_current_user),
):
    """Get feature access for the authenticated user based on their tier and credits."""
    tier = current_user.effective_tier

    return {
        "tier": tier,
        "credits": current_user.credits,
        "has_unlimited": current_user.has_unlimited_generations,
        "can_generate": current_user.can_generate,
        "features": {
            "multiple_options": current_user.last_credit_pack == "pro" or current_user.is_subscriber,
            "keyword_refinement": current_user.can_use_keyword_refinement,
            "all_tones": current_user.last_credit_pack == "pro" or current_user.is_subscriber,
            "api_access": current_user.can_use_api,
            "priority_support": current_user.is_subscriber,
        },
        "limits": {
            "options_per_generation": current_user.options_per_generation,
        },
    }
