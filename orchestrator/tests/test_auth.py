"""Unit tests for orchestrator/auth.py — JWT auth module."""

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
import jwt

from auth import (
    register_user,
    authenticate_user,
    create_access_token,
    decode_token,
    get_current_user,
    validate_ws_token,
    _load_users,
    _save_users,
    USERS_FILE,
    AUTH_DIR,
)


@pytest.fixture(autouse=True)
def clean_users(tmp_path, monkeypatch):
    """Redirect user storage to a temp directory for each test."""
    test_auth_dir = tmp_path / "_auth"
    test_users_file = test_auth_dir / "users.json"
    monkeypatch.setattr("auth.AUTH_DIR", test_auth_dir)
    monkeypatch.setattr("auth.USERS_FILE", test_users_file)
    yield


class TestUserRegistration:
    def test_register_creates_user(self):
        result = register_user("alice", "password123")
        assert result["username"] == "alice"
        users = _load_users()
        assert "alice" in users
        assert "hashed_password" in users["alice"]

    def test_register_duplicate_raises(self):
        register_user("alice", "password123")
        with pytest.raises(ValueError, match="already exists"):
            register_user("alice", "other_password")


class TestAuthentication:
    def test_authenticate_valid(self):
        register_user("bob", "secret")
        result = authenticate_user("bob", "secret")
        assert result is not None
        assert result["username"] == "bob"

    def test_authenticate_wrong_password(self):
        register_user("bob", "secret")
        result = authenticate_user("bob", "wrong")
        assert result is None

    def test_authenticate_unknown_user(self):
        result = authenticate_user("nobody", "password")
        assert result is None


class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token("charlie")
        username = decode_token(token)
        assert username == "charlie"

    def test_expired_token(self, monkeypatch):
        monkeypatch.setattr("auth.settings.access_token_expire_minutes", -1)
        token = create_access_token("charlie")
        result = decode_token(token)
        assert result is None

    def test_invalid_token(self):
        result = decode_token("not.a.real.token")
        assert result is None

    def test_tampered_token(self):
        token = create_access_token("charlie")
        tampered = token[:-4] + "XXXX"
        result = decode_token(tampered)
        assert result is None


class TestGetCurrentUser:
    def test_auth_disabled_returns_anonymous(self, monkeypatch):
        monkeypatch.setattr("auth.settings.auth_enabled", False)
        assert get_current_user(None) == "anonymous"
        assert get_current_user("") == "anonymous"

    def test_auth_enabled_no_header_raises(self, monkeypatch):
        monkeypatch.setattr("auth.settings.auth_enabled", True)
        with pytest.raises(ValueError, match="Missing"):
            get_current_user(None)

    def test_auth_enabled_valid_token(self, monkeypatch):
        monkeypatch.setattr("auth.settings.auth_enabled", True)
        token = create_access_token("dave")
        result = get_current_user(f"Bearer {token}")
        assert result == "dave"

    def test_auth_enabled_invalid_token(self, monkeypatch):
        monkeypatch.setattr("auth.settings.auth_enabled", True)
        with pytest.raises(ValueError, match="Invalid"):
            get_current_user("Bearer bad.token.here")


class TestWSTokenValidation:
    def test_auth_disabled(self, monkeypatch):
        monkeypatch.setattr("auth.settings.auth_enabled", False)
        assert validate_ws_token(None) == "anonymous"
        assert validate_ws_token("any_token") == "anonymous"

    def test_auth_enabled_valid(self, monkeypatch):
        monkeypatch.setattr("auth.settings.auth_enabled", True)
        token = create_access_token("eve")
        assert validate_ws_token(token) == "eve"

    def test_auth_enabled_no_token(self, monkeypatch):
        monkeypatch.setattr("auth.settings.auth_enabled", True)
        assert validate_ws_token(None) is None

    def test_auth_enabled_bad_token(self, monkeypatch):
        monkeypatch.setattr("auth.settings.auth_enabled", True)
        assert validate_ws_token("invalid") is None
