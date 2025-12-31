"""Data factories for generating consistent seed data.

This module provides factory functions for creating realistic test data
for all models in the application.
"""

import hashlib
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any

# Password hash for "password123" using bcrypt-style format
# In production, use passlib to generate proper hashes
DEFAULT_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G4Ig4YGfgKz3mu"


def create_user_data(
    email: str | None = None,
    username: str | None = None,
    full_name: str | None = None,
    role: str = "free",
    subscription_tier: str = "free",
    is_active: bool = True,
    stripe_customer_id: str | None = None,
    credits: int = 3,
    lifetime_credits_purchased: int = 0,
    last_credit_pack: str | None = None,
) -> dict[str, Any]:
    """Create user data dictionary.

    Args:
        email: User email (generated if not provided)
        username: Username (generated from email if not provided)
        full_name: Full name
        role: User role (free, admin)
        subscription_tier: Subscription tier (free, unlimited)
        is_active: Whether user is active
        stripe_customer_id: Stripe customer ID
        credits: Credit balance (default 3 for new users)
        lifetime_credits_purchased: Total credits ever purchased
        last_credit_pack: Last credit pack purchased (starter, pro)

    Returns:
        Dictionary of user data
    """
    if email is None:
        random_suffix = secrets.token_hex(4)
        email = f"user_{random_suffix}@example.com"

    if username is None:
        username = email.split("@")[0]

    return {
        "email": email,
        "username": username,
        "full_name": full_name or username.replace("_", " ").title(),
        "hashed_password": DEFAULT_PASSWORD_HASH,
        "is_active": is_active,
        "role": role,
        "subscription_tier": subscription_tier,
        "subscription_status": "active",
        "stripe_customer_id": stripe_customer_id,
        "recommendation_count": 0,
        "daily_limit": 5,
        "email_notifications_enabled": True,
        "default_tone": "professional",
        "language": "en",
        # Credits system
        "credits": credits,
        "lifetime_credits_purchased": lifetime_credits_purchased,
        "last_credit_pack": last_credit_pack,
    }


def create_subscription_data(
    user_id: int,
    stripe_customer_id: str,
    tier: str = "free",
    status: str = "active",
    stripe_subscription_id: str | None = None,
    stripe_price_id: str | None = None,
    trial_days: int = 0,
) -> dict[str, Any]:
    """Create subscription data dictionary.

    Args:
        user_id: Associated user ID
        stripe_customer_id: Stripe customer ID
        tier: Subscription tier (free, pro, team)
        status: Subscription status (active, past_due, cancelled, trialing)
        stripe_subscription_id: Stripe subscription ID
        stripe_price_id: Stripe price ID
        trial_days: Number of trial days (0 for no trial)

    Returns:
        Dictionary of subscription data
    """
    now = datetime.now(timezone.utc)
    period_start = now
    period_end = now + timedelta(days=30)

    data = {
        "user_id": user_id,
        "stripe_customer_id": stripe_customer_id,
        "stripe_subscription_id": stripe_subscription_id,
        "stripe_price_id": stripe_price_id,
        "tier": tier,
        "status": status,
        "current_period_start": period_start,
        "current_period_end": period_end,
        "cancel_at_period_end": False,
    }

    if trial_days > 0:
        data["trial_start"] = now
        data["trial_end"] = now + timedelta(days=trial_days)
        data["status"] = "trialing"

    return data


