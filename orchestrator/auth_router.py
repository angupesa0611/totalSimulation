"""Auth endpoints — register, login, status check."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auth import register_user, authenticate_user, create_access_token
from config import settings

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    username: str


class AuthStatus(BaseModel):
    auth_enabled: bool


@auth_router.post("/register", response_model=AuthResponse)
def register(req: AuthRequest):
    """Create a new user and return a JWT."""
    try:
        user = register_user(req.username, req.password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    token = create_access_token(user["username"])
    return AuthResponse(token=token, username=user["username"])


@auth_router.post("/login", response_model=AuthResponse)
def login(req: AuthRequest):
    """Authenticate and return a JWT."""
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["username"])
    return AuthResponse(token=token, username=user["username"])


@auth_router.get("/status", response_model=AuthStatus)
def status():
    """Check whether authentication is enabled."""
    return AuthStatus(auth_enabled=settings.auth_enabled)
