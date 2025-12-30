import logging
from datetime import timedelta
from typing import Optional

import bcrypt
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_database_session
from app.core.token import token_helper
from app.models.user import User
from app.schemas.user import Token, UserCreate

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

router = APIRouter()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if the provided password matches the stored password (hashed)."""
    password_byte_enc = plain_password.encode("utf-8")
    hashed_password_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password_bytes)


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
    if not verify_password(password, user.hashed_password):  # type: ignore
        logger.warning(f"Authentication failed for user {username}: Invalid password.")
        return None

    logger.info(f"User {username} authenticated successfully.")
    return user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_database_session),
) -> Token:
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

    hashed_password = hash_password(user_in.password)
    user = User(email=user_in.email, username=user_in.username, hashed_password=hashed_password)

    if user_in.email and user_in.email.lower() in settings.admin_emails:
        user.role = "admin"  # type: ignore
    elif user_in.role:  # Allow setting role if provided in schema (e.g. for premium users)
        user.role = user_in.role  # type: ignore
    else:
        user.role = "free"  # type: ignore

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"User {user.username} registered successfully with ID: {user.id}")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = token_helper.create_access_token(
        data={
            "sub": user.username,
            "id": str(user.id),  # Include user ID in token
        },
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


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
    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout() -> dict:
    """Logout endpoint - clears any server-side session data."""
    logger.info("User logout requested")
    return {"message": "Successfully logged out"}


@router.post("/login", response_model=Token)
async def login(
    credentials: dict = Body(...),  # Accept raw JSON instead of form data
    db: AsyncSession = Depends(get_database_session),
) -> Token:
    """Alternative login endpoint that accepts JSON credentials."""
    logger.info("Attempting to log in user via /login endpoint")

    # Extract username and password from the request body
    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
        )

    user = await authenticate_user(username, password, db)
    if not user:
        logger.warning(f"Login failed for user {username}: Invalid credentials.")
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

    logger.info(f"User {user.username} logged in successfully via /login endpoint, token generated.")
    return Token(access_token=access_token, token_type="bearer")


async def get_current_user(
    db: AsyncSession = Depends(get_database_session),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Get current authenticated user from token."""
    logger.debug(f"Backend: Received token from OAuth2 scheme: {token[:50]}...")  # Debug log
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


@router.put("/change-password", response_model=dict)
async def change_password(
    password_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session),
) -> dict:
    """Change user's password."""
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")

    if not current_password or not new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both current_password and new_password are required")

    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    # Hash new password
    hashed_new_password = hash_password(new_password)

    # Update password in database
    current_user.hashed_password = hashed_new_password
    db.add(current_user)
    await db.commit()

    return {"message": "Password updated successfully"}
