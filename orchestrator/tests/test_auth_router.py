"""Integration tests for auth_router endpoints using FastAPI TestClient."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def auth_dir(tmp_path, monkeypatch):
    """Redirect auth storage to temp dir."""
    test_auth_dir = tmp_path / "_auth"
    test_users_file = test_auth_dir / "users.json"
    monkeypatch.setattr("auth.AUTH_DIR", test_auth_dir)
    monkeypatch.setattr("auth.USERS_FILE", test_users_file)


@pytest.fixture
def client(auth_dir):
    """Create a TestClient with fresh auth state."""
    from main import app
    return TestClient(app)


class TestAuthStatus:
    def test_status_returns_disabled(self, client, monkeypatch):
        monkeypatch.setattr("config.settings.auth_enabled", False)
        res = client.get("/api/auth/status")
        assert res.status_code == 200
        assert res.json()["auth_enabled"] is False

    def test_status_returns_enabled(self, client, monkeypatch):
        monkeypatch.setattr("config.settings.auth_enabled", True)
        res = client.get("/api/auth/status")
        assert res.status_code == 200
        assert res.json()["auth_enabled"] is True


class TestRegisterAndLogin:
    def test_register_returns_token(self, client):
        res = client.post("/api/auth/register", json={"username": "user1", "password": "pass123"})
        assert res.status_code == 200
        data = res.json()
        assert "token" in data
        assert data["username"] == "user1"

    def test_register_duplicate(self, client):
        client.post("/api/auth/register", json={"username": "user1", "password": "pass123"})
        res = client.post("/api/auth/register", json={"username": "user1", "password": "other"})
        assert res.status_code == 409

    def test_login_success(self, client):
        client.post("/api/auth/register", json={"username": "user2", "password": "secret"})
        res = client.post("/api/auth/login", json={"username": "user2", "password": "secret"})
        assert res.status_code == 200
        assert "token" in res.json()

    def test_login_invalid(self, client):
        res = client.post("/api/auth/login", json={"username": "nobody", "password": "wrong"})
        assert res.status_code == 401


class TestAuthMiddleware:
    def test_health_always_accessible(self, client, monkeypatch):
        monkeypatch.setattr("config.settings.auth_enabled", True)
        res = client.get("/health")
        assert res.status_code == 200

    def test_auth_endpoints_always_accessible(self, client, monkeypatch):
        monkeypatch.setattr("config.settings.auth_enabled", True)
        res = client.get("/api/auth/status")
        assert res.status_code == 200

    def test_protected_route_401_without_token(self, client, monkeypatch):
        monkeypatch.setattr("config.settings.auth_enabled", True)
        res = client.get("/api/layers")
        assert res.status_code == 401

    def test_protected_route_with_valid_token(self, client, monkeypatch):
        monkeypatch.setattr("config.settings.auth_enabled", True)
        # Register to get a token
        reg = client.post("/api/auth/register", json={"username": "tester", "password": "pass"})
        token = reg.json()["token"]
        res = client.get("/api/layers", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200

    def test_auth_disabled_passthrough(self, client, monkeypatch):
        monkeypatch.setattr("config.settings.auth_enabled", False)
        res = client.get("/api/layers")
        assert res.status_code == 200