def create_github_profile_data(
    github_username: str,
    github_id: int | None = None,
    user_id: int | None = None,
    full_name: str | None = None,
) -> dict[str, Any]:
    """Create GitHub profile data dictionary.

    Args:
        github_username: GitHub username
        github_id: GitHub user ID (generated from username hash if not provided)
        user_id: Associated user ID (optional)
        full_name: Full name

    Returns:
        Dictionary of GitHub profile data
    """
    if github_id is None:
        # Generate consistent ID from username (limit to int32 range: max 2147483647)
        github_id = int(hashlib.md5(github_username.encode()).hexdigest()[:7], 16) % 2000000000

    return {
        "github_username": github_username,
        "github_id": github_id,
        "user_id": user_id,
        "full_name": full_name or github_username.replace("-", " ").title(),
        "bio": f"Software engineer passionate about open source. {github_username}",
        "company": "Tech Company Inc.",
        "location": "San Francisco, CA",
        "email": f"{github_username}@example.com",
        "blog": f"https://{github_username}.dev",
        "avatar_url": f"https://avatars.githubusercontent.com/u/{github_id}",
        "public_repos": 42,
        "followers": 150,
        "following": 75,
        "public_gists": 10,
        "repositories_data": {
            "top_repos": [
                {"name": "awesome-project", "stars": 120, "language": "Python"},
                {"name": "cool-library", "stars": 85, "language": "TypeScript"},
                {"name": "useful-tool", "stars": 45, "language": "Go"},
            ]
        },
        "languages_data": {
            "Python": 45,
            "TypeScript": 30,
            "Go": 15,
            "JavaScript": 10,
        },
        "contribution_data": {
            "total_commits": 1250,
            "total_prs": 89,
            "total_issues": 45,
            "streak_days": 30,
        },
        "skills_analysis": {
            "primary": ["Python", "TypeScript", "Go"],
            "frameworks": ["FastAPI", "React", "Docker"],
            "tools": ["Git", "PostgreSQL", "Redis"],
        },
    }


def create_recommendation_data(
    github_profile_id: int,
    user_id: int | None = None,
    title: str | None = None,
    content: str | None = None,
    recommendation_type: str = "professional",
    tone: str = "professional",
    length: str = "medium",
) -> dict[str, Any]:
    """Create recommendation data dictionary.

    Args:
        github_profile_id: Associated GitHub profile ID
        user_id: Associated user ID (optional)
        title: Recommendation title
        content: Recommendation content
        recommendation_type: Type (professional, technical, leadership)
        tone: Tone (professional, friendly, formal, casual)
        length: Length (short, medium, long)

    Returns:
        Dictionary of recommendation data
    """
    if title is None:
        title = f"LinkedIn Recommendation - {recommendation_type.title()}"

    if content is None:
        content = _generate_sample_recommendation(recommendation_type, tone)

    return {
        "github_profile_id": github_profile_id,
        "user_id": user_id,
        "title": title,
        "content": content,
        "recommendation_type": recommendation_type,
        "tone": tone,
        "length": length,
        "ai_model": "gemini-2.5-flash-lite",
        "word_count": len(content.split()),
        "generation_parameters": {
            "temperature": 0.7,
            "max_tokens": 2048,
        },
    }


def create_usage_record_data(
    user_id: int,
    usage_date: date | None = None,
    generation_count: int = 1,
    tier: str = "free",
) -> dict[str, Any]:
    """Create usage record data dictionary.

    Args:
        user_id: Associated user ID
        usage_date: Date of usage (defaults to today)
        generation_count: Number of generations
        tier: User tier at time of usage

    Returns:
        Dictionary of usage record data
    """
    if usage_date is None:
        usage_date = date.today()

    return {
        "user_id": user_id,
        "date": usage_date,
        "generation_count": generation_count,
        "tier": tier,
    }


def create_api_key_data(
    user_id: int,
    name: str = "Default API Key",
    scopes: list[str] | None = None,
) -> dict[str, Any]:
    """Create API key data dictionary.

    Args:
        user_id: Associated user ID
        name: Key name
        scopes: List of permission scopes

    Returns:
        Dictionary of API key data (includes raw key for display)
    """
    if scopes is None:
        scopes = ["recommendations:read", "recommendations:write"]

    # Generate key - prefix must be max 10 chars to match DB column
    full_key = f"lrw_{secrets.token_urlsafe(32)}"
    key_prefix = full_key[:10]  # "lrw_" + 6 chars = 10 chars
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    return {
        "user_id": user_id,
        "name": name,
        "key_hash": key_hash,
        "key_prefix": key_prefix,
        "scopes": scopes,
        "is_active": True,
        # Not stored in DB, but useful for testing
        "_raw_key": full_key,
    }


