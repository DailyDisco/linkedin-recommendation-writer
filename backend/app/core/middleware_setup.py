"""Middleware setup and configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.csrf_protection import APICSRFProtectionMiddleware, CSRFProtectionMiddleware
from app.core.middleware import ErrorHandlingMiddleware, LoggingMiddleware, RateLimitingMiddleware, RequestIDMiddleware
from app.core.security_middleware import (
    EnhancedSecurityHeadersMiddleware,
    InputSanitizationMiddleware,
    PIIFilteringMiddleware,
    RequestSizeLimitMiddleware,
)


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the FastAPI application.

    Note: Middleware is executed in reverse order of addition.
    Last added middleware is executed first.
    """
    # CORS middleware (must be added first to execute last)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Add custom middleware (order matters - last added is executed first)
    # Security middlewares (executed in reverse order)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(APICSRFProtectionMiddleware)  # API-specific CSRF protection
    app.add_middleware(CSRFProtectionMiddleware)  # General CSRF protection
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(InputSanitizationMiddleware)
    app.add_middleware(PIIFilteringMiddleware)
    app.add_middleware(EnhancedSecurityHeadersMiddleware)  # Replace old SecurityHeadersMiddleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Rate limiting middleware
    if settings.ENABLE_RATE_LIMITING:
        app.add_middleware(
            RateLimitingMiddleware,
            requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        )
