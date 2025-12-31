"""Simplified security utilities - essential validation and sanitization only."""

import re
from typing import List, Optional


def validate_github_username(username: str) -> bool:
    """Validate GitHub username format.

    GitHub username rules:
    - 1-39 characters
    - Alphanumeric and hyphens only
    - Must start and end with alphanumeric
    - No consecutive hyphens
    """
    if not username or not isinstance(username, str):
        return False

    if len(username) < 1 or len(username) > 39:
        return False

    if not username[0].isalnum() or not username[-1].isalnum():
        return False

    if "--" in username:
        return False

    # Check that only alphanumeric and single hyphens are used
    for char in username:
        if not (char.isalnum() or char == "-"):
            return False

    return True


def validate_url(url: str, allowed_domains: Optional[List[str]] = None) -> bool:
    """Validate URL format and optionally check against allowed domains."""
    if not url or not isinstance(url, str):
        return False

    # Basic URL pattern
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",  # path
        re.IGNORECASE,
    )

    if not url_pattern.match(url):
        return False

    # Check against allowed domains if specified
    if allowed_domains:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove port if present
        if ":" in domain:
            domain = domain.split(":")[0]

        return domain in [d.lower() for d in allowed_domains]

    return True


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """Sanitize text input to remove dangerous content.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)

    # Remove null bytes and control characters
    text = text.replace("\x00", "")
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")

    # Limit length
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def filter_pii_for_logging(text: str) -> str:
    """Remove potentially sensitive information from text for safe logging.

    Filters common PII patterns:
    - Email addresses
    - JWT tokens
    - API keys (20+ char alphanumeric strings)
    """
    if not isinstance(text, str):
        return str(text)

    # Email pattern
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "[REDACTED_EMAIL]",
        text,
    )

    # JWT token pattern
    text = re.sub(
        r"\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b",
        "[REDACTED_TOKEN]",
        text,
    )

    # API key pattern (20+ alphanumeric/underscore/hyphen characters)
    text = re.sub(
        r"\b[A-Za-z0-9_-]{20,}\b",
        "[REDACTED_API_KEY]",
        text,
    )

    return text