def _generate_sample_recommendation(recommendation_type: str, tone: str) -> str:
    """Generate sample recommendation content based on type and tone."""
    templates = {
        ("professional", "professional"): """I had the pleasure of working alongside this talented developer for over two years, and I can confidently say they are one of the most dedicated professionals I've encountered. Their technical expertise in Python and cloud architecture consistently delivered results that exceeded expectations.

What truly sets them apart is their ability to translate complex technical concepts into actionable solutions. They led the migration of our legacy systems to a modern microservices architecture, reducing deployment time by 60% and improving system reliability significantly.

Beyond technical skills, they demonstrated exceptional leadership qualities, mentoring junior developers and fostering a collaborative team environment. I wholeheartedly recommend them for any senior engineering role.""",
        ("technical", "professional"): """As a fellow engineer, I've been consistently impressed by their deep technical knowledge and problem-solving abilities. Their contributions to our open-source projects showcase a rare combination of algorithmic thinking and practical engineering.

They architected our real-time data processing pipeline using Apache Kafka and Python, handling millions of events daily with sub-second latency. Their code reviews were invaluable, always providing constructive feedback that elevated the entire team's capabilities.

Their expertise in distributed systems, combined with a pragmatic approach to software design, makes them an exceptional asset to any engineering organization.""",
        ("leadership", "friendly"): """Working with this person was an absolute joy! Not only are they technically brilliant, but they have this amazing ability to bring out the best in everyone around them.

I watched them transform our team's culture from siloed individual work to true collaboration. They introduced pair programming sessions, created learning opportunities, and always made time to help others grow.

If you're looking for someone who can both ship great code and build great teams, look no further!""",
    }

    key = (recommendation_type, tone)
    if key in templates:
        return templates[key]

    # Default template
    return templates[("professional", "professional")]


# Pre-defined seed data for common scenarios
SEED_USERS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "full_name": "Admin User",
        "role": "admin",
        "subscription_tier": "unlimited",
        "credits": 999,
    },
    {
        "email": "subscriber@example.com",
        "username": "subscriber",
        "full_name": "Unlimited Subscriber",
        "role": "free",
        "subscription_tier": "unlimited",
        "credits": 0,  # Doesn't need credits - has unlimited
    },
    {
        "email": "propack@example.com",
        "username": "propack",
        "full_name": "Pro Pack User",
        "role": "free",
        "subscription_tier": "free",
        "credits": 45,
        "lifetime_credits_purchased": 50,
        "last_credit_pack": "pro",
    },
    {
        "email": "starter@example.com",
        "username": "starter",
        "full_name": "Starter Pack User",
        "role": "free",
        "subscription_tier": "free",
        "credits": 8,
        "lifetime_credits_purchased": 10,
        "last_credit_pack": "starter",
    },
    {
        "email": "free@example.com",
        "username": "freeuser",
        "full_name": "Free User",
        "role": "free",
        "subscription_tier": "free",
        "credits": 3,  # Default free credits
    },
    {
        "email": "empty@example.com",
        "username": "emptyuser",
        "full_name": "No Credits User",
        "role": "free",
        "subscription_tier": "free",
        "credits": 0,  # No credits left
    },
]

SEED_GITHUB_PROFILES = [
    {"github_username": "octocat", "full_name": "The Octocat"},
    {"github_username": "torvalds", "full_name": "Linus Torvalds"},
    {"github_username": "gaearon", "full_name": "Dan Abramov"},
    {"github_username": "sindresorhus", "full_name": "Sindre Sorhus"},
    {"github_username": "addyosmani", "full_name": "Addy Osmani"},
]
