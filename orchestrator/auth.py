"""JWT authentication module — toggleable via AUTH_ENABLED env var.

User store: JSON file at /data/results/_auth/users.json (persists on results volume).
Passwords: bcrypt via passlib.
Tokens: HS256 JWT via PyJWT.
"""

import json
import os
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from passlib.context import CryptContext

from config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

AUTH_DIR = Path(settings.results_dir) / "_auth"
USERS_FILE = AUTH_DIR / "users.json"


def _load_users() -> dict:
    """Load user store from JSON file."""
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        logger.warning("Corrupt users file, starting fresh")
        return {}


def _save_users(users: dict) -> None:
    """Persist user store to JSON file."""
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, indent=2))


def register_user(username: str, password: str) -> dict:
    """Register a new user. Returns user dict or raises ValueError."""
    users = _load_users()
    if username in users:
        raise ValueError("Username already exists")

    users[username] = {
        "username": username,
        "hashed_password": pwd_context.hash(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_users(users)
    logger.info("Registered user: %s", username)
    return {"username": username}


def authenticate_user(username: str, password: str) -> dict | None:
    """Verify credentials. Returns user dict or None."""
    users = _load_users()
    user = users.get(username)
    if not user:
        return None
    if not pwd_context.verify(password, user["hashed_password"]):
        return None
    return {"username": username}


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
