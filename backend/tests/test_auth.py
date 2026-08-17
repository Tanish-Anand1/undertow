from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_login_me() -> None:
    email = f"auth-{uuid.uuid4().hex[:10]}@example.com"
    password = "password123"
    reg = client.post("/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 201
    login = client.post("/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_login_wrong_password() -> None:
    email = f"auth-{uuid.uuid4().hex[:10]}@example.com"
    client.post("/auth/register", json={"email": email, "password": "password123"})
    bad = client.post("/auth/login", data={"username": email, "password": "nope-nope"})
    assert bad.status_code == 401


def test_keyword_cap_returns_400(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "max_keywords_per_user", 3)
    email = f"cap-{uuid.uuid4().hex[:10]}@example.com"
    client.post("/auth/register", json={"email": email, "password": "password123"})
    token = client.post("/auth/login", data={"username": email, "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    for i in range(3):
        res = client.post("/watchlists", headers=headers, json={"keyword": f"kw-{i}-{uuid.uuid4().hex[:4]}", "platforms": ["hn"]})
        assert res.status_code == 201
    res = client.post("/watchlists", headers=headers, json={"keyword": "one-too-many", "platforms": ["hn"]})
    assert res.status_code == 400
    assert "cap" in res.json()["detail"].lower()


def test_forgot_password_does_not_leak_user() -> None:
    res = client.post("/auth/forgot-password", json={"email": "nobody-exists@example.com"})
    assert res.status_code == 200
    assert res.json() == {"ok": True}
