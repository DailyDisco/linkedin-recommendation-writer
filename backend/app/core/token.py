import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.user import TokenData

logger = logging.getLogger(__name__)


class TokenHelper:
    """Helper for JWT token operations."""

    def __init__(self):
        self.secret_key_bytes = settings.SECRET_KEY.encode("utf-8")
        logger.debug(f"TokenHelper initialized. secret_key_bytes type: {type(self.secret_key_bytes)}, length: {len(self.secret_key_bytes)}")

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})

        # Debugging: Log SECRET_KEY type before encoding
        logger.debug(f"SECRET_KEY used for encoding type: {type(self.secret_key_bytes)}, length: {len(self.secret_key_bytes)}")
        encoded_jwt: str = jwt.encode(to_encode, self.secret_key_bytes, algorithm=settings.JWT_ALGORITHM)  # Use pre-encoded secret key
        logger.debug(f"Encoded JWT (from create_access_token): {encoded_jwt[:50]}...")
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify JWT token and return token data if valid."""
        try:
            logger.debug(f"Verifying token with SECRET_KEY length: {len(self.secret_key_bytes)}")
            logger.debug(f"Using algorithm: {settings.JWT_ALGORITHM}")

            # Check if token is empty or None
            if not token or token.strip() == "":
                logger.warning("Token verification failed: Token is empty or None")
                return None

            logger.debug(f"Token type (before decode): {type(token)}, length: {len(token)}")
            logger.debug(f"SECRET_KEY used for decoding type: {type(self.secret_key_bytes)}, length: {len(self.secret_key_bytes)}")

            payload = jwt.decode(token, self.secret_key_bytes, algorithms=[settings.JWT_ALGORITHM])  # Use pre-encoded secret key
            logger.debug(f"Decoded payload: {payload}")

            username: Optional[str] = payload.get("sub")
            user_id: Optional[str] = payload.get("id")

            logger.debug(f"Extracted username: {username}, user_id: {user_id}")

            if username is None:
                logger.warning("Token verification failed: 'sub' claim missing from payload")
                return None
            return TokenData(username=username, id=user_id)
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: Token has expired")
            return None
        except (JWTError, ValidationError) as e:
            logger.error(f"JWTError or ValidationError during token verification: {str(e)}")
            logger.debug(f"Token being verified: {token[:50]}..." if len(token) > 50 else f"Token: {token}")
            logger.debug(f"SECRET_KEY type (in exception): {type(self.secret_key_bytes)}, length: {len(self.secret_key_bytes)}")
            logger.debug(f"JWT_ALGORITHM (in exception): {settings.JWT_ALGORITHM}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {type(e).__name__}: {str(e)}")
            logger.debug(f"Token being verified: {token[:50]}..." if len(token) > 50 else f"Token: {token}")
            logger.debug(f"SECRET_KEY type (in unexpected exception): {type(self.secret_key_bytes)}, length: {len(self.secret_key_bytes)}")
            logger.debug(f"JWT_ALGORITHM (in unexpected exception): {settings.JWT_ALGORITHM}")
            return None


token_helper = TokenHelper()
