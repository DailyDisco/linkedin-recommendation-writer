"""Simplified middleware setup - JWT auth and basic security only."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    RateLimitingMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)


def setup_middleware(app: FastAPI) -> None:
    """Configure essential middleware only.
    
    Middleware execution order (reverse of addition):
    1. RequestIDMiddleware - Generate request IDs
    2. LoggingMiddleware - Log requests/responses
    3. SecurityHeadersMiddleware - Basic security headers
    4. ErrorHandlingMiddleware - Handle errors
    5. RateLimitingMiddleware - Rate limiting (if enabled)
    6. CORSMiddleware - CORS handling
    """
    
    # CORS middleware (must be added first to execute last)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        max_age=86400,  # 24 hours cache for preflight
    )

    # Rate limiting (optional, controlled by settings)
    if settings.ENABLE_RATE_LIMITING:
        app.add_middleware(
            RateLimitingMiddleware,
            requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        )

    # Core middleware (executed in reverse order)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
