"""Unit tests for security components - no external dependencies."""

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.security_config import security_utils
from app.core.security_middleware import (
    InputSanitizationMiddleware,
    EnhancedSecurityHeadersMiddleware,
    PIIFilteringMiddleware,
    RequestSizeLimitMiddleware,
)


class TestInputSanitizationMiddleware:
    """Test input sanitization middleware."""

    @pytest.mark.asyncio
    async def test_sanitization_middleware_basic(self):
        """Test basic input sanitization."""
        middleware = InputSanitizationMiddleware(None)

        # Mock request
        class MockRequest:
            def __init__(self):
                self.method = "POST"
                self.headers = {"content-type": "application/json"}
                self.query_params = {"test": "value"}

            async def json(self):
                return {"input": "test<script>alert('xss')</script>data"}

        request = MockRequest()

        # Mock call_next function
        async def call_next(req):
            return JSONResponse({"status": "ok"})

        # This should not raise an exception
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 200


class TestEnhancedSecurityHeadersMiddleware:
    """Test enhanced security headers middleware."""

    @pytest.mark.asyncio
    async def test_security_headers_added(self):
        """Test that security headers are added to responses."""
        middleware = EnhancedSecurityHeadersMiddleware(None)

        # Mock request
        class MockRequest:
            def __init__(self):
                self.method = "GET"
                self.url = "http://test.com/api/test"

        request = MockRequest()

        # Mock response
        response = JSONResponse({"test": "data"})

        # Mock call_next function
        async def call_next(req):
            return response

        result = await middleware.dispatch(request, call_next)

        # Check that security headers are present
        assert "X-Content-Type-Options" in result.headers
        assert "X-Frame-Options" in result.headers
        assert "X-XSS-Protection" in result.headers
        assert "Content-Security-Policy" in result.headers
        assert "X-Content-Type-Options" in result.headers


class TestPIIFilteringMiddleware:
    """Test PII filtering middleware."""

    @pytest.mark.asyncio
    async def test_pii_filtering(self):
        """Test that PII is filtered in logs."""
        middleware = PIIFilteringMiddleware(None)

        # Mock request
        class MockRequest:
            def __init__(self):
                self.method = "GET"
                self.url = "http://test.com/api/test?email=user@example.com"
                self.query_params = "email=user@example.com"
                self.client = type('obj', (object,), {'host': '127.0.0.1'})()
                self.state = type('obj', (object,), {'request_id': 'test-id'})()

        request = MockRequest()

        # Mock response
        response = JSONResponse({"status": "ok"})

        # Mock call_next function
        async def call_next(req):
            return response

        result = await middleware.dispatch(request, call_next)

        # Should complete without errors
        assert result.status_code == 200


class TestRequestSizeLimitMiddleware:
    """Test request size limiting middleware."""

    @pytest.mark.asyncio
    async def test_normal_request_size(self):
        """Test that normal-sized requests pass through."""
        middleware = RequestSizeLimitMiddleware(None, max_request_size=1024)

        # Mock request with normal size
        class MockRequest:
            def __init__(self):
                self.method = "POST"
                self.headers = {"content-length": "100"}

        request = MockRequest()

        # Mock response
        response = JSONResponse({"status": "ok"})

        # Mock call_next function
        async def call_next(req):
            return response

        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_large_request_rejected(self):
        """Test that overly large requests are rejected."""
        middleware = RequestSizeLimitMiddleware(None, max_request_size=100)

        # Mock request with large size
        class MockRequest:
            def __init__(self):
                self.method = "POST"
                self.headers = {"content-length": "200"}

        request = MockRequest()

        # Mock call_next function (shouldn't be called)
        async def call_next(req):
            return JSONResponse({"status": "ok"})

        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 413  # Request Entity Too Large
