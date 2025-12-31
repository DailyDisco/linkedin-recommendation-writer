"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List, Literal

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with comprehensive validation and typing."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(default="development", description="Application environment")

    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", description="API host address")
    API_PORT: int = Field(default=8000, ge=1000, le=65535, description="API port")
    API_DEBUG: bool = Field(default=False, description="Enable debug mode")
    API_RELOAD: bool = Field(default=True, description="Enable auto-reload")
    API_WORKERS: int = Field(default=1, ge=1, le=8, description="Number of worker processes")

    # Database Configuration
    DATABASE_URL: str = Field(
        default=("postgresql+asyncpg://postgres:password@localhost:5432/" "github_recommender"),
        description="Database connection URL",
    )
    DATABASE_POOL_SIZE: int = Field(default=10, ge=5, le=50, description="Database pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=10, le=100, description="Database pool max overflow")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=5, le=120, description="Database pool timeout")

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://redis:6379/0", description="Redis connection URL")
    REDIS_TIMEOUT: int = Field(default=5, ge=1, le=30, description="Redis timeout in seconds")
    REDIS_DEFAULT_TTL: int = Field(default=3600, ge=60, le=86400, description="Default cache TTL")

    # External APIs
    GITHUB_TOKEN: str = Field(default="", description="GitHub API token")
    GITHUB_RATE_LIMIT: int = Field(default=5000, ge=1000, le=15000, description="GitHub API rate limit")

    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash-lite", description="Gemini model name")
    GEMINI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0, description="Gemini temperature")
    GEMINI_MAX_TOKENS: int = Field(default=2048, ge=100, le=8192, description="Gemini max tokens")

    # AI Quality Settings
    AI_QUALITY_TIER: Literal["fast", "balanced", "quality"] = Field(
        default="balanced",
        description="AI quality tier: fast (gemini-2.5-flash-lite), balanced (gemini-2.0-flash), quality (gemini-1.5-pro)"
    )
    AI_ENABLE_QUALITY_GATE: bool = Field(
        default=True,
        description="Enable quality gate with automatic retry for low-quality outputs"
    )
    AI_QUALITY_GATE_MIN_SCORE: int = Field(
        default=65,
        ge=0,
        le=100,
        description="Minimum quality score required (0-100)"
    )
    AI_QUALITY_GATE_MAX_RETRIES: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum retry attempts for quality gate"
    )
    AI_PARALLEL_GENERATION: bool = Field(
        default=True,
        description="Enable parallel option generation for faster response"
    )

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="DEBUG", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )

    # Initialization flags
    INIT_DB: bool = Field(default=True, description="Initialize database on startup")
    RUN_MIGRATIONS: bool = Field(default=True, description="Run database migrations on startup")

    # CORS Configuration
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:5174,http://127.0.0.1:3000,http://127.0.0.1:5173,https://linkedin-recommendation-writer-production.up.railway.app",
        description="Comma-separated list of allowed CORS origins",
    )

    # Security
    SECRET_KEY: str = Field(
        description="Secret key for security operations",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=120, ge=1, description="Access token expiration in minutes")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=120,
        ge=10,
        le=1000,
        description="Rate limit requests per minute",
    )
    RATE_LIMIT_BURST_SIZE: int = Field(default=30, ge=1, le=100, description="Rate limit burst size")

    # Feature Flags
    ENABLE_RATE_LIMITING: bool = Field(default=True, description="Enable API rate limiting")

    # Admin Configuration
    ADMIN_EMAILS: str = Field(default="", description="Comma-separated list of admin email addresses")

    # Stripe Configuration
    STRIPE_SECRET_KEY: str = Field(default="", description="Stripe secret API key")
    STRIPE_PUBLISHABLE_KEY: str = Field(default="", description="Stripe publishable API key")
    STRIPE_WEBHOOK_SECRET: str = Field(default="", description="Stripe webhook signing secret")

    # Credit Pack Price IDs (one-time purchases)
    STRIPE_PRICE_ID_STARTER: str = Field(default="", description="Stripe Price ID for Starter pack (10 credits)")
    STRIPE_PRICE_ID_PRO_PACK: str = Field(default="", description="Stripe Price ID for Pro pack (50 credits)")

    # Subscription Price ID
    STRIPE_PRICE_ID_UNLIMITED: str = Field(default="", description="Stripe Price ID for Unlimited monthly")

    # Legacy (deprecated)
    STRIPE_PRICE_ID_PRO: str = Field(default="", description="[Deprecated] Use STRIPE_PRICE_ID_PRO_PACK")
    STRIPE_PRICE_ID_TEAM: str = Field(default="", description="[Deprecated] Use STRIPE_PRICE_ID_UNLIMITED")
    STRIPE_TRIAL_DAYS: int = Field(default=7, ge=0, le=30, description="Trial period in days")

    # Billing Feature Flags
    BILLING_ENABLED: bool = Field(default=True, description="Enable billing features")

    @computed_field
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        if not self.ALLOWED_ORIGINS.strip():
            return []
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @computed_field
    def admin_emails(self) -> List[str]:
        """Get admin emails as a list."""
        if not self.ADMIN_EMAILS.strip():
            return []
        return [email.strip().lower() for email in self.ADMIN_EMAILS.split(",")]

    @computed_field
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @computed_field
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"

    @computed_field
    def recommended_model(self) -> str:
        """Get recommended Gemini model based on quality tier.

        Quality tiers:
        - fast: gemini-2.5-flash-lite (cheapest, fastest, good for testing)
        - balanced: gemini-2.0-flash (good balance of quality and speed)
        - quality: gemini-1.5-pro (highest quality, slower, more expensive)
        """
        tier_models = {
            "fast": "gemini-2.5-flash-lite",
            "balanced": "gemini-2.0-flash",
            "quality": "gemini-1.5-pro",
        }
        return tier_models.get(self.AI_QUALITY_TIER, self.GEMINI_MODEL)

    @computed_field
    def recommended_temperature(self) -> float:
        """Get recommended temperature based on quality tier.

        Higher quality tiers use slightly lower temperature for more consistency.
        """
        tier_temps = {
            "fast": 0.8,      # More creative, faster iteration
            "balanced": 0.7,  # Good balance
            "quality": 0.6,   # More consistent, higher quality
        }
        return tier_temps.get(self.AI_QUALITY_TIER, self.GEMINI_TEMPERATURE)

    def get_dynamic_temperature(self, recommendation_type: str, tone: str) -> float:
        """Get dynamic temperature based on recommendation type and tone.

        Args:
            recommendation_type: Type of recommendation (professional, technical, etc.)
            tone: Tone of recommendation (professional, casual, friendly, formal)

        Returns:
            Adjusted temperature value
        """
        base_temp = self.recommended_temperature

        # Tone adjustments
        tone_adjustments = {
            "professional": -0.1,  # More consistent
            "formal": -0.15,       # Very consistent
            "casual": +0.15,       # More creative
            "friendly": +0.1,      # Slightly more creative
        }

        # Type adjustments
        type_adjustments = {
            "technical": -0.1,     # More precise
            "professional": -0.05,
            "leadership": +0.05,   # More inspiring
            "academic": -0.1,      # More formal
            "personal": +0.1,      # More creative
        }

        temp = base_temp
        temp += tone_adjustments.get(tone, 0)
        temp += type_adjustments.get(recommendation_type, 0)

        # Clamp to valid range
        return max(0.3, min(1.5, temp))

    @field_validator("GITHUB_TOKEN")
    @classmethod
    def validate_github_token(cls, v: str) -> str:
        """Validate GitHub token format."""
        if v and not v.startswith(("ghp_", "github_pat_")):
            raise ValueError('GitHub token should start with "ghp_" or "github_pat_"')
        return v

    @field_validator("GEMINI_API_KEY")
    @classmethod
    def validate_gemini_key(cls, v: str) -> str:
        """Validate Gemini API key format."""
        if v and not v.startswith("AIza"):
            raise ValueError('Gemini API key should start with "AIza"')
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key length and format."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format and ensure asyncpg driver is used."""
        if v.startswith("postgresql://"):
            # Convert plain postgresql:// to postgresql+asyncpg://
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif not v.startswith("postgresql+asyncpg://"):
            raise ValueError("Database URL must use postgresql or postgresql+asyncpg scheme")
        return v

    def get_database_config(self) -> dict:
        """Get database configuration dictionary."""
        return {
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "pool_timeout": self.DATABASE_POOL_TIMEOUT,
            "pool_recycle": 3600,
            "echo": self.API_DEBUG,
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
