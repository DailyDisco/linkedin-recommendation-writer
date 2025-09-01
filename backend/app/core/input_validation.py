"""Enhanced input validation and sanitization."""

import re
from pathlib import Path
from typing import Any, Dict, Optional, Set

import magic
from fastapi import HTTPException, UploadFile

from app.core.security_config import security_utils


class FileUploadValidator:
    """Validate and secure file uploads."""

    def __init__(self):
        # Allowed MIME types
        self.allowed_mime_types = {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf", "text/plain", "text/csv", "application/json", "application/xml"}

        # Maximum file sizes (in bytes)
        self.max_file_sizes = {
            "image": 5 * 1024 * 1024,  # 5MB for images
            "document": 10 * 1024 * 1024,  # 10MB for documents
            "text": 1 * 1024 * 1024,  # 1MB for text files
        }

        # Dangerous file extensions to block
        self.blocked_extensions = {".exe", ".bat", ".cmd", ".com", ".pif", ".scr", ".vbs", ".js", ".jar", ".py", ".php", ".asp", ".jsp", ".dll", ".so", ".dylib"}

        # File type detection patterns
        self.file_type_patterns = {"image": re.compile(r"^image/"), "document": re.compile(r"^(application/pdf|application/xml|text/)"), "text": re.compile(r"^text/")}

    async def validate_upload(self, file: UploadFile, allowed_types: Optional[Set[str]] = None) -> Dict[str, Any]:
        """Validate an uploaded file comprehensively."""
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")

        # Basic file information
        file_info = {"filename": file.filename, "content_type": file.content_type, "size": 0, "is_valid": False, "detected_type": None, "security_issues": []}

        # Read file content for analysis
        content = await file.read()
        file_info["size"] = len(content)

        # Reset file pointer
        await file.seek(0)

        # Validate file size
        if not self._validate_file_size(content, file.filename):
            file_info["security_issues"].append("File size exceeds limits")
            raise HTTPException(status_code=400, detail="File size exceeds maximum allowed size")

        # Detect MIME type from content
        detected_mime = self._detect_mime_type(content)
        file_info["detected_type"] = detected_mime

        # Validate MIME type
        if detected_mime not in self.allowed_mime_types:
            file_info["security_issues"].append(f"MIME type {detected_mime} not allowed")
            raise HTTPException(status_code=400, detail=f"File type {detected_mime} is not allowed")

        # Check for file type mismatch (content vs extension)
        if not self._validate_file_type_consistency(file.filename, detected_mime):
            file_info["security_issues"].append("File type mismatch detected")
            raise HTTPException(status_code=400, detail="File type mismatch detected")

        # Check for malicious content
        if self._detect_malicious_content(content):
            file_info["security_issues"].append("Malicious content detected")
            raise HTTPException(status_code=400, detail="File contains potentially malicious content")

        # Validate filename
        if not self._validate_filename(file.filename):
            file_info["security_issues"].append("Invalid filename")
            raise HTTPException(status_code=400, detail="Invalid filename")

        file_info["is_valid"] = True
        return file_info

    def _validate_file_size(self, content: bytes, filename: str) -> bool:
        """Validate file size based on type."""
        size = len(content)
        file_type = self._determine_file_type(filename)

        max_size = self.max_file_sizes.get(file_type, 1 * 1024 * 1024)  # Default 1MB
        return size <= max_size

    def _detect_mime_type(self, content: bytes) -> str:
        """Detect MIME type from file content."""
        try:
            # Use python-magic if available
            mime = magic.Magic(mime=True)
            return mime.from_buffer(content)
        except Exception:
            # Fallback to simple detection
            if content.startswith(b"\xff\xd8\xff"):
                return "image/jpeg"
            elif content.startswith(b"\x89PNG\r\n\x1a\n"):
                return "image/png"
            elif content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
                return "image/gif"
            elif content.startswith(b"%PDF"):
                return "application/pdf"
            else:
                return "application/octet-stream"

    def _validate_file_type_consistency(self, filename: str, detected_mime: str) -> bool:
        """Validate that file extension matches detected MIME type."""
        if not filename:
            return False

        extension = Path(filename).suffix.lower()

        # Extension to MIME type mapping
        extension_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".json": "application/json",
            ".xml": "application/xml",
        }

        expected_mime = extension_map.get(extension)
        return expected_mime == detected_mime if expected_mime else True

    def _detect_malicious_content(self, content: bytes) -> bool:
        """Detect potentially malicious content in files."""
        # Check for script tags in text files
        content_str = content.decode("utf-8", errors="ignore")

        # Check for HTML/script injection
        if re.search(r"<script[^>]*>.*?</script>", content_str, re.IGNORECASE | re.DOTALL):
            return True

        # Check for PHP/ASP tags
        if re.search(r"<\?(php|=)", content_str, re.IGNORECASE):
            return True

        # Check for suspicious binary patterns
        if b"\x00\x00\x00\x00" in content[:100]:  # Null bytes at start
            return True

        return False

    def _validate_filename(self, filename: str) -> bool:
        """Validate filename for security."""
        if not filename:
            return False

        # Check length
        if len(filename) > 255:
            return False

        # Check for dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "\x00"]
        if any(char in filename for char in dangerous_chars):
            return False

        # Check for directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            return False

        # Check blocked extensions
        extension = Path(filename).suffix.lower()
        if extension in self.blocked_extensions:
            return False

        return True

    def _determine_file_type(self, filename: str) -> str:
        """Determine file type category from filename."""
        extension = Path(filename).suffix.lower()

        if extension in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            return "image"
        elif extension in [".pdf", ".doc", ".docx", ".xml"]:
            return "document"
        elif extension in [".txt", ".csv", ".json"]:
            return "text"
        else:
            return "unknown"


