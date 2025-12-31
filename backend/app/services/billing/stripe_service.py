"""Stripe API service for payment processing."""

import logging
from datetime import datetime, timezone
from typing import Any, Literal, Optional

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.credit_purchase import CreditPurchase
from app.models.subscription import Subscription
from app.models.user import CREDIT_PACKS, User
from app.models.webhook_event import StripeWebhookEvent

logger = logging.getLogger(__name__)

# Map price IDs to pack types
PRICE_TO_PACK: dict[str, str] = {}  # Populated at runtime from settings


class StripeService:
    """Service for interacting with Stripe API."""

    def __init__(self):
        """Initialize Stripe service with API key."""
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    async def create_customer(self, user: User) -> str:
        """Create a Stripe customer for a user.

        Args:
            user: User to create customer for

        Returns:
            Stripe customer ID
        """
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name or user.username,
                metadata={
                    "user_id": str(user.id),
                    "username": user.username,
                },
            )
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id
        except stripe.StripeError as e:
            logger.error(f"Failed to create Stripe customer for user {user.id}: {e}")
            raise

    async def get_or_create_customer(self, user: User, db: AsyncSession) -> str:
        """Get existing Stripe customer or create new one.

        Args:
            user: User to get/create customer for
            db: Database session

        Returns:
            Stripe customer ID
        """
        if user.stripe_customer_id:
            return user.stripe_customer_id

        customer_id = await self.create_customer(user)
        user.stripe_customer_id = customer_id
        await db.commit()
        await db.refresh(user)

        return customer_id

    async def create_checkout_session(
        self,
        user: User,
        price_id: str,
        success_url: str,
        cancel_url: str,
        db: AsyncSession,
        trial_days: Optional[int] = None,
    ) -> dict:
        """Create a Stripe Checkout session.

        Args:
            user: User creating the checkout
            price_id: Stripe Price ID for the subscription
            success_url: URL to redirect after successful checkout
            cancel_url: URL to redirect if checkout is cancelled
            db: Database session
            trial_days: Number of trial days (overrides default)

        Returns:
            Dict with checkout_url and session_id
        """
        customer_id = await self.get_or_create_customer(user, db)

        # Determine trial period
        if trial_days is None and settings.TRIALS_ENABLED:
            # Check if user has had a trial before
            trial_days = settings.STRIPE_TRIAL_DAYS if not await self._has_had_trial(user, db) else 0

        try:
            session_params = {
                "customer": customer_id,
                "mode": "subscription",
                "line_items": [{"price": price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {
                    "user_id": str(user.id),
                },
                "subscription_data": {
                    "metadata": {
                        "user_id": str(user.id),
                    },
                },
            }

            # Add trial period if applicable
            if trial_days and trial_days > 0:
                session_params["subscription_data"]["trial_period_days"] = trial_days

            session = stripe.checkout.Session.create(**session_params)

            logger.info(f"Created checkout session {session.id} for user {user.id}")
            return {
                "checkout_url": session.url,
                "session_id": session.id,
            }
        except stripe.StripeError as e:
            logger.error(f"Failed to create checkout session for user {user.id}: {e}")
            raise

    async def create_credit_pack_checkout(
        self,
        user: User,
        pack_type: Literal["starter", "pro"],
        success_url: str,
        cancel_url: str,
        db: AsyncSession,
    ) -> dict:
        """Create a Stripe Checkout session for a one-time credit pack purchase.

        Args:
            user: User making the purchase
            pack_type: Type of credit pack (starter or pro)
            success_url: URL to redirect after successful checkout
            cancel_url: URL to redirect if checkout is cancelled
            db: Database session

        Returns:
            Dict with checkout_url and session_id
        """
        # Get the correct price ID
        if pack_type == "starter":
            price_id = settings.STRIPE_PRICE_ID_STARTER
        else:
            price_id = settings.STRIPE_PRICE_ID_PRO_PACK

        if not price_id:
            raise ValueError(f"No Stripe price configured for {pack_type} pack")

        pack_info = CREDIT_PACKS.get(pack_type)
        if not pack_info:
            raise ValueError(f"Invalid pack type: {pack_type}")

        customer_id = await self.get_or_create_customer(user, db)

        # Create a pending credit purchase record
        purchase = CreditPurchase(
            user_id=user.id,
            pack_type=pack_type,
            credits_amount=pack_info["credits"],
            price_cents=pack_info["price_cents"],
            status="pending",
        )
        db.add(purchase)
        await db.flush()  # Get the purchase ID

        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                mode="payment",  # One-time payment, not subscription
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": str(user.id),
                    "purchase_type": "credit_pack",
                    "pack_type": pack_type,
                    "credits_amount": str(pack_info["credits"]),
                    "purchase_id": str(purchase.id),
                },
            )

            # Update purchase with session ID
            purchase.stripe_checkout_session_id = session.id

            await db.commit()

            logger.info(f"Created credit pack checkout {session.id} for user {user.id}, pack={pack_type}")
            return {
                "checkout_url": session.url,
                "session_id": session.id,
            }
        except stripe.StripeError as e:
            logger.error(f"Failed to create credit pack checkout for user {user.id}: {e}")
            await db.rollback()
            raise

    async def create_portal_session(
        self,
        user: User,
        return_url: str,
        db: AsyncSession,
    ) -> dict:
        """Create a Stripe Customer Portal session.

        Args:
            user: User accessing the portal
            return_url: URL to return to after portal session
            db: Database session

        Returns:
            Dict with portal_url
        """
        customer_id = await self.get_or_create_customer(user, db)

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )

            logger.info(f"Created portal session for user {user.id}")
            return {"portal_url": session.url}
        except stripe.StripeError as e:
            logger.error(f"Failed to create portal session for user {user.id}: {e}")
            raise

    def construct_webhook_event(self, payload: bytes, signature: str) -> Any:
        """Construct and verify a webhook event.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header

        Returns:
            Verified Stripe event

        Raises:
            ValueError: If signature verification fails
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret,
            )
            return event
        except stripe.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise ValueError("Invalid webhook signature")

    async def process_webhook_event(
        self,
        event: Any,
        db: AsyncSession,
    ) -> bool:
        """Process a Stripe webhook event.

        Args:
            event: Verified Stripe event
            db: Database session

        Returns:
            True if processed successfully
        """
        event_id = event.id
        event_type = event.type

        # Check for duplicate event (idempotency)
        existing = await db.execute(select(StripeWebhookEvent).where(StripeWebhookEvent.stripe_event_id == event_id))
        if existing.scalar_one_or_none():
            logger.info(f"Duplicate webhook event {event_id}, skipping")
            return True

        # Record the event
        webhook_event = StripeWebhookEvent(
            stripe_event_id=event_id,
            event_type=event_type,
            payload=dict(event),
        )
        db.add(webhook_event)

        try:
            # Handle specific event types
            if event_type == "checkout.session.completed":
                await self._handle_checkout_completed(event, db)
            elif event_type == "customer.subscription.created":
                await self._handle_subscription_created(event, db)
            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(event, db)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(event, db)
            elif event_type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(event, db)
            elif event_type == "invoice.payment_failed":
                await self._handle_payment_failed(event, db)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")

            webhook_event.mark_processed()
            await db.commit()
            return True

        except Exception as e:
            logger.error(f"Error processing webhook event {event_id}: {e}")
            webhook_event.mark_error(str(e))
            await db.commit()
            raise

    async def _handle_checkout_completed(self, event: Any, db: AsyncSession) -> None:
        """Handle checkout.session.completed event."""
        session = event.data.object
        user_id = int(session.metadata.get("user_id", 0))

        if not user_id:
            logger.warning("Checkout completed without user_id in metadata")
            return

        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"User {user_id} not found for checkout completion")
            return

        # Update user's Stripe customer ID if not set
        if not user.stripe_customer_id:
            user.stripe_customer_id = session.customer

        # Check if this is a credit pack purchase
        purchase_type = session.metadata.get("purchase_type")
        if purchase_type == "credit_pack":
            await self._handle_credit_pack_purchase(session, user, db)
        else:
            logger.info(f"Checkout completed for user {user_id}")

    async def _handle_credit_pack_purchase(self, session: Any, user: User, db: AsyncSession) -> None:
        """Handle credit pack purchase completion."""
        pack_type = session.metadata.get("pack_type")
        credits_amount = int(session.metadata.get("credits_amount", 0))
        purchase_id = int(session.metadata.get("purchase_id", 0))

        if not pack_type or not credits_amount:
            logger.error(f"Invalid credit pack metadata for session {session.id}")
            return

        # Update the credit purchase record
        if purchase_id:
            result = await db.execute(select(CreditPurchase).where(CreditPurchase.id == purchase_id))
            purchase = result.scalar_one_or_none()
            if purchase:
                purchase.complete()
                if session.payment_intent:
                    purchase.stripe_payment_intent_id = session.payment_intent

        # Add credits to user
        user.add_credits(credits_amount, pack_type)

        logger.info(f"Credit pack purchase completed for user {user.id}: " f"pack={pack_type}, credits={credits_amount}, new_balance={user.credits}")

    async def _handle_subscription_created(self, event: Any, db: AsyncSession) -> None:
        """Handle customer.subscription.created event."""
        subscription = event.data.object
        await self._update_subscription_from_stripe(subscription, db)

    async def _handle_subscription_updated(self, event: Any, db: AsyncSession) -> None:
        """Handle customer.subscription.updated event."""
        subscription = event.data.object
        await self._update_subscription_from_stripe(subscription, db)

    async def _handle_subscription_deleted(self, event: Any, db: AsyncSession) -> None:
        """Handle customer.subscription.deleted event."""
        subscription = event.data.object
        customer_id = subscription.customer

        # Find user by Stripe customer ID
        result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"No user found for customer {customer_id}")
            return

        # Downgrade user to free tier
        user.subscription_tier = "free"
        user.subscription_status = "cancelled"

        # Update subscription record
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        sub = sub_result.scalar_one_or_none()
        if sub:
            sub.status = "cancelled"
            sub.cancelled_at = datetime.now(timezone.utc)

        logger.info(f"Subscription deleted for user {user.id}, downgraded to free")

    async def _handle_payment_succeeded(self, event: Any, db: AsyncSession) -> None:
        """Handle invoice.payment_succeeded event."""
        invoice = event.data.object
        customer_id = invoice.customer

        # Find user
        result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
        user = result.scalar_one_or_none()

        if user:
            user.subscription_status = "active"
            logger.info(f"Payment succeeded for user {user.id}")

    async def _handle_payment_failed(self, event: Any, db: AsyncSession) -> None:
        """Handle invoice.payment_failed event."""
        invoice = event.data.object
        customer_id = invoice.customer

        # Find user
        result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
        user = result.scalar_one_or_none()

        if user:
            user.subscription_status = "past_due"
            logger.warning(f"Payment failed for user {user.id}")

    async def _update_subscription_from_stripe(
        self,
        stripe_sub: Any,
        db: AsyncSession,
    ) -> None:
        """Update local subscription from Stripe subscription object."""
        customer_id = stripe_sub.customer
        user_id = int(stripe_sub.metadata.get("user_id", 0))

        # Find user
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
        else:
            result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"No user found for subscription update (customer: {customer_id})")
            return

        # Determine tier from price ID
        price_id = stripe_sub.items.data[0].price.id if stripe_sub.items.data else None
        tier = self._get_tier_from_price_id(price_id)

        # Determine status
        status = stripe_sub.status
        if status == "active":
            status = "active"
        elif status == "trialing":
            status = "trialing"
        elif status in ("past_due", "unpaid"):
            status = "past_due"
        elif status in ("canceled", "cancelled"):
            status = "cancelled"
        else:
            status = "active"

        # Update user
        user.subscription_tier = tier
        user.subscription_status = status

        # Update or create subscription record
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        sub = sub_result.scalar_one_or_none()

        if not sub:
            sub = Subscription(
                user_id=user.id,
                stripe_customer_id=customer_id,
            )
            db.add(sub)

        sub.stripe_subscription_id = stripe_sub.id
        sub.stripe_price_id = price_id
        sub.tier = tier
        sub.status = status
        sub.current_period_start = datetime.fromtimestamp(stripe_sub.current_period_start, tz=timezone.utc)
        sub.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end, tz=timezone.utc)
        sub.cancel_at_period_end = stripe_sub.cancel_at_period_end

        if stripe_sub.trial_end:
            sub.trial_end = datetime.fromtimestamp(stripe_sub.trial_end, tz=timezone.utc)

        logger.info(f"Updated subscription for user {user.id}: tier={tier}, status={status}")

    def _get_tier_from_price_id(self, price_id: Optional[str]) -> str:
        """Get tier name from Stripe price ID."""
        if not price_id:
            return "free"
        # New unlimited subscription
        if price_id == settings.STRIPE_PRICE_ID_UNLIMITED:
            return "unlimited"
        # Legacy support
        if price_id == settings.STRIPE_PRICE_ID_TEAM:
            return "unlimited"
        if price_id == settings.STRIPE_PRICE_ID_PRO:
            return "unlimited"  # Migrate old pro to unlimited
        return "free"

    async def _has_had_trial(self, user: User, db: AsyncSession) -> bool:
        """Check if user has ever had a trial."""
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.trial_start.isnot(None),
            )
        )
        return result.scalar_one_or_none() is not None
