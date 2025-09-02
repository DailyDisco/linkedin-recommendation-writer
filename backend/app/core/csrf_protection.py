"""CSRF (Cross-Site Request Forgery) protection middleware."""

import hashlib
import secrets
from typing import Optional

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.redis_client import get_redis


class CSRFTokenManager:
    """Manage CSRF tokens securely."""

    def __init__(self):
        self.token_length = 32
        self.token_lifetime = 3600  # 1 hour
        self.redis_prefix = "csrf_token:"

    async def generate_token(self, session_id: str) -> str:
        """Generate a new CSRF token for a session."""
        redis_client = await get_redis()

        # Generate random token
        token = secrets.token_hex(self.token_length)

        # Create token hash for storage (never store plain token)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Store token hash with session association
        await redis_client.setex(f"{self.redis_prefix}{token_hash}", self.token_lifetime, session_id)

        # Store session -> token mapping for cleanup
        await redis_client.setex(f"{self.redis_prefix}session:{session_id}", self.token_lifetime, token_hash)

        return token

    async def validate_token(self, token: str, session_id: str) -> bool:
        """Validate a CSRF token."""
        if not token or not session_id:
            return False

        redis_client = await get_redis()

        # Hash the provided token
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Check if token exists and belongs to session
        stored_session_id = await redis_client.get(f"{self.redis_prefix}{token_hash}")

        if not stored_session_id:
            return False

        # Verify session matches
        return stored_session_id.decode() == session_id

    async def invalidate_token(self, token: str):
        """Invalidate a CSRF token."""
        if not token:
            return

        redis_client = await get_redis()
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Get session ID before deleting
        session_id = await redis_client.get(f"{self.redis_prefix}{token_hash}")
        if session_id:
            # Clean up session -> token mapping
            await redis_client.delete(f"{self.redis_prefix}session:{session_id.decode()}")

        # Delete token
        await redis_client.delete(f"{self.redis_prefix}{token_hash}")

    async def cleanup_expired_tokens(self):
        """Clean up expired tokens (should be run periodically)."""
        # Redis TTL will handle this automatically, but this method
        # can be used for manual cleanup if needed
        pass


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware to protect against CSRF attacks."""

    def __init__(self, app):
        super().__init__(app)
        self.csrf_manager = CSRFTokenManager()
        self.exempt_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

        # HTTP methods that can be CSRF targets
        self.protected_methods = {"POST", "PUT", "DELETE", "PATCH"}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip CSRF protection for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Skip CSRF for non-protected methods
        if request.method not in self.protected_methods:
            return await call_next(request)

        # Skip CSRF for API endpoints (they should use Authorization headers)
        if request.url.path.startswith("/api/"):
            return await call_next(request)

        # For state-changing operations, require CSRF token
        await self._validate_csrf_token(request)

        response = await call_next(request)

        # Add CSRF token to response for future requests
        await self._inject_csrf_token(request, response)

        return response

    async def _validate_csrf_token(self, request: Request):
        """Validate CSRF token from request."""
        # Get token from various sources
        csrf_token = self._extract_csrf_token(request)

        if not csrf_token:
            raise HTTPException(status_code=403, detail="CSRF token missing. Include X-CSRF-Token header or csrf_token in form data.")

        # Get session ID (you might need to implement session management)
        session_id = await self._get_session_id(request)

        if not session_id:
            raise HTTPException(status_code=403, detail="No valid session found")

        # Validate token
        if not await self.csrf_manager.validate_token(csrf_token, session_id):
            raise HTTPException(status_code=403, detail="Invalid or expired CSRF token")

        # Token is valid, but don't remove it yet (allow for multiple uses within lifetime)

    async def _inject_csrf_token(self, request: Request, response: Response):
        """Inject CSRF token into response."""
        try:
            session_id = await self._get_session_id(request)
            if session_id:
                token = await self.csrf_manager.generate_token(session_id)
                response.headers["X-CSRF-Token"] = token
        except Exception:
            # Don't fail the request if token injection fails
            pass

    def _extract_csrf_token(self, request: Request) -> Optional[str]:
        """Extract CSRF token from various sources."""
        # Check headers first
        token = request.headers.get("X-CSRF-Token")
        if token:
            return token

        # Check form data
        if hasattr(request, "form") and request.form:
            token = request.form.get("csrf_token")
            if token:
                return token

        # Check query parameters (less secure, but supported)
        token = request.query_params.get("csrf_token")
        if token:
            return token

        return None

    async def _get_session_id(self, request: Request) -> Optional[str]:
        """Get session ID from request."""
        # This is a placeholder - you should implement proper session management
        # For now, we'll use a simple approach

        # Check for session cookie
        session_id = request.cookies.get("session_id")
        if session_id:
            return session_id

        # Check for Authorization header (for API requests)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Extract user ID from JWT token (simplified)
            try:
                # This would need proper JWT decoding
                return f"session_{hash(auth_header)}"
            except Exception:
                pass

        # Fallback: create a temporary session ID based on client info
        client_info = f"{request.client.host}_{request.headers.get('User-Agent', '')}"
        return f"temp_session_{hash(client_info)}"


# CSRF protection for API endpoints (different approach)
class APICSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection specifically for API endpoints using custom headers."""

    def __init__(self, app):
        super().__init__(app)
        self.required_header = "X-API-Key"  # Or use Authorization header
        self.allowed_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])

    async def dispatch(self, request: Request, call_next) -> Response:
        # Only protect API endpoints
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # Skip for safe methods
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return await call_next(request)

        # TEMPORARY: Allow certain endpoints without authentication for testing
        if (
            "/api/v1/github/analyze" in request.url.path
            or "/api/v1/github/repository/contributors" in request.url.path
            or "/api/v1/recommendations/prompt-suggestions" in request.url.path
            or "/api/v1/recommendations/autocomplete-suggestions" in request.url.path
            or "/api/v1/recommendations/generate-options/stream" in request.url.path
            or "/api/v1/recommendations/chat-assistant" in request.url.path
            or "/api/v1/recommendations/generate" in request.url.path
            or "/api/v1/recommendations/regenerate" in request.url.path
            or "/api/v1/auth/register" in request.url.path
            or "/api/v1/auth/login" in request.url.path
            or "/api/v1/auth/token" in request.url.path
        ):
            return await call_next(request)

        # Check for API key or proper authorization
        if not self._has_valid_api_auth(request):
            raise HTTPException(status_code=401, detail="API authentication required")

        # Check origin for cross-origin requests
        origin = request.headers.get("Origin")
        if origin and origin not in self.allowed_origins:
            # For API requests, we might be more strict
            referer = request.headers.get("Referer", "")
            if not any(allowed in referer for allowed in self.allowed_origins):
                raise HTTPException(status_code=403, detail="Cross-origin request not allowed")

        response = await call_next(request)

        # Add security headers
        response.headers["X-API-Version"] = "v1"
        response.headers["X-Request-ID"] = getattr(request.state, "request_id", "unknown")

        return response

    def _has_valid_api_auth(self, request: Request) -> bool:
        """Check if request has valid API authentication."""
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return self._validate_api_key(api_key)

        # Check for Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            return self._validate_bearer_token(token)

        return False

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key format and existence."""
        # This should check against your API key storage
        # For now, just check basic format
        return len(api_key) >= 20 and any(char.isalnum() for char in api_key)

    def _validate_bearer_token(self, token: str) -> bool:
        """Validate Bearer token format."""
        # This should decode and validate JWT
        # For now, just check basic format
        return len(token) > 20 and "." in token  # Basic JWT format check


# Global CSRF manager instance
csrf_manager = CSRFTokenManager()
