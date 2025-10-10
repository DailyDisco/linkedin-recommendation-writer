"""Custom exceptions for the application with security considerations."""

from typing import Any, Dict, Optional

from app.core.security_config import filter_pii_for_logging


class BaseApplicationError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "GENERIC_ERROR",
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or self._get_default_user_message()
        super().__init__(self.message)

    def _get_default_user_message(self) -> str:
        """Get a safe default user message based on error code."""
        user_messages = {
            "VALIDATION_ERROR": "The provided data is invalid. Please check your input and try again.",
            "NOT_FOUND": "The requested resource was not found.",
            "RATE_LIMIT_ERROR": "Too many requests. Please try again later.",
            "EXTERNAL_SERVICE_ERROR": "A service is temporarily unavailable. Please try again later.",
            "DATABASE_ERROR": "A database error occurred. Please try again later.",
            "CACHE_ERROR": "A caching error occurred. Please try again later.",
            "CONFIGURATION_ERROR": "A configuration error occurred. Please contact support.",
            "AUTHENTICATION_ERROR": "Authentication failed. Please check your credentials.",
            "AUTHORIZATION_ERROR": "You don't have permission to access this resource.",
            "INPUT_SANITIZATION_ERROR": "The provided input contains invalid content.",
        }
        return user_messages.get(self.error_code, "An error occurred. Please try again later.")

    def get_safe_message(self) -> str:
        """Get a sanitized error message safe for logging."""
        return filter_pii_for_logging(self.message)

    def get_user_friendly_message(self) -> str:
        """Get a user-friendly message safe for client responses."""
        return filter_pii_for_logging(self.user_message)

    def to_dict(self, include_details: bool = False) -> Dict[str, Any]:
        """Convert error to dictionary format for API responses."""
        result = {
            "error": self.error_code,
            "message": self.get_user_friendly_message(),
        }

        if include_details and self.details:
            # Sanitize details before including
            safe_details = {}
            for key, value in self.details.items():
                if isinstance(value, str):
                    safe_details[key] = filter_pii_for_logging(value)
                else:
                    safe_details[key] = value
            result["details"] = safe_details

        return result


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


class AuthenticationError(BaseApplicationError):
    """Raised when user authentication fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, error_code="AUTHENTICATION_ERROR", details=details, user_message="Authentication failed. Please check your credentials and try again.")


class AuthorizationError(BaseApplicationError):
    """Raised when user authorization fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, error_code="AUTHORIZATION_ERROR", details=details, user_message="You don't have permission to perform this action.")
