"""Usage service for tracking and managing usage."""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import List

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage_record import UsageRecord
from app.models.user import User
from app.schemas.billing import UsageHistoryItem, UsageResponse

logger = logging.getLogger(__name__)


class UsageService:
    """Service for tracking and managing usage."""

    async def get_usage(
        self,
        user: User,
        db: AsyncSession,
    ) -> UsageResponse:
        """Get usage statistics for a user.

        Args:
            user: User to get usage for
            db: Database session

        Returns:
            UsageResponse with usage statistics
        """
        today = date.today()
        now = datetime.now(timezone.utc)

        # Get today's usage
        generations_used = user.recommendation_count or 0

        # Check if count should be reset (new day)
        if user.last_recommendation_date:
            last_date = user.last_recommendation_date
            if hasattr(last_date, 'date'):
                last_date = last_date.date()
            if last_date < today:
                generations_used = 0

        # Get limits
        tier = user.effective_tier
        limit = user.effective_daily_limit

        # Calculate remaining
        if limit == -1:
            remaining = -1  # Unlimited
        else:
            remaining = max(0, limit - generations_used)

        # Calculate reset time (midnight UTC)
        tomorrow = datetime.combine(
            today + timedelta(days=1),
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

        # Get history for last 30 days
        history = await self._get_usage_history(user, db, days=30)

        # Period is daily for now
        period_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
        period_end = tomorrow

        return UsageResponse(
            tier=tier,
            period_start=period_start,
            period_end=period_end,
            generations_used=generations_used,
            generations_limit=limit,
            generations_remaining=remaining,
            resets_at=tomorrow,
            history=history,
        )

    async def record_usage(
        self,
        user: User,
        db: AsyncSession,
    ) -> None:
        """Record a generation for usage tracking.

        This is called after a successful generation.
        It updates both the user's daily count and the usage_records table.

        Args:
            user: User who generated
            db: Database session
        """
        today = date.today()

        # Update or create usage record
        result = await db.execute(
            select(UsageRecord).where(
                and_(
                    UsageRecord.user_id == user.id,
                    UsageRecord.date == today,
                )
            )
        )
        record = result.scalar_one_or_none()

        if record:
            record.generation_count += 1
        else:
            record = UsageRecord(
                user_id=user.id,
                date=today,
                generation_count=1,
                tier=user.effective_tier,
            )
            db.add(record)

        await db.commit()
        logger.debug(f"Recorded usage for user {user.id}: {record.generation_count} today")

    async def check_can_generate(
        self,
        user: User,
        db: AsyncSession,
    ) -> tuple[bool, int, str]:
        """Check if user can generate a recommendation.

        Args:
            user: User to check
            db: Database session

        Returns:
            Tuple of (can_generate, remaining, error_message)
        """
        usage = await self.get_usage(user, db)

        # Unlimited tier
        if usage.generations_limit == -1:
            return True, -1, ""

        # Check limit
        if usage.generations_remaining <= 0:
            return False, 0, f"Daily generation limit ({usage.generations_limit}) exceeded"

        return True, usage.generations_remaining, ""

    async def _get_usage_history(
        self,
        user: User,
        db: AsyncSession,
        days: int = 30,
    ) -> List[UsageHistoryItem]:
        """Get usage history for a user.

        Args:
            user: User to get history for
            db: Database session
            days: Number of days of history

        Returns:
            List of UsageHistoryItem
        """
        start_date = date.today() - timedelta(days=days)

        result = await db.execute(
            select(UsageRecord)
            .where(
                and_(
                    UsageRecord.user_id == user.id,
                    UsageRecord.date >= start_date,
                )
            )
            .order_by(UsageRecord.date.desc())
        )
        records = result.scalars().all()

        return [
            UsageHistoryItem(date=r.date, count=r.generation_count)
            for r in records
        ]

    async def get_total_usage(
        self,
        user: User,
        db: AsyncSession,
    ) -> int:
        """Get total lifetime usage for a user.

        Args:
            user: User to get total for
            db: Database session

        Returns:
            Total generation count
        """
        result = await db.execute(
            select(func.sum(UsageRecord.generation_count))
            .where(UsageRecord.user_id == user.id)
        )
        total = result.scalar() or 0
        return total

    async def reset_daily_count(
        self,
        user: User,
        db: AsyncSession,
    ) -> None:
        """Reset user's daily recommendation count.

        Called when a new day starts.

        Args:
            user: User to reset
            db: Database session
        """
        user.recommendation_count = 0
        user.last_recommendation_date = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Reset daily count for user {user.id}")
