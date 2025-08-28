"""Custom exceptions for the application."""

from typing import Any, Dict, Optional


class BaseApplicationError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "GENERIC_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseApplicationError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class NotFoundError(BaseApplicationError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource: str,
        identifier: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, "NOT_FOUND", details)
        self.resource = resource
        self.identifier = identifier


class ExternalServiceError(BaseApplicationError):
    """Raised when an external service call fails."""

    def __init__(
        self,
        service: str,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(f"{service} error: {message}", "EXTERNAL_SERVICE_ERROR", details)
        self.service = service
        self.status_code = status_code


class GitHubAPIError(ExternalServiceError):
    """Raised when GitHub API calls fail."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__("GitHub API", message, status_code, details)


class GeminiAPIError(ExternalServiceError):
    """Raised when Gemini AI API calls fail."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__("Gemini AI", message, status_code, details)


class DatabaseError(BaseApplicationError):
    """Raised when database operations fail."""

    def __init__(
        self,
        operation: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            f"Database {operation} failed: {message}",
            "DATABASE_ERROR",
            details,
        )
        self.operation = operation


class CacheError(BaseApplicationError):
    """Raised when cache operations fail."""

    def __init__(
        self,
        operation: str,
        key: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            f"Cache {operation} failed for key '{key}': {message}",
            "CACHE_ERROR",
            details,
        )
        self.operation = operation
        self.key = key


class RateLimitError(BaseApplicationError):
    """Raised when rate limits are exceeded."""

    def __init__(
        self,
        service: str,
        limit: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            f"Rate limit exceeded for {service}: {limit}",
            "RATE_LIMIT_ERROR",
            details,
        )
        self.service = service
        self.limit = limit


class ConfigurationError(BaseApplicationError):
    """Raised when there are configuration issues."""

    def __init__(
        self,
        setting: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            f"Configuration error for '{setting}': {message}",
            "CONFIGURATION_ERROR",
            details,
        )
        self.setting = setting
