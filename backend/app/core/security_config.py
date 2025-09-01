"""Security configuration and utilities."""

import re
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SecurityConfig(BaseModel):
    """Security configuration settings."""

    # Input validation settings
    max_input_length: int = Field(default=10000, description="Maximum input length for text fields")
    max_list_items: int = Field(default=100, description="Maximum items in list inputs")
    max_nesting_depth: int = Field(default=5, description="Maximum nesting depth for complex inputs")

    # Rate limiting settings
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=120, description="Requests per minute")
    rate_limit_burst: int = Field(default=30, description="Burst allowance")

    # Content Security Policy
    csp_enabled: bool = Field(default=True, description="Enable CSP headers")
    csp_report_uri: Optional[str] = Field(default=None, description="CSP violation report URI")

    # PII detection patterns
    pii_patterns: Dict[str, str] = Field(
        default_factory=lambda: {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "api_key": r"\b[A-Za-z0-9_-]{20,}\b",
            "jwt": r"\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b",
        }
    )

    # Case-insensitive PII patterns for better detection
    pii_patterns_case_insensitive: Dict[str, str] = Field(
        default_factory=lambda: {
            "email": r"(?i)\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"(?i)\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"(?i)\b\d{3}[-]?\d{2}[-]?\d{4}\b",
            "credit_card": r"(?i)\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "api_key": r"(?i)\b[A-Za-z0-9_-]{20,}\b",
            "jwt": r"(?i)\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b",
        }
    )

    # Input sanitization
    allowed_html_tags: List[str] = Field(default_factory=lambda: ["p", "br", "strong", "em", "u", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote", "code", "pre"])

    # Security headers
    security_headers_enabled: bool = Field(default=True, description="Enable security headers")
    hsts_enabled: bool = Field(default=True, description="Enable HSTS in production")
    hsts_max_age: int = Field(default=31536000, description="HSTS max-age in seconds")

    # CORS settings
    cors_enabled: bool = Field(default=True, description="Enable CORS")
    cors_allowed_origins: List[str] = Field(default_factory=list)
    cors_allow_credentials: bool = Field(default=True)
    cors_allowed_methods: List[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_allowed_headers: List[str] = Field(default_factory=lambda: ["*"])
    cors_max_age: int = Field(default=86400, description="CORS preflight cache duration")


class SecurityUtils:
    """Utility functions for security operations."""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self._compiled_patterns = {}

        # Compile regex patterns for better performance
        # Use case-insensitive patterns if available, otherwise regular patterns
        patterns_to_use = config.pii_patterns_case_insensitive if hasattr(config, "pii_patterns_case_insensitive") else config.pii_patterns

        for name, pattern in patterns_to_use.items():
            self._compiled_patterns[name] = re.compile(pattern)

    def sanitize_text(self, text: str) -> str:
        """Sanitize text input to remove dangerous content."""
        if not isinstance(text, str):
            return str(text)

        # Remove null bytes and control characters
        text = text.replace("\x00", "")
        text = "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")

        # Limit length
        if len(text) > self.config.max_input_length:
            text = text[: self.config.max_input_length] + "..."

        return text

    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect PII patterns in text."""
        found_pii = {}

        for pattern_name, pattern in self._compiled_patterns.items():
            matches = pattern.findall(text)
            if matches:
                found_pii[pattern_name] = matches

        return found_pii

    def filter_pii_for_logging(self, text: str) -> str:
        """Remove PII from text for safe logging."""
        for pattern_name, pattern in self._compiled_patterns.items():
            text = pattern.sub(f"[REDACTED_{pattern_name.upper()}]", text)
        return text

    def validate_github_username(self, username: str) -> bool:
        """Validate GitHub username format."""
        if not username or not isinstance(username, str):
            return False

        # GitHub username rules: 1-39 chars, alphanumeric and single hyphens only
        # Must start and end with alphanumeric character, no consecutive hyphens
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

    def validate_url(self, url: str, allowed_domains: Optional[List[str]] = None) -> bool:
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
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )  # path

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

    def sanitize_html(self, html_content: str) -> str:
        """Sanitize HTML content using bleach."""
        try:
            import bleach

            return bleach.clean(html_content, tags=self.config.allowed_html_tags, attributes={}, strip=True)
        except ImportError:
            # Fallback if bleach is not available
            return self.sanitize_text(html_content)


# Global security configuration instance
security_config = SecurityConfig()
security_utils = SecurityUtils(security_config)
