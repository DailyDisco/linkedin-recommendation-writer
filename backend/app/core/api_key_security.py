"""Secure API key management system."""

import hashlib
import secrets
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.redis_client import get_redis


class APIKeyMetadata(BaseModel):
    """Metadata for API key management."""

    service_name: str = Field(..., description="External service name (e.g., 'github', 'gemini')")
    key_hash: str = Field(..., description="SHA-256 hash of the API key")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    usage_count: int = Field(default=0, description="Number of times key has been used")
    is_active: bool = Field(default=True, description="Whether the key is currently active")


class APIKeyManager:
    """Secure API key management with encryption."""

    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.key_prefix = "api_key:"
        self.metadata_prefix = "api_key_meta:"

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for API keys."""
        key_env = getattr(settings, "API_KEY_ENCRYPTION_KEY", None)
        if key_env:
            return key_env.encode()

        # Generate a new key (in production, this should be stored securely)
        key = Fernet.generate_key()
        print(f"⚠️  WARNING: Generated new encryption key: {key.decode()}")
        print("   Store this key securely in your environment as API_KEY_ENCRYPTION_KEY")
        return key

    async def store_api_key(self, service_name: str, api_key: str) -> str:
        """Store an API key securely with encryption."""
        redis_client = await get_redis()

        # Generate a unique key ID
        key_id = f"{service_name}_{secrets.token_hex(8)}"

        # Encrypt the API key
        encrypted_key = self.cipher.encrypt(api_key.encode())

        # Store encrypted key
        await redis_client.setex(f"{self.key_prefix}{key_id}", 86400 * 365, encrypted_key)  # 1 year TTL

        # Store metadata
        metadata = APIKeyMetadata(service_name=service_name, key_hash=self._hash_api_key(api_key))

        await redis_client.setex(f"{self.metadata_prefix}{key_id}", 86400 * 365, metadata.model_dump_json())

        return key_id

    async def get_api_key(self, key_id: str) -> Optional[str]:
        """Retrieve and decrypt an API key."""
        redis_client = await get_redis()

        # Get encrypted key
        encrypted_key = await redis_client.get(f"{self.key_prefix}{key_id}")
        if not encrypted_key:
            return None

        # Update usage metadata
        await self._update_usage_metadata(key_id)

        # Decrypt and return
        try:
            return self.cipher.decrypt(encrypted_key).decode()
        except Exception:
            return None

    async def get_active_key_for_service(self, service_name: str) -> Optional[Tuple[str, str]]:
        """Get an active API key for a specific service."""
        redis_client = await get_redis()

        # Find all keys for this service
        pattern = f"{self.metadata_prefix}{service_name}_*"
        keys = await redis_client.keys(pattern)

        if not keys:
            return None

        # Check each key's metadata
        for key in keys:
            metadata_raw = await redis_client.get(key)
            if not metadata_raw:
                continue

            metadata = APIKeyMetadata.model_validate_json(metadata_raw)
            if metadata.is_active:
                key_id = key.decode().replace(self.metadata_prefix, "")
                return key_id, await self.get_api_key(key_id)

        return None

    def _hash_api_key(self, api_key: str) -> str:
        """Create a secure hash of the API key for comparison."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def _update_usage_metadata(self, key_id: str):
        """Update usage metadata when key is accessed."""
        redis_client = await get_redis()

        metadata_raw = await redis_client.get(f"{self.metadata_prefix}{key_id}")
        if not metadata_raw:
            return

        metadata = APIKeyMetadata.model_validate_json(metadata_raw)
        metadata.last_used = datetime.utcnow()
        metadata.usage_count += 1

        await redis_client.setex(f"{self.metadata_prefix}{key_id}", 86400 * 365, metadata.model_dump_json())


class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""

    def __init__(self, service_name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func, *args, **kwargs):
        """Execute a function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception(f"Circuit breaker is OPEN for {self.service_name}")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if not self.last_failure_time:
            return True

        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout

    def _on_success(self):
        """Handle successful call."""
        if self.state == "half-open":
            self.state = "closed"
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"

    def get_status(self) -> Dict:
        """Get circuit breaker status."""
        return {"service": self.service_name, "state": self.state, "failure_count": self.failure_count, "last_failure": self.last_failure_time}


# Global instances
api_key_manager = APIKeyManager()

# Circuit breakers for external services
github_circuit_breaker = CircuitBreaker("github_api", failure_threshold=3, recovery_timeout=30)
gemini_circuit_breaker = CircuitBreaker("gemini_api", failure_threshold=5, recovery_timeout=60)
