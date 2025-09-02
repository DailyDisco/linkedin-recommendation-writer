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
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    REDIS_TIMEOUT: int = Field(default=5, ge=1, le=30, description="Redis timeout in seconds")
    REDIS_DEFAULT_TTL: int = Field(default=3600, ge=60, le=86400, description="Default cache TTL")

    # External APIs
    GITHUB_TOKEN: str = Field(default="", description="GitHub API token")
    GITHUB_RATE_LIMIT: int = Field(default=5000, ge=1000, le=15000, description="GitHub API rate limit")

    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash-lite", description="Gemini model name")
    GEMINI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0, description="Gemini temperature")
    GEMINI_MAX_TOKENS: int = Field(default=2048, ge=100, le=8192, description="Gemini max tokens")

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="DEBUG", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )

    # Initialization flags
    INIT_DB: bool = Field(default=True, description="Initialize database on startup")
    RUN_MIGRATIONS: bool = Field(default=False, description="Run database migrations on startup")

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
    ENABLE_METRICS: bool = Field(default=False, description="Enable metrics collection")
    ENABLE_TRACING: bool = Field(default=False, description="Enable request tracing")

    @computed_field
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        if not self.ALLOWED_ORIGINS.strip():
            return []
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @computed_field
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @computed_field
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"

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
