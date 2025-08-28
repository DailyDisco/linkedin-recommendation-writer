"""Custom middleware for the application."""

import logging
import time
import uuid
from typing import Callable, Dict, Any, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request for tracing."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log request and response details."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")

        # Log request
        logger.info(
            f"Request started - ID: {request_id}, Method: {request.method}, "
            f"URL: {request.url}, Client: {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            logger.info(f"Request completed - ID: {request_id}, Status: {response.status_code}, " f"Duration: {duration:.3f}s")

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed - ID: {request_id}, Error: {str(e)}, " f"Duration: {duration:.3f}s",
                exc_info=True,
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app: Any, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, int] = {}  # In production, use Redis

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if not settings.ENABLE_RATE_LIMITING:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time() / 60)  # Current minute

        # Clean old entries
        self.requests = {k: v for k, v in self.requests.items() if int(k.split(":")[1]) >= current_time - 1}

        # Count requests for this client in current minute
        key = f"{client_ip}:{current_time}"
        count = self.requests.get(key, 0)

        if count >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": "60"},
            )

        self.requests[key] = count + 1
        return await call_next(request)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Centralized error handling middleware."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        try:
            return await call_next(request)
        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            return JSONResponse(
                status_code=400,
                content={"detail": str(e), "type": "validation_error"},
            )
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Service temporarily unavailable",
                    "type": "connection_error",
                },
            )
        except TimeoutError as e:
            logger.error(f"Timeout error: {e}")
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timeout", "type": "timeout_error"},
            )
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(f"Unhandled error in request {request_id}: {e}", exc_info=True)

            if settings.API_DEBUG:
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": str(e),
                        "type": "internal_error",
                        "request_id": request_id,
                    },
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Internal server error",
                        "type": "internal_error",
                        "request_id": request_id,
                    },
                )
