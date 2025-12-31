"""Integration tests for authentication flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.models.user import User


@pytest.fixture
def test_client():
    """Test client with mocked database."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock async database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.2LQq2W9y1.K0Hy"  # "password123"
    user.is_active = True
    user.role = "free"
    user.credits = 3
    user.subscription_tier = "free"
    user.subscription_status = "active"
    return user


class TestUserRegistration:
    """Tests for user registration endpoint."""

    def test_register_success(self, test_client, mock_db_session, sample_user):
        """Test successful user registration."""
        # Mock database to return None (no existing user)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock refresh to set user ID
        async def mock_refresh(user):
            user.id = 1
            user.username = "newuser"

        mock_db_session.refresh = mock_refresh

        with patch("app.api.v1.auth.get_database_session", return_value=mock_db_session):
            with patch("app.core.dependencies.get_database_session", return_value=mock_db_session):
                response = test_client.post(
                    "/api/v1/auth/register",
                    json={
                        "username": "newuser",
                        "email": "newuser@example.com",
                        "password": "SecureP@ss123",
                    },
                )

        # Should return 201 with access token
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_username(self, test_client, mock_db_session, sample_user):
        """Test registration with existing username."""
        # Mock database to return existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.api.v1.auth.get_database_session", return_value=mock_db_session):
            with patch("app.core.dependencies.get_database_session", return_value=mock_db_session):
                response = test_client.post(
                    "/api/v1/auth/register",
                    json={
                        "username": "testuser",  # Already exists
                        "email": "different@example.com",
                        "password": "SecureP@ss123",
                    },
                )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, test_client, mock_db_session, sample_user):
        """Test registration with existing email."""
        # Create a user with matching email but different username
        existing_user = MagicMock(spec=User)
        existing_user.username = "otheruser"
        existing_user.email = "test@example.com"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.api.v1.auth.get_database_session", return_value=mock_db_session):
            with patch("app.core.dependencies.get_database_session", return_value=mock_db_session):
                response = test_client.post(
                    "/api/v1/auth/register",
                    json={
                        "username": "newuser",
                        "email": "test@example.com",  # Already exists
                        "password": "SecureP@ss123",
                    },
                )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_missing_fields(self, test_client):
        """Test registration with missing required fields."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                # Missing email and password
            },
        )

        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Tests for user login endpoints."""

    def test_login_success(self, test_client, mock_db_session, sample_user):
        """Test successful login."""
        # Set up correct password hash for "password123"
        import bcrypt

        sample_user.hashed_password = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.api.v1.auth.get_database_session", return_value=mock_db_session):
            with patch("app.core.dependencies.get_database_session", return_value=mock_db_session):
                response = test_client.post(
                    "/api/v1/auth/login",
                    json={
                        "username": "testuser",
                        "password": "password123",
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_username(self, test_client, mock_db_session):
        """Test login with non-existent username."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.api.v1.auth.get_database_session", return_value=mock_db_session):
            with patch("app.core.dependencies.get_database_session", return_value=mock_db_session):
                response = test_client.post(
                    "/api/v1/auth/login",
                    json={
                        "username": "nonexistent",
                        "password": "password123",
                    },
                )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_invalid_password(self, test_client, mock_db_session, sample_user):
        """Test login with wrong password."""
        import bcrypt

        sample_user.hashed_password = bcrypt.hashpw("correctpassword".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.api.v1.auth.get_database_session", return_value=mock_db_session):
            with patch("app.core.dependencies.get_database_session", return_value=mock_db_session):
                response = test_client.post(
                    "/api/v1/auth/login",
                    json={
                        "username": "testuser",
                        "password": "wrongpassword",
                    },
                )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_missing_credentials(self, test_client):
        """Test login with missing credentials."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                # Missing password
            },
        )

        assert response.status_code == 422  # Validation error


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_success(self, test_client):
        """Test successful logout."""
        response = test_client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()


class TestPasswordChange:
    """Tests for password change endpoint."""

    def test_change_password_success(self, test_client, mock_db_session, sample_user):
        """Test successful password change."""
        import bcrypt

        sample_user.hashed_password = bcrypt.hashpw("oldpassword123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Create a valid token for the test user
        from app.core.token import token_helper

        token = token_helper.create_access_token(data={"sub": "testuser", "id": "1"})

        with patch("app.api.v1.auth.get_database_session", return_value=mock_db_session):
            with patch("app.core.dependencies.get_database_session", return_value=mock_db_session):
                response = test_client.put(
                    "/api/v1/auth/change-password",
                    json={
                        "current_password": "oldpassword123",
                        "new_password": "newpassword456",
                    },
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert response.status_code == 200
        assert "updated" in response.json()["message"].lower()

    def test_change_password_wrong_current(self, test_client, mock_db_session, sample_user):
        """Test password change with wrong current password."""
        import bcrypt

        sample_user.hashed_password = bcrypt.hashpw("correctpassword".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        from app.core.token import token_helper

        token = token_helper.create_access_token(data={"sub": "testuser", "id": "1"})

        with patch("app.api.v1.auth.get_database_session", return_value=mock_db_session):
            with patch("app.core.dependencies.get_database_session", return_value=mock_db_session):
                response = test_client.put(
                    "/api/v1/auth/change-password",
                    json={
                        "current_password": "wrongpassword",
                        "new_password": "newpassword456",
                    },
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    def test_change_password_unauthenticated(self, test_client):
        """Test password change without authentication."""
        response = test_client.put(
            "/api/v1/auth/change-password",
            json={
                "current_password": "oldpassword",
                "new_password": "newpassword",
            },
        )

        assert response.status_code == 401


class TestTokenValidation:
    """Tests for token validation."""

    def test_valid_token_accepted(self, test_client, mock_db_session, sample_user):
        """Test that valid tokens are accepted."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        from app.core.token import token_helper

        token = token_helper.create_access_token(data={"sub": "testuser", "id": "1"})

        with patch("app.api.v1.auth.get_database_session", return_value=mock_db_session):
            with patch("app.core.dependencies.get_database_session", return_value=mock_db_session):
                response = test_client.get(
                    "/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                )

        # Should not return 401 - token is valid
        assert response.status_code != 401 or "credentials" not in response.json().get("detail", "").lower()

    def test_invalid_token_rejected(self, test_client):
        """Test that invalid tokens are rejected."""
        response = test_client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid-token-here"},
        )

        assert response.status_code == 401

    def test_missing_token_rejected(self, test_client):
        """Test that requests without tokens are rejected for protected endpoints."""
        response = test_client.get("/api/v1/users/me")

        assert response.status_code == 401

    def test_malformed_header_rejected(self, test_client):
        """Test that malformed authorization headers are rejected."""
        response = test_client.get(
            "/api/v1/users/me",
            headers={"Authorization": "NotBearer some-token"},
        )

        assert response.status_code == 401
