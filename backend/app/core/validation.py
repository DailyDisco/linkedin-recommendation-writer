"""Data validation utilities for database and application layers."""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from email_validator import EmailNotValidError, validate_email

logger = logging.getLogger(__name__)


class DataValidator:
    """Comprehensive data validation utilities."""

    @staticmethod
    def validate_email_format(email: str) -> Dict[str, Any]:
        """Validate email format and deliverability."""
        try:
            # Use email_validator library for comprehensive validation
            validated = validate_email(email, check_deliverability=False)

            return {"valid": True, "normalized": validated.email, "message": "Email is valid"}
        except EmailNotValidError as e:
            return {"valid": False, "error": str(e), "message": "Invalid email format"}
        except Exception as e:
            logger.error(f"Email validation error: {e}")
            return {"valid": False, "error": str(e), "message": "Email validation failed"}

    @staticmethod
    def validate_username(username: str) -> Dict[str, Any]:
        """Validate username format and constraints."""
        if not username:
            return {"valid": False, "error": "Username cannot be empty", "message": "Username is required"}

        if len(username) < 3:
            return {"valid": False, "error": "Username too short", "message": "Username must be at least 3 characters"}

        if len(username) > 50:
            return {"valid": False, "error": "Username too long", "message": "Username must be less than 50 characters"}

        # Allow alphanumeric, underscore, and hyphen
        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            return {"valid": False, "error": "Invalid characters", "message": "Username can only contain letters, numbers, underscores, and hyphens"}

        return {"valid": True, "message": "Username is valid"}

    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength requirements."""
        if not password:
            return {"valid": False, "error": "Password cannot be empty", "message": "Password is required"}

        if len(password) < 8:
            return {"valid": False, "error": "Password too short", "message": "Password must be at least 8 characters"}

        if len(password) > 128:
            return {"valid": False, "error": "Password too long", "message": "Password must be less than 128 characters"}

        # Check for character variety
        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"[0-9]", password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password))

        score = sum([has_upper, has_lower, has_digit, has_special])

        strength = "weak"
        if score >= 4:
            strength = "strong"
        elif score >= 3:
            strength = "medium"

        return {
            "valid": True,
            "strength": strength,
            "score": score,
            "requirements": {"has_uppercase": has_upper, "has_lowercase": has_lower, "has_digit": has_digit, "has_special": has_special, "min_length": len(password) >= 8},
            "message": f"Password strength: {strength}",
        }

    @staticmethod
    def validate_github_profile_url(url: str) -> Dict[str, Any]:
        """Validate GitHub profile URL format."""
        if not url:
            return {"valid": False, "error": "URL cannot be empty", "message": "GitHub profile URL is required"}

        # GitHub URL patterns
        github_patterns = [
            r"^https?://github\.com/([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})$",
            r"^https?://www\.github\.com/([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})$",
            r"^github\.com/([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})$",
            r"^@([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})$",  # GitHub handle with @
        ]

        username = None
        for pattern in github_patterns:
            match = re.match(pattern, url.strip())
            if match:
                username = match.group(1)
                break

        if not username:
            return {"valid": False, "error": "Invalid GitHub URL format", "message": "URL must be a valid GitHub profile URL or username"}

        # Validate username format
        if not re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$", username):
            return {"valid": False, "error": "Invalid GitHub username", "message": "GitHub username contains invalid characters"}

        return {"valid": True, "username": username, "normalized_url": f"https://github.com/{username}", "message": f"Valid GitHub profile for user: {username}"}

    @staticmethod
    def validate_recommendation_limits(user_id: int, recommendation_count: int, user_role: str, last_recommendation_date: Optional[datetime]) -> Dict[str, Any]:
        """Validate recommendation limits based on user role and activity."""

        # Define limits by role
        limits = {"free": {"daily_limit": 5, "reset_hours": 24}, "premium": {"daily_limit": 50, "reset_hours": 24}, "admin": {"daily_limit": 1000, "reset_hours": 24}}

        role_limit = limits.get(user_role, limits["free"])
        daily_limit = role_limit["daily_limit"]

        # Check if we need to reset the counter
        needs_reset = False
        if last_recommendation_date:
            time_since_last = datetime.utcnow() - last_recommendation_date
            reset_hours = role_limit["reset_hours"]
            needs_reset = time_since_last.total_seconds() > (reset_hours * 3600)

        # If reset needed, counter should be 0
        effective_count = 0 if needs_reset else recommendation_count

        # Check if limit exceeded
        if effective_count >= daily_limit:
            reset_time = None
            if last_recommendation_date:
                reset_time = last_recommendation_date + timedelta(hours=role_limit["reset_hours"])

            return {
                "valid": False,
                "can_create": False,
                "current_count": effective_count,
                "daily_limit": daily_limit,
                "remaining": 0,
                "reset_time": reset_time.isoformat() if reset_time else None,
                "error": "Daily limit exceeded",
                "message": f"Daily recommendation limit ({daily_limit}) exceeded for {user_role} users",
            }

        return {
            "valid": True,
            "can_create": True,
            "current_count": effective_count,
            "daily_limit": daily_limit,
            "remaining": daily_limit - effective_count,
            "needs_reset": needs_reset,
            "message": f"Can create {daily_limit - effective_count} more recommendations today",
        }

    @staticmethod
    def validate_recommendation_content(content: str) -> Dict[str, Any]:
        """Validate recommendation content."""
        if not content:
            return {"valid": False, "error": "Content cannot be empty", "message": "Recommendation content is required"}

        if len(content) < 50:
            return {"valid": False, "error": "Content too short", "message": "Recommendation must be at least 50 characters"}

        if len(content) > 5000:
            return {"valid": False, "error": "Content too long", "message": "Recommendation cannot exceed 5000 characters"}

        # Check for minimum word count (approximately 10 words for 50 chars)
        word_count = len(content.split())
        if word_count < 8:
            return {"valid": False, "error": "Insufficient content", "message": "Recommendation must contain at least 8 words"}

        return {"valid": True, "word_count": word_count, "character_count": len(content), "message": f"Content validation passed ({word_count} words, {len(content)} characters)"}

    @staticmethod
    def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
        """Sanitize user input by removing potentially harmful content."""
        if not text:
            return ""

        # Remove null bytes and other control characters
        sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

        # Trim whitespace
        sanitized = sanitized.strip()

        # Apply length limit if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    @staticmethod
    def validate_data_types(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data types against a schema."""
        errors = []
        validated_data = {}

        for field, rules in schema.items():
            if field not in data and rules.get("required", False):
                errors.append(f"Required field '{field}' is missing")
                continue

            if field not in data:
                continue

            value = data[field]
            expected_type = rules.get("type")

            # Type validation
            if expected_type == "str" and not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string")
                continue
            elif expected_type == "int" and not isinstance(value, int):
                errors.append(f"Field '{field}' must be an integer")
                continue
            elif expected_type == "float" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be a number")
                continue
            elif expected_type == "bool" and not isinstance(value, bool):
                errors.append(f"Field '{field}' must be a boolean")
                continue
            elif expected_type == "list" and not isinstance(value, list):
                errors.append(f"Field '{field}' must be a list")
                continue

            # Length validation for strings
            if expected_type == "str" and isinstance(value, str):
                min_len = rules.get("min_length")
                max_len = rules.get("max_length")

                if min_len and len(value) < min_len:
                    errors.append(f"Field '{field}' must be at least {min_len} characters")
                    continue
                if max_len and len(value) > max_len:
                    errors.append(f"Field '{field}' cannot exceed {max_len} characters")
                    continue

            # Range validation for numbers
            if expected_type in ["int", "float"] and isinstance(value, (int, float)):
                min_val = rules.get("min_value")
                max_val = rules.get("max_value")

                if min_val is not None and value < min_val:
                    errors.append(f"Field '{field}' must be at least {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    errors.append(f"Field '{field}' cannot exceed {max_val}")
                    continue

            # Enum validation
            allowed_values = rules.get("allowed_values")
            if allowed_values and value not in allowed_values:
                errors.append(f"Field '{field}' must be one of: {', '.join(allowed_values)}")
                continue

            validated_data[field] = value

        return {"valid": len(errors) == 0, "errors": errors, "validated_data": validated_data, "message": "Validation completed" if len(errors) == 0 else f"Found {len(errors)} validation errors"}


# Predefined validation schemas
USER_SCHEMA = {
    "email": {"type": "str", "required": True, "max_length": 255},
    "username": {"type": "str", "required": False, "max_length": 50, "min_length": 3},
    "full_name": {"type": "str", "required": False, "max_length": 100},
    "role": {"type": "str", "required": True, "allowed_values": ["free", "premium", "admin"]},
    "is_active": {"type": "bool", "required": False},
}

RECOMMENDATION_SCHEMA = {
    "title": {"type": "str", "required": True, "max_length": 200, "min_length": 5},
    "content": {"type": "str", "required": True, "max_length": 5000, "min_length": 50},
    "recipient_name": {"type": "str", "required": True, "max_length": 100, "min_length": 2},
    "relationship": {"type": "str", "required": False, "max_length": 100},
}

GITHUB_PROFILE_SCHEMA = {
    "username": {"type": "str", "required": True, "max_length": 39, "min_length": 1},
    "profile_url": {"type": "str", "required": True, "max_length": 500},
    "bio": {"type": "str", "required": False, "max_length": 160},
    "company": {"type": "str", "required": False, "max_length": 100},
    "location": {"type": "str", "required": False, "max_length": 100},
}
