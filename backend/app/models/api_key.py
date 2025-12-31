"""API Key model for Team tier API access."""

import secrets
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import ARRAY, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ApiKey(Base):
    """API Key model for storing API keys for Team tier users."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Key data
    name = Column(String(255), nullable=False)  # User-provided name for the key
    key_hash = Column(String(255), nullable=False, unique=True, index=True)  # Hashed API key
    key_prefix = Column(String(10), nullable=False, index=True)  # First 8 chars for identification

    # Permissions
    scopes = Column(ARRAY(Text), default=[])  # e.g., ['recommendations:read', 'recommendations:write']

    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="api_keys")

    @property
    def is_expired(self) -> bool:
        """Check if API key is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """Generate a new API key.

        Returns:
            tuple: (full_key, key_hash, key_prefix)
        """
        # Generate a secure random key
        full_key = f"lrw_{secrets.token_urlsafe(32)}"
        key_prefix = full_key[:12]  # "lrw_" + 8 chars

        # Hash the key for storage
        import hashlib

        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        return full_key, key_hash, key_prefix

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for comparison."""
        import hashlib

        return hashlib.sha256(key.encode()).hexdigest()

    def record_usage(self) -> None:
        """Record API key usage."""
        self.last_used_at = datetime.now(timezone.utc)
        self.usage_count += 1

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name={self.name}, prefix={self.key_prefix}, active={self.is_active})>"