class InputValidator:
    """Comprehensive input validation for various data types."""

    def __init__(self):
        self.validators = {
            "email": self._validate_email,
            "url": self._validate_url,
            "phone": self._validate_phone,
            "credit_card": self._validate_credit_card,
            "ssn": self._validate_ssn,
            "zip_code": self._validate_zip_code,
            "text": self._validate_text,
            "json": self._validate_json,
        }

    def validate(self, input_type: str, value: Any, **kwargs) -> Dict[str, Any]:
        """Validate input based on type."""
        if input_type not in self.validators:
            return {"valid": False, "error": f"Unknown validation type: {input_type}"}

        try:
            result = self.validators[input_type](value, **kwargs)
            return result
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def _validate_email(self, email: str, **kwargs) -> Dict[str, Any]:
        """Validate email address."""
        if not isinstance(email, str):
            return {"valid": False, "error": "Email must be a string"}

        # Basic email pattern
        pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        if not pattern.match(email):
            return {"valid": False, "error": "Invalid email format"}

        # Additional checks
        if len(email) > 254:  # RFC 5321 limit
            return {"valid": False, "error": "Email too long"}

        return {"valid": True, "sanitized": email.lower().strip()}

    def _validate_url(self, url: str, **kwargs) -> Dict[str, Any]:
        """Validate URL."""
        return {"valid": security_utils.validate_url(url), "sanitized": url.strip() if security_utils.validate_url(url) else url}

    def _validate_phone(self, phone: str, **kwargs) -> Dict[str, Any]:
        """Validate phone number."""
        if not isinstance(phone, str):
            return {"valid": False, "error": "Phone must be a string"}

        # Remove all non-digit characters
        digits_only = re.sub(r"\D", "", phone)

        if len(digits_only) < 10 or len(digits_only) > 15:
            return {"valid": False, "error": "Invalid phone number length"}

        return {"valid": True, "sanitized": digits_only}

    def _validate_credit_card(self, cc_number: str, **kwargs) -> Dict[str, Any]:
        """Validate credit card number (without storing)."""
        if not isinstance(cc_number, str):
            return {"valid": False, "error": "Credit card must be a string"}

        # Remove spaces and dashes
        cc_number = re.sub(r"[\s-]", "", cc_number)

        if not cc_number.isdigit():
            return {"valid": False, "error": "Credit card must contain only digits"}

        if len(cc_number) < 13 or len(cc_number) > 19:
            return {"valid": False, "error": "Invalid credit card length"}

        # Luhn algorithm check
        if not self._luhn_checksum(cc_number):
            return {"valid": False, "error": "Invalid credit card number"}

        return {"valid": True, "masked": self._mask_credit_card(cc_number)}

    def _validate_ssn(self, ssn: str, **kwargs) -> Dict[str, Any]:
        """Validate Social Security Number format."""
        if not isinstance(ssn, str):
            return {"valid": False, "error": "SSN must be a string"}

        # Remove dashes
        ssn = re.sub(r"-", "", ssn)

        if len(ssn) != 9 or not ssn.isdigit():
            return {"valid": False, "error": "Invalid SSN format"}

        return {"valid": True, "masked": "XXX-XX-" + ssn[-4:]}

    def _validate_zip_code(self, zip_code: str, **kwargs) -> Dict[str, Any]:
        """Validate ZIP code."""
        if not isinstance(zip_code, str):
            return {"valid": False, "error": "ZIP code must be a string"}

        # US ZIP code pattern (5 digits or 5+4)
        pattern = re.compile(r"^\d{5}(-\d{4})?$")

        if not pattern.match(zip_code):
            return {"valid": False, "error": "Invalid ZIP code format"}

        return {"valid": True, "sanitized": zip_code}

    def _validate_text(self, text: str, max_length: int = 10000, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize text input."""
        if not isinstance(text, str):
            return {"valid": False, "error": "Input must be a string"}

        if len(text) > max_length:
            return {"valid": False, "error": f"Text exceeds maximum length of {max_length}"}

        sanitized = security_utils.sanitize_text(text)

        return {"valid": True, "sanitized": sanitized}

    def _validate_json(self, json_str: str, **kwargs) -> Dict[str, Any]:
        """Validate JSON string."""
        import json

        try:
            parsed = json.loads(json_str)
            return {"valid": True, "parsed": parsed}
        except json.JSONDecodeError as e:
            return {"valid": False, "error": f"Invalid JSON: {e}"}

    def _luhn_checksum(self, number: str) -> bool:
        """Validate credit card number using Luhn algorithm."""

        def digits_of(n):
            return [int(d) for d in str(n)]

        digits = digits_of(number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)

        for d in even_digits:
            checksum += sum(digits_of(d * 2))

        return checksum % 10 == 0

    def _mask_credit_card(self, cc_number: str) -> str:
        """Mask credit card number for display."""
        if len(cc_number) <= 4:
            return cc_number

        return "*" * (len(cc_number) - 4) + cc_number[-4:]


# Global instances
file_validator = FileUploadValidator()
input_validator = InputValidator()
