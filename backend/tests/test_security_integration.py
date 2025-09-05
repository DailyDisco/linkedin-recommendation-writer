"""Integration tests for security features."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.api_key_security import APIKeyManager, CircuitBreaker
from app.core.csrf_protection import CSRFTokenManager
from app.core.database_security import DatabaseSecurityMonitor, SecureQueryBuilder
from app.core.input_validation import FileUploadValidator, InputValidator
from app.core.security_monitoring import SecurityEvent, SecurityMonitor
from app.main import app


@pytest.fixture
def client():
    """Test client with mocked dependencies."""
    return TestClient(app)


class TestAPIKeySecurity:
    """Test API key management and security."""

    @pytest.mark.asyncio
    async def test_api_key_storage_and_retrieval(self):
        """Test secure API key storage and retrieval."""
        manager = APIKeyManager()

        # Mock Redis for testing
        with patch("app.core.api_key_security.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            # Test key storage
            test_key = "sk-test123456789"
            key_id = await manager.store_api_key("github", test_key)

            assert key_id.startswith("github_")
            mock_redis.setex.assert_called()

            # Test key retrieval
            mock_redis.get.return_value = manager.cipher.encrypt(test_key.encode())
            retrieved_key = await manager.get_api_key(key_id)

            assert retrieved_key == test_key

    def test_circuit_breaker_functionality(self):
        """Test circuit breaker pattern."""
        breaker = CircuitBreaker("test_service", failure_threshold=2)

        # Initially closed
        assert breaker.state == "closed"
        assert breaker.failure_count == 0

        # Record failures
        breaker._on_failure()
        assert breaker.state == "closed"
        assert breaker.failure_count == 1

        breaker._on_failure()
        assert breaker.state == "open"
        assert breaker.failure_count == 2

        # Test success resets
        breaker._on_success()
        assert breaker.state == "closed"
        assert breaker.failure_count == 0


class TestCSRFProtection:
    """Test CSRF protection mechanisms."""

    @pytest.mark.asyncio
    async def test_csrf_token_generation(self):
        """Test CSRF token generation and validation."""
        manager = CSRFTokenManager()

        with patch("app.core.csrf_protection.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            session_id = "test_session_123"

            # Generate token
            token = await manager.generate_token(session_id)
            assert len(token) == 64  # 32 bytes * 2 for hex

            # Validate token
            mock_redis.get.return_value = session_id.encode()
            is_valid = await manager.validate_token(token, session_id)
            assert is_valid

            # Test invalid token
            is_valid_invalid = await manager.validate_token("invalid_token", session_id)
            assert not is_valid_invalid

    @pytest.mark.asyncio
    async def test_csrf_token_invalidation(self):
        """Test CSRF token invalidation."""
        manager = CSRFTokenManager()

        with patch("app.core.csrf_protection.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            session_id = "test_session_123"
            token = await manager.generate_token(session_id)

            # Invalidate token
            await manager.invalidate_token(token)

            # Verify token is invalidated
            mock_redis.get.return_value = None
            is_valid = await manager.validate_token(token, session_id)
            assert not is_valid


class TestDatabaseSecurity:
    """Test database security features."""

    def test_secure_query_builder(self):
        """Test secure query building."""
        builder = SecureQueryBuilder()

        # Test allowed table
        query, params = builder.build_select_query("users", ["id", "username"])
        assert "SELECT id, username FROM users" in query
        assert params == {}

        # Test disallowed table
        with pytest.raises(ValueError, match="not allowed"):
            builder.build_select_query("forbidden_table")

    def test_database_security_monitoring(self):
        """Test database security monitoring."""
        monitor = DatabaseSecurityMonitor()

        # Test suspicious query detection
        suspicious_query = "SELECT * FROM users WHERE id = 1; DROP TABLE users;"
        analysis = monitor._analyze_query_security(suspicious_query)

        assert analysis["risk_level"] == "high"
        assert len(analysis["issues"]) > 0

    def test_parameterized_query_protection(self):
        """Test protection against SQL injection."""
        builder = SecureQueryBuilder()

        # Test safe parameterized query
        query, params = builder.build_select_query("users", ["id", "username"], "username = :username", limit=1)

        assert ":username" in query
        assert query.count(";") <= 1  # Should not have multiple statements


class TestFileUploadSecurity:
    """Test file upload security features."""

    @pytest.mark.asyncio
    async def test_file_type_validation(self):
        """Test file type validation."""
        validator = FileUploadValidator()

        # Mock file content
        class MockFile:
            def __init__(self, content, filename):
                self.content = content
                self.filename = filename

            async def read(self):
                return self.content

            async def seek(self, pos):
                pass

        # Test valid image
        jpeg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # JPEG header
        mock_file = MockFile(jpeg_content, "test.jpg")

        result = await validator.validate_upload(mock_file)
        assert result["is_valid"]

        # Test malicious file
        malicious_content = b'<script>alert("xss")</script>'
        mock_malicious = MockFile(malicious_content, "evil.html")

        with pytest.raises(Exception):  # Should raise validation error
            await validator.validate_upload(mock_malicious)

    def test_filename_validation(self):
        """Test filename validation."""
        validator = FileUploadValidator()

        # Valid filenames
        assert validator._validate_filename("test.jpg")
        assert validator._validate_filename("document.pdf")

        # Invalid filenames
        assert not validator._validate_filename("")  # Empty
        assert not validator._validate_filename("a" * 300)  # Too long
        assert not validator._validate_filename("../evil.jpg")  # Path traversal
        assert not validator._validate_filename("evil.exe")  # Dangerous extension


class TestInputValidationSecurity:
    """Test comprehensive input validation."""

    def test_email_validation(self):
        """Test email validation."""
        validator = InputValidator()

        # Valid emails
        result = validator.validate("email", "user@example.com")
        assert result["valid"]

        # Invalid emails
        result = validator.validate("email", "invalid-email")
        assert not result["valid"]

    def test_credit_card_validation(self):
        """Test credit card validation."""
        validator = InputValidator()

        # Valid card number (test number)
        result = validator.validate("credit_card", "4532015112830366")
        assert result["valid"]
        assert "masked" in result

        # Invalid card number
        result = validator.validate("credit_card", "1234567890123456")
        assert not result["valid"]

    def test_text_sanitization(self):
        """Test text sanitization."""
        validator = InputValidator()

        malicious_text = "<script>alert('xss')</script>Hello World"
        result = validator.validate("text", malicious_text)

        assert result["valid"]
        # Should be sanitized (depending on implementation)
        assert isinstance(result.get("sanitized"), str)


class TestSecurityMonitoring:
    """Test security monitoring and alerting."""

    @pytest.mark.asyncio
    async def test_security_event_logging(self):
        """Test security event logging."""
        monitor = SecurityMonitor()

        event = SecurityEvent(event_type="failed_login", severity="medium", message="Failed login attempt", source_ip="192.168.1.100", user_id="test_user")

        with patch("app.core.security_monitoring.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await monitor.log_security_event(event)

            # Verify Redis calls were made
            assert mock_redis.setex.called
            assert mock_redis.lpush.called

    @pytest.mark.asyncio
    async def test_security_report_generation(self):
        """Test security report generation."""
        monitor = SecurityMonitor()

        with patch("app.core.security_monitoring.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            # Mock empty results
            mock_redis.keys.return_value = []
            mock_redis.lrange.return_value = []

            report = await monitor.get_security_report(hours=24)

            assert "total_events" in report
            assert "events_by_type" in report
            assert "events_by_severity" in report


class TestIntegrationSecurity:
    """Test end-to-end security integration."""

    def test_security_headers_integration(self, client):
        """Test security headers in actual responses."""
        response = client.get("/health")

        # Check security headers are present
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Content-Security-Policy" in response.headers

    def test_request_id_tracking(self, client):
        """Test request ID tracking."""
        response = client.get("/health")

        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0

    def test_input_validation_integration(self, client):
        """Test input validation in API endpoints."""
        # This would require setting up proper test data and mocking
        # For now, just test that the endpoint exists and handles validation
        response = client.post("/api/v1/recommendations/generate", json={"invalid": "data"})

        # Should return validation error
        assert response.status_code >= 400

    def test_rate_limiting_integration(self, client):
        """Test rate limiting functionality."""
        # Make multiple requests quickly
        responses = []
        for _ in range(5):
            response = client.get("/health")
            responses.append(response.status_code)

        # At least some should succeed
        assert 200 in responses

    def test_error_handling_integration(self, client):
        """Test secure error handling."""
        response = client.get("/nonexistent-endpoint")

        assert response.status_code >= 400
        data = response.json()

        # Should have proper error structure
        assert "error" in data
        assert "message" in data
        assert "request_id" in data

        # Should not leak sensitive information
        error_msg = data["message"].lower()
        assert "password" not in error_msg
        assert "token" not in error_msg
        assert "key" not in error_msg
