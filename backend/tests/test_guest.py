from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _device_id() -> str:
    return uuid.uuid4().hex


def _guest_token() -> str:
    res = client.post("/auth/guest", json={"device_id": _device_id()})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_guest_session_is_reused_for_same_device() -> None:
    device_id = _device_id()
    first = client.post("/auth/guest", json={"device_id": device_id})
    second = client.post("/auth/guest", json={"device_id": device_id})
    assert first.status_code == 200
    assert second.status_code == 200
    me1 = client.get("/auth/me", headers={"Authorization": f"Bearer {first.json()['access_token']}"})
    me2 = client.get("/auth/me", headers={"Authorization": f"Bearer {second.json()['access_token']}"})
    assert me1.json()["id"] == me2.json()["id"]
    assert me1.json()["is_guest"] is True


def test_guest_can_scan_twice_then_blocked() -> None:
    token = _guest_token()
    headers = {"Authorization": f"Bearer {token}"}
    kw = client.post("/watchlists", headers=headers, json={"keyword": f"kw-{uuid.uuid4().hex[:6]}", "platforms": ["hn"]})
    assert kw.status_code == 201, kw.text

    for _ in range(2):
        res = client.post("/ingest/run", headers=headers)
        assert res.status_code == 200, res.text

    blocked = client.post("/ingest/run", headers=headers)
    assert blocked.status_code == 403
    assert "account" in blocked.json()["detail"].lower()

    me = client.get("/auth/me", headers=headers)
    assert me.json()["guest_scans_used"] == 2


def test_claim_upgrades_guest_and_preserves_watchlists() -> None:
    token = _guest_token()
    headers = {"Authorization": f"Bearer {token}"}
    kw = client.post("/watchlists", headers=headers, json={"keyword": f"claim-{uuid.uuid4().hex[:6]}", "platforms": ["hn"]})
    assert kw.status_code == 201

    email = f"claimed-{uuid.uuid4().hex[:10]}@example.com"
    claim = client.post(
        "/auth/claim",
        headers=headers,
        json={"name": "Ada", "email": email, "password": "password123"},
    )
    assert claim.status_code == 200, claim.text
    new_token = claim.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me.status_code == 200
    assert me.json()["is_guest"] is False
    assert me.json()["name"] == "Ada"
    assert me.json()["email"] == email

    watchlists = client.get("/watchlists", headers={"Authorization": f"Bearer {new_token}"})
    assert watchlists.status_code == 200
    assert any(w["keyword"].startswith("claim-") for w in watchlists.json())

    login = client.post("/auth/login", data={"username": email, "password": "password123"})
    assert login.status_code == 200

    old_token_check = client.get("/auth/me", headers=headers)
    assert old_token_check.status_code == 401


def test_claim_frees_device_id_for_a_new_guest() -> None:
    device_id = _device_id()
    start = client.post("/auth/guest", json={"device_id": device_id})
    guest_headers = {"Authorization": f"Bearer {start.json()['access_token']}"}
    guest_id = client.get("/auth/me", headers=guest_headers).json()["id"]

    email = f"freed-{uuid.uuid4().hex[:10]}@example.com"
    claim = client.post(
        "/auth/claim",
        headers=guest_headers,
        json={"name": "Zed", "email": email, "password": "password123"},
    )
    assert claim.status_code == 200, claim.text

    again = client.post("/auth/guest", json={"device_id": device_id})
    assert again.status_code == 200
    new_me = client.get("/auth/me", headers={"Authorization": f"Bearer {again.json()['access_token']}"})
    assert new_me.json()["is_guest"] is True
    assert new_me.json()["id"] != guest_id


def test_claim_rejects_duplicate_email() -> None:
    existing_email = f"dup-{uuid.uuid4().hex[:10]}@example.com"
    client.post("/auth/register", json={"email": existing_email, "password": "password123"})

    token = _guest_token()
    headers = {"Authorization": f"Bearer {token}"}
    claim = client.post(
        "/auth/claim",
        headers=headers,
        json={"name": "Bob", "email": existing_email, "password": "password123"},
    )
    assert claim.status_code == 400


def test_claim_does_not_issue_token_when_email_verify_required(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "require_email_verify", True)
    token = _guest_token()
    headers = {"Authorization": f"Bearer {token}"}
    email = f"unverified-{uuid.uuid4().hex[:10]}@example.com"
    claim = client.post(
        "/auth/claim",
        headers=headers,
        json={"name": "Vera", "email": email, "password": "password123"},
    )
    assert claim.status_code == 403, claim.text

    login = client.post("/auth/login", data={"username": email, "password": "password123"})
    assert login.status_code == 403


def test_claim_requires_guest_account() -> None:
    email = f"nonguest-{uuid.uuid4().hex[:10]}@example.com"
    client.post("/auth/register", json={"email": email, "password": "password123"})
    login = client.post("/auth/login", data={"username": email, "password": "password123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    claim = client.post(
        "/auth/claim",
        headers=headers,
        json={"name": "Carl", "email": "someone-else@example.com", "password": "password123"},
    )
    assert claim.status_code == 400


def test_invalid_device_id_rejected(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "auth_login_max_attempts", 10_000)
    res = client.post("/auth/guest", json={"device_id": "!!short!!"})
    assert res.status_code in (400, 422)
