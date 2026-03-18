"""JWT authentication module — toggleable via AUTH_ENABLED env var.

User store: PostgreSQL auth.users table (migrated from JSON file).
Passwords: bcrypt via passlib.
Tokens: HS256 JWT via PyJWT.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from passlib.context import CryptContext
from sqlalchemy import select

from config import settings
from db.engine import sync_session_factory
from db.models.auth import User
from db.audit import write_audit

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

AUTH_DIR = Path(settings.results_dir) / "_auth"
USERS_FILE = AUTH_DIR / "users.json"


def register_user(username: str, password: str) -> dict:
    """Register a new user. Returns user dict or raises ValueError."""
    session = sync_session_factory()
    try:
        existing = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if existing:
            raise ValueError("Username already exists")

        user = User(
            username=username,
            hashed_password=pwd_context.hash(password),
            created_at=datetime.now(timezone.utc),
        )
        session.add(user)
        session.commit()
        logger.info("Registered user: %s", username)
        write_audit("register", "user", entity_id=username, username=username)
        return {"username": username}
    finally:
        session.close()


def authenticate_user(username: str, password: str) -> dict | None:
    """Verify credentials. Returns user dict or None."""
    session = sync_session_factory()
    try:
        user = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if not user:
            return None
        if not user.is_active:
            return None
        if not pwd_context.verify(password, user.hashed_password):
            return None
        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        session.commit()
        write_audit("login", "user", entity_id=username, username=username)
        return {"username": username}
    finally:
        session.close()


def create_access_token(username: str) -> str:
    """Create a signed JWT for the given username."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> str | None:
    """Decode and validate a JWT. Returns username or None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user(authorization: str | None) -> str:
    """FastAPI dependency — extract user from Authorization header.

    Returns 'anonymous' when auth is disabled.
    Raises ValueError when auth is enabled and token is invalid.
    """
    if not settings.auth_enabled:
        return "anonymous"

    if not authorization or not authorization.startswith("Bearer "):
        raise ValueError("Missing or invalid authorization header")

    token = authorization[7:]
    username = decode_token(token)
    if not username:
        raise ValueError("Invalid or expired token")
    return username


def validate_ws_token(token: str | None) -> str | None:
    """Validate a WebSocket token query parameter.

    Returns username when valid (or when auth is disabled).
    Returns None when auth is enabled and token is invalid.
    """
    if not settings.auth_enabled:
        return "anonymous"
    if not token:
        return None
    return decode_token(token)


def migrate_users_json() -> int:
    """One-time migration: import users.json into DB, rename to .migrated.

    Returns number of users migrated.
    """
    if not USERS_FILE.exists():
        return 0

    try:
        users_data = json.loads(USERS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        logger.warning("Could not read users.json for migration")
        return 0

    if not users_data:
        USERS_FILE.rename(USERS_FILE.with_suffix(".json.migrated"))
        return 0

    session = sync_session_factory()
    migrated = 0
    try:
        for username, user_data in users_data.items():
            existing = session.execute(
                select(User).where(User.username == username)
            ).scalar_one_or_none()
            if existing:
                continue

            created_at_str = user_data.get("created_at")
            created_at = datetime.now(timezone.utc)
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                except (ValueError, TypeError):
                    pass

            user = User(
                username=username,
                hashed_password=user_data["hashed_password"],
                created_at=created_at,
            )
            session.add(user)
            migrated += 1

        session.commit()
        USERS_FILE.rename(USERS_FILE.with_suffix(".json.migrated"))
        logger.info("Migrated %d users from users.json to DB", migrated)
    except Exception:
        session.rollback()
        logger.exception("Failed to migrate users.json")
    finally:
        session.close()

    return migrated
