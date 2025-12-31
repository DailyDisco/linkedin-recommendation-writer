"""Subscription service for managing user subscriptions."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.billing import (
    Plan,
    PlansResponse,
    SubscriptionResponse,
    get_plans,
)

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing subscriptions."""

    def get_plans(self) -> PlansResponse:
        """Get all available subscription plans.

        Returns:
            PlansResponse with all plans
        """
        plans = get_plans(
            stripe_price_id_pro=settings.STRIPE_PRICE_ID_PRO,
            stripe_price_id_team=settings.STRIPE_PRICE_ID_TEAM,
        )
        return PlansResponse(plans=plans)

    def get_plan_by_id(self, plan_id: str) -> Optional[Plan]:
        """Get a specific plan by ID.

        Args:
            plan_id: Plan ID (free, pro, team)

        Returns:
            Plan if found, None otherwise
        """
        plans = get_plans(
            stripe_price_id_pro=settings.STRIPE_PRICE_ID_PRO,
            stripe_price_id_team=settings.STRIPE_PRICE_ID_TEAM,
        )
        for plan in plans:
            if plan.id == plan_id:
                return plan
        return None

    async def get_user_subscription(
        self,
        user: User,
        db: AsyncSession,
    ) -> SubscriptionResponse:
        """Get current subscription for a user.

        Args:
            user: User to get subscription for
            db: Database session

        Returns:
            SubscriptionResponse with current subscription details
        """
        # Check for subscription record
        result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        subscription = result.scalar_one_or_none()

        if subscription:
            return SubscriptionResponse(
                id=subscription.id,
                tier=subscription.tier,
                status=subscription.status,
                stripe_subscription_id=subscription.stripe_subscription_id,
                stripe_customer_id=subscription.stripe_customer_id,
                current_period_start=subscription.current_period_start,
                current_period_end=subscription.current_period_end,
                cancel_at_period_end=subscription.cancel_at_period_end,
                trial_end=subscription.trial_end,
            )

        # Return free tier status
        return SubscriptionResponse(
            id=None,
            tier=user.subscription_tier or "free",
            status=user.subscription_status or "active",
            stripe_subscription_id=None,
            stripe_customer_id=user.stripe_customer_id,
            current_period_start=None,
            current_period_end=None,
            cancel_at_period_end=False,
            trial_end=None,
        )

    async def update_user_tier(
        self,
        user: User,
        tier: str,
        status: str,
        db: AsyncSession,
    ) -> None:
        """Update user's subscription tier.

        Args:
            user: User to update
            tier: New tier (free, pro, team)
            status: New status (active, past_due, cancelled, trialing)
            db: Database session
        """
        user.subscription_tier = tier
        user.subscription_status = status
        await db.commit()
        await db.refresh(user)
        logger.info(f"Updated user {user.id} to tier={tier}, status={status}")

    async def check_feature_access(
        self,
        user: User,
        feature: str,
    ) -> bool:
        """Check if user has access to a feature.

        Args:
            user: User to check
            feature: Feature name to check

        Returns:
            True if user has access
        """
        tier = user.effective_tier

        # Define feature access by tier
        feature_access = {
            "multiple_options": ["pro", "team", "admin"],
            "keyword_refinement": ["pro", "team", "admin"],
            "all_tones": ["pro", "team", "admin"],
            "version_history": ["pro", "team", "admin"],
            "api_access": ["team", "admin"],
            "priority_support": ["team", "admin"],
        }

        allowed_tiers = feature_access.get(feature, [])
        return tier in allowed_tiers

    async def get_tier_for_price(self, price_id: str) -> str:
        """Get tier name for a Stripe price ID.

        Args:
            price_id: Stripe Price ID

        Returns:
            Tier name (free, pro, team)
        """
        if price_id == settings.STRIPE_PRICE_ID_PRO:
            return "pro"
        if price_id == settings.STRIPE_PRICE_ID_TEAM:
            return "team"
        return "free"

    async def validate_upgrade(
        self,
        user: User,
        target_tier: str,
    ) -> tuple[bool, str]:
        """Validate if user can upgrade to target tier.

        Args:
            user: User attempting upgrade
            target_tier: Target tier

        Returns:
            Tuple of (is_valid, error_message)
        """
        current_tier = user.effective_tier

        # Can't upgrade to same tier
        if current_tier == target_tier:
            return False, f"Already on {target_tier} plan"

        # Can't upgrade to free (that's a downgrade)
        if target_tier == "free":
            return False, "Use billing portal to cancel subscription"

        # Admin can't change tier
        if current_tier == "admin":
            return False, "Admin accounts cannot change subscription"

        return True, ""
