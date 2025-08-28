import logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_database_session
from app.core.token import token_helper
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

router = APIRouter()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


async def authenticate_user(
    username: str,
    password: str,
    db: AsyncSession,
) -> Optional[User]:
    """Authenticate a user by username and password."""
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        logger.warning(f"Authentication failed: User {username} not found or no password set.")
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed for user {username}: Invalid password.")
        return None

    logger.info(f"User {username} authenticated successfully.")
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_database_session),
) -> UserResponse:
    """Register a new user."""
    logger.info(f"Attempting to register new user: {user_in.username}")

    # Check if username or email already exists
    existing_user_query = select(User).where((User.username == user_in.username) | (User.email == user_in.email))
    existing_user_result = await db.execute(existing_user_query)
    existing_user = existing_user_result.scalar_one_or_none()

    if existing_user:
        if existing_user.username == user_in.username:
            logger.warning(f"Registration failed: Username '{user_in.username}' already registered.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        if existing_user.email == user_in.email:
            logger.warning(f"Registration failed: Email '{user_in.email}' already registered.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    hashed_password = get_password_hash(user_in.password)
    user = User(email=user_in.email, username=user_in.username, hashed_password=hashed_password)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"User {user.username} registered successfully with ID: {user.id}")
    return UserResponse.from_orm(user)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_database_session),
) -> Token:
    """OAuth2 token endpoint for user login."""
    logger.info(f"Attempting to log in user: {form_data.username}")

    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        logger.warning(f"Login failed for user {form_data.username}: Invalid credentials.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = token_helper.create_access_token(
        data={
            "sub": user.username,
            "id": str(user.id),  # Include user ID in token
        },
        expires_delta=access_token_expires,
    )

    logger.info(f"User {user.username} logged in successfully, token generated.")
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    db: AsyncSession = Depends(get_database_session),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Get current authenticated user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = token_helper.verify_token(token)
        if payload is None:
            logger.warning("Token verification failed: Payload is None.")
            raise credentials_exception
        username = payload.username
        if username is None:
            logger.warning("Token verification failed: Username not found in payload.")
            raise credentials_exception
        user_id = payload.id  # assuming payload includes id
        if user_id is None:
            logger.warning("Token verification failed: User ID not found in payload.")
            raise credentials_exception
    except Exception:
        logger.warning("Token verification failed: JWTError or other exception during decoding.", exc_info=True)
        raise credentials_exception

    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"Authentication failed: User {username} not found in database.")
        raise credentials_exception
    if not user.is_active:
        logger.warning(f"Authentication failed for user {username}: User is inactive.")
        raise HTTPException(status_code=400, detail="Inactive user")

    logger.debug(f"Current user retrieved: {user.username}")
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active authenticated user."""
    return current_user
