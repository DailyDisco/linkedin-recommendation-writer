from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from jose.exceptions import JWTError

from app.core.config import settings
from app.schemas.user import TokenData


class TokenHelper:
    """Helper for JWT token operations."""

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt: str = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify JWT token and return token data if valid."""
        try:
            import logging

            logger = logging.getLogger(__name__)

            logger.debug(f"Verifying token with SECRET_KEY length: {len(settings.SECRET_KEY)}")
            logger.debug(f"Using algorithm: {settings.JWT_ALGORITHM}")

            # Check if token is empty or None
            if not token or token.strip() == "":
                logger.warning("Token verification failed: Token is empty or None")
                return None

            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            logger.debug(f"Decoded payload: {payload}")

            username: Optional[str] = payload.get("sub")
            user_id: Optional[str] = payload.get("id")

            logger.debug(f"Extracted username: {username}, user_id: {user_id}")

            if username is None:
                logger.warning("Token verification failed: 'sub' claim missing from payload")
                return None
            return TokenData(username=username, id=user_id)
        except jwt.ExpiredSignatureError:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning("Token verification failed: Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"JWTError during token verification: Invalid token - {str(e)}")
            logger.debug(f"Token being verified: {token[:50]}..." if len(token) > 50 else f"Token: {token}")
            return None
        except JWTError as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"JWTError during token verification: {str(e)}")
            logger.debug(f"Token being verified: {token[:50]}..." if len(token) > 50 else f"Token: {token}")
            return None
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error during token verification: {type(e).__name__}: {str(e)}")
            return None


token_helper = TokenHelper()
