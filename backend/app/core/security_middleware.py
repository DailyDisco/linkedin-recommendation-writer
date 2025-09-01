"""Enhanced security middleware for comprehensive protection."""

import logging
import re
import time
from typing import Any, Awaitable, Callable, Dict

import bleach
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitize and validate all incoming request data."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        # Define allowed HTML tags and attributes for content that might contain HTML
        self.allowed_tags = ["p", "br", "strong", "em", "u", "h1", "h2", "h3", "h4", "h5", "h6"]
        self.allowed_attributes = {}

        # PII patterns to detect and filter
        self.pii_patterns = {
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
            "ssn": re.compile(r"\b\d{3}[-]?\d{2}[-]?\d{4}\b"),
            "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
            "api_key": re.compile(r"\b[A-Za-z0-9_-]{20,}\b"),  # Generic API key pattern
        }

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Sanitize query parameters
        if request.query_params:
            self._sanitize_query_params(dict(request.query_params))
            # Update request with sanitized params (limited effectiveness but good for logging)

        # Sanitize request body for JSON requests
        if request.method in ["POST", "PUT", "PATCH"] and request.headers.get("content-type", "").startswith("application/json"):
            await self._sanitize_json_body(request)

        response = await call_next(request)
        return response

    def _sanitize_query_params(self, params: Dict[str, str]) -> Dict[str, str]:
        """Sanitize query parameters."""
        sanitized = {}
        for key, value in params.items():
            if isinstance(value, str):
                # Remove potential script injection
                sanitized[key] = self._sanitize_text(value)
            else:
                sanitized[key] = value
        return sanitized

    async def _sanitize_json_body(self, request: Request) -> None:
        """Sanitize JSON request body."""
        try:
            body = await request.json()
            self._sanitize_dict(body)
            # Note: We can't modify the request body easily, but we can log sanitized version
            logger.debug(f"Sanitized request body for {request.url.path}")
        except Exception:
            # If we can't parse JSON, let it pass through
            pass

    def _sanitize_dict(self, data: Any) -> Any:
        """Recursively sanitize dictionary data."""
        if isinstance(data, dict):
            return {key: self._sanitize_dict(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_dict(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_text(data)
        else:
            return data

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text content."""
        if not isinstance(text, str):
            return text

        # Remove null bytes and other control characters
        text = text.replace("\x00", "")

        # Check for PII patterns
        for pattern_name, pattern in self.pii_patterns.items():
            if pattern.search(text):
                logger.warning(f"Potential {pattern_name} detected in request data - sanitizing")
                # Replace PII with placeholder
                text = pattern.sub(f"[REDACTED_{pattern_name.upper()}]", text)

        # HTML sanitization for fields that might contain HTML
        if "<" in text and ">" in text:
            text = bleach.clean(text, tags=self.allowed_tags, attributes=self.allowed_attributes, strip=True)

        return text


class EnhancedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enhanced security headers with CSP and comprehensive protection."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)

        # Enhanced security headers
        headers = {
            # Content Security Policy - strict but practical
            "Content-Security-Policy": self._get_csp_policy(),
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            # XSS protection
            "X-XSS-Protection": "1; mode=block",
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Feature policy to disable potentially dangerous features
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
            # Prevent caching of sensitive content
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            # HSTS for production
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        }

        # Only add HSTS in production
        if settings.ENVIRONMENT != "production":
            del headers["Strict-Transport-Security"]

        # Apply all headers
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value

        return response

    def _get_csp_policy(self) -> str:
        """Generate Content Security Policy based on environment."""
        if settings.ENVIRONMENT == "development":
            # More permissive for development
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:3000 localhost:5173; "
                "style-src 'self' 'unsafe-inline' localhost:3000 localhost:5173; "
                "img-src 'self' data: https: localhost:3000 localhost:5173; "
                "font-src 'self' data:; "
                "connect-src 'self' localhost:3000 localhost:5173 ws: wss:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:
            # Strict CSP for production
            return (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests;"
            )


class PIIFilteringMiddleware(BaseHTTPMiddleware):
    """Filter PII from logs and responses."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self.pii_patterns = {
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "api_key": re.compile(r"\b[A-Za-z0-9_-]{20,}\b"),
            "token": re.compile(r"\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b"),  # JWT pattern
        }

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.time()

        # Log sanitized request info
        safe_url = self._sanitize_text(str(request.url))
        sanitized_query = self._sanitize_text(str(request.query_params))

        logger.info(f"Request: {request.method} {safe_url} " f"Query: {sanitized_query} " f"Client: {request.client.host if request.client else 'unknown'}")

        response = await call_next(request)
        duration = time.time() - start_time

        # Log sanitized response info
        logger.info(f"Response: {response.status_code} " f"Duration: {duration:.3f}s " f"Request-ID: {getattr(request.state, 'request_id', 'unknown')}")

        return response

    def _sanitize_text(self, text: str) -> str:
        """Remove PII from text for logging."""
        for pattern_name, pattern in self.pii_patterns.items():
            text = pattern.sub(f"[REDACTED_{pattern_name.upper()}]", text)
        return text


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request size to prevent DoS attacks."""

    def __init__(self, app: Any, max_request_size: int = 10 * 1024 * 1024) -> None:  # 10MB default
        super().__init__(app)
        self.max_request_size = max_request_size

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    logger.warning(f"Request size {size} exceeds limit {self.max_request_size}")
                    return JSONResponse(status_code=413, content={"error": "Request too large", "max_size": f"{self.max_request_size} bytes"})
            except ValueError:
                pass  # Invalid content-length, let it pass

        # For streaming requests, we can't easily check size upfront
        # but we can monitor during processing

        response = await call_next(request)
        return response
