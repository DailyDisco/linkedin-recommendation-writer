"""Custom middleware for the application."""

import logging
import time
import uuid
from typing import Any, Awaitable, Callable, Dict

from fastapi import Request, Response
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BaseApplicationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.core.security_config import security_utils

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
    """Log request and response details with PII filtering."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")

        # Sanitize URL and query parameters for logging
        safe_url = security_utils.filter_pii_for_logging(str(request.url))
        safe_client = request.client.host if request.client else "unknown"

        # Log request
        logger.info(f"Request started - ID: {request_id}, Method: {request.method}, " f"URL: {safe_url}, Client: {safe_client}")

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            logger.info(f"Request completed - ID: {request_id}, Status: {response.status_code}, " f"Duration: {duration:.3f}s")

            return response

        except Exception as e:
            duration = time.time() - start_time
            safe_error = security_utils.filter_pii_for_logging(str(e))
            logger.error(
                f"Request failed - ID: {request_id}, Error: {safe_error}, " f"Duration: {duration:.3f}s",
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
    """Centralized error handling middleware with support for custom exceptions."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        try:
            return await call_next(request)
        except BaseApplicationError as e:
            # Handle custom application exceptions
            return await self._handle_application_error(e, request)
        except ValueError as e:
            # Handle standard Python ValueError
            logger.warning(f"Validation error: {security_utils.filter_pii_for_logging(str(e))}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "VALIDATION_ERROR",
                    "message": "The provided data is invalid. Please check your input and try again.",
                    "type": "validation_error",
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            )
        except ConnectionError as e:
            # Handle connection errors
            logger.error(f"Connection error: {security_utils.filter_pii_for_logging(str(e))}")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "EXTERNAL_SERVICE_ERROR",
                    "message": "Service temporarily unavailable. Please try again later.",
                    "type": "connection_error",
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            )
        except TimeoutError as e:
            # Handle timeout errors
            logger.error(f"Timeout error: {security_utils.filter_pii_for_logging(str(e))}")
            return JSONResponse(
                status_code=504,
                content={
                    "error": "EXTERNAL_SERVICE_ERROR",
                    "message": "Request timeout. The server is taking longer than expected to respond.",
                    "type": "timeout_error",
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            )
        except Exception as e:
            # Handle any other unhandled exceptions
            request_id = getattr(request.state, "request_id", "unknown")
            safe_error = security_utils.filter_pii_for_logging(str(e))
            logger.error(f"Unhandled error in request {request_id}: {safe_error}", exc_info=True)

            if settings.API_DEBUG:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "INTERNAL_ERROR",
                        "message": "An internal server error occurred.",
                        "detail": safe_error,
                        "type": "internal_error",
                        "request_id": request_id,
                    },
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "INTERNAL_ERROR",
                        "message": "Internal server error. Please try again later.",
                        "type": "internal_error",
                        "request_id": request_id,
                    },
                )

    async def _handle_application_error(self, error: BaseApplicationError, request: Request) -> JSONResponse:
        """Handle custom application exceptions with proper error mapping."""
        request_id = getattr(request.state, "request_id", "unknown")

        # Determine HTTP status code based on error type
        status_code = self._get_status_code_for_error(error)

        # Log the error with appropriate level
        safe_message = error.get_safe_message()
        if isinstance(error, (ValidationError, NotFoundError)):
            logger.warning(f"Application error in request {request_id}: {safe_message}")
        else:
            logger.error(f"Application error in request {request_id}: {safe_message}", exc_info=True)

        # Prepare response content
        response_content = {
            "error": error.error_code,
            "message": error.get_user_friendly_message(),
            "type": error.__class__.__name__.lower(),
            "request_id": request_id,
        }

        # Include additional details for certain error types in debug mode
        if settings.API_DEBUG and hasattr(error, "details") and error.details:
            # Sanitize details before including
            safe_details = {}
            for key, value in error.details.items():
                if isinstance(value, str):
                    safe_details[key] = security_utils.filter_pii_for_logging(value)
                else:
                    safe_details[key] = value
            response_content["details"] = safe_details

        return JSONResponse(
            status_code=status_code,
            content=response_content,
        )

    def _get_status_code_for_error(self, error: BaseApplicationError) -> int:
        """Map error types to appropriate HTTP status codes."""
        if isinstance(error, AuthenticationError):
            return status.HTTP_401_UNAUTHORIZED
        elif isinstance(error, AuthorizationError):
            return status.HTTP_403_FORBIDDEN
        elif isinstance(error, RateLimitError):
            return status.HTTP_429_TOO_MANY_REQUESTS
        elif isinstance(error, NotFoundError):
            return status.HTTP_404_NOT_FOUND
        else:
            return status.HTTP_500_INTERNAL_SERVER_ERROR
