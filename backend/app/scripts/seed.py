#!/usr/bin/env python3
"""Database seed script for development and testing.

This script populates the database with realistic test data for all models.
It is idempotent - safe to run multiple times without creating duplicates.

Usage:
    # From backend directory
    python -m app.scripts.seed

    # With options
    python -m app.scripts.seed --clean        # Clear existing data first
    python -m app.scripts.seed --minimal      # Create minimal seed data
    python -m app.scripts.seed --verbose      # Show detailed output

Environment:
    DATABASE_URL: PostgreSQL connection string (required)
"""

import argparse
import asyncio
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine, Base
from app.models import (
    User,
    Subscription,
    UsageRecord,
    GitHubProfile,
    Recommendation,
    ApiKey,
)
from app.scripts.factories import (
    create_user_data,
    create_subscription_data,
    create_github_profile_data,
    create_recommendation_data,
    create_usage_record_data,
    create_api_key_data,
    SEED_USERS,
    SEED_GITHUB_PROFILES,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """Database seeder with idempotent operations."""

    def __init__(self, session: AsyncSession, verbose: bool = False):
        self.session = session
        self.verbose = verbose
        self.stats = {
            "users_created": 0,
            "users_skipped": 0,
            "subscriptions_created": 0,
            "github_profiles_created": 0,
            "github_profiles_skipped": 0,
            "recommendations_created": 0,
            "usage_records_created": 0,
            "api_keys_created": 0,
        }

    def log(self, message: str, level: str = "info") -> None:
        """Log message based on verbosity."""
        if self.verbose or level in ("warning", "error"):
            getattr(logger, level)(message)

    async def seed_users(self) -> dict[str, User]:
        """Seed users and return mapping of username to User object."""
        users = {}

        for user_config in SEED_USERS:
            # Make a copy to avoid modifying the original
            config = user_config.copy()

            # Check if user exists
            result = await self.session.execute(
                select(User).where(User.email == config["email"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                self.log(f"User {config['email']} already exists, skipping")
                self.stats["users_skipped"] += 1
                users[config["username"]] = existing
                continue

            # Create user data
            stripe_customer_id = f"cus_seed_{config['username']}"

            user_data = create_user_data(
                stripe_customer_id=stripe_customer_id,
                **config,
            )

            user = User(**user_data)
            self.session.add(user)
            await self.session.flush()  # Get ID

            users[config["username"]] = user
            self.stats["users_created"] += 1
            tier_info = f"tier={user.subscription_tier}, credits={user.credits}"
            self.log(f"Created user: {user.email} ({tier_info})")

            # Create subscription for unlimited subscribers
            if config.get("subscription_tier") == "unlimited":
                await self._create_subscription(user)

            # Create API key for users with API access (subscribers or 50+ credits purchased)
            if user.can_use_api:
                await self._create_api_key(user)

        return users

    async def _create_subscription(self, user: User) -> None:
        """Create subscription for a user."""
        sub_data = create_subscription_data(
            user_id=user.id,
            stripe_customer_id=user.stripe_customer_id,
            tier=user.subscription_tier,
            stripe_subscription_id=f"sub_seed_{user.username}",
            stripe_price_id="price_seed_unlimited",
        )

        subscription = Subscription(**sub_data)
        self.session.add(subscription)
        self.stats["subscriptions_created"] += 1
        self.log(f"  Created subscription: {user.subscription_tier}")

    async def _create_api_key(self, user: User) -> None:
        """Create API key for a user."""
        key_data = create_api_key_data(
            user_id=user.id,
            name=f"{user.username}'s API Key",
        )

        # Remove raw key before creating model
        raw_key = key_data.pop("_raw_key")

        api_key = ApiKey(**key_data)
        self.session.add(api_key)
        self.stats["api_keys_created"] += 1
        self.log(f"  Created API key: {key_data['key_prefix']}... (raw: {raw_key})")

    async def seed_github_profiles(
        self, users: dict[str, User]
    ) -> dict[str, GitHubProfile]:
        """Seed GitHub profiles and return mapping of username to profile."""
        profiles = {}

        for profile_config in SEED_GITHUB_PROFILES:
            github_username = profile_config["github_username"]

            # Check if profile exists
            result = await self.session.execute(
                select(GitHubProfile).where(
                    GitHubProfile.github_username == github_username
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                self.log(f"GitHub profile {github_username} already exists, skipping")
                self.stats["github_profiles_skipped"] += 1
                profiles[github_username] = existing
                continue

            profile_data = create_github_profile_data(**profile_config)
            profile = GitHubProfile(**profile_data)
            self.session.add(profile)
            await self.session.flush()

            profiles[github_username] = profile
            self.stats["github_profiles_created"] += 1
            self.log(f"Created GitHub profile: {github_username}")

        return profiles

    async def seed_recommendations(
        self, users: dict[str, User], profiles: dict[str, GitHubProfile]
    ) -> None:
        """Seed recommendations linking users to GitHub profiles."""
        # Create recommendations for different combinations
        recommendation_configs = [
            {
                "user": "admin",
                "profile": "torvalds",
                "type": "technical",
                "tone": "professional",
            },
            {
                "user": "subscriber",
                "profile": "octocat",
                "type": "professional",
                "tone": "professional",
            },
            {
                "user": "propack",
                "profile": "gaearon",
                "type": "technical",
                "tone": "friendly",
            },
            {
                "user": "starter",
                "profile": "sindresorhus",
                "type": "leadership",
                "tone": "professional",
            },
            {
                "user": "freeuser",
                "profile": "addyosmani",
                "type": "professional",
                "tone": "casual",
            },
        ]

        for config in recommendation_configs:
            user = users.get(config["user"])
            profile = profiles.get(config["profile"])

            if not user or not profile:
                self.log(
                    f"Skipping recommendation: user={config['user']}, profile={config['profile']}",
                    "warning",
                )
                continue

            rec_data = create_recommendation_data(
                github_profile_id=profile.id,
                user_id=user.id,
                recommendation_type=config["type"],
                tone=config["tone"],
            )

            recommendation = Recommendation(**rec_data)
            self.session.add(recommendation)
            self.stats["recommendations_created"] += 1
            self.log(
                f"Created recommendation: {user.username} -> {profile.github_username}"
            )

    async def seed_usage_records(self, users: dict[str, User]) -> None:
        """Seed usage records for the past 7 days."""
        today = date.today()

        for username, user in users.items():
            # Create usage records for past 7 days
            for days_ago in range(7):
                usage_date = today - timedelta(days=days_ago)

                # Vary usage based on tier
                tier_usage = {
                    "free": 2,
                    "pro": 8,
                    "team": 15,
                }
                base_count = tier_usage.get(user.subscription_tier, 2)

                # Add some variance
                count = max(1, base_count - days_ago)

                usage_data = create_usage_record_data(
                    user_id=user.id,
                    usage_date=usage_date,
                    generation_count=count,
                    tier=user.subscription_tier,
                )

                usage = UsageRecord(**usage_data)
                self.session.add(usage)
                self.stats["usage_records_created"] += 1

            self.log(f"Created 7 usage records for: {username}")

    async def clean_database(self) -> None:
        """Remove all seeded data (use with caution)."""
        logger.warning("Cleaning database - removing seed data...")

        # Delete in reverse order of dependencies
        tables = [
            UsageRecord,
            ApiKey,
            Recommendation,
            Subscription,
            GitHubProfile,
            User,
        ]

        for model in tables:
            result = await self.session.execute(delete(model))
            logger.info(f"Deleted {result.rowcount} rows from {model.__tablename__}")

        await self.session.commit()
        logger.info("Database cleaned successfully")

    async def run(self, clean: bool = False, minimal: bool = False) -> None:
        """Run the seeder.

        Args:
            clean: If True, clean existing data before seeding
            minimal: If True, create minimal seed data
        """
        try:
            if clean:
                await self.clean_database()

            logger.info("Starting database seeding...")

            # Seed in dependency order
            users = await self.seed_users()

            if not minimal:
                profiles = await self.seed_github_profiles(users)
                await self.seed_recommendations(users, profiles)
                await self.seed_usage_records(users)
            else:
                logger.info("Minimal mode: skipping GitHub profiles, recommendations, and usage records")

            await self.session.commit()

            # Print summary
            logger.info("=" * 50)
            logger.info("Seeding completed successfully!")
            logger.info("=" * 50)
            for key, value in self.stats.items():
                if value > 0:
                    logger.info(f"  {key.replace('_', ' ').title()}: {value}")
            logger.info("=" * 50)

            # Print test credentials
            logger.info("\nTest Credentials (password: password123):")
            logger.info("-" * 60)
            logger.info(f"  {'Email':30} {'Tier':12} {'Credits':8}")
            logger.info("-" * 60)
            for user_config in SEED_USERS:
                tier = user_config.get("subscription_tier", "free")
                credits = user_config.get("credits", 3)
                pack = user_config.get("last_credit_pack", "")
                tier_display = tier if tier != "free" else (pack or "free")
                logger.info(f"  {user_config['email']:30} {tier_display:12} {credits:8}")

        except Exception as e:
            logger.error(f"Seeding failed: {e}")
            await self.session.rollback()
            raise


async def main(args: argparse.Namespace) -> None:
    """Main entry point."""
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    async with AsyncSessionLocal() as session:
        seeder = DatabaseSeeder(session, verbose=args.verbose)
        await seeder.run(clean=args.clean, minimal=args.minimal)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed the database with test data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m app.scripts.seed              # Run with default data
    python -m app.scripts.seed --clean      # Clear existing data first
    python -m app.scripts.seed --minimal    # Create only users and profiles
    python -m app.scripts.seed --verbose    # Show detailed output

Test Credentials:
    All seeded users have password: password123
        """,
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean existing seed data before seeding",
    )

    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Create minimal seed data (users and profiles only)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Show only warnings and errors",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
