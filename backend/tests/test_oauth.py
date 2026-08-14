from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.oauth_google import make_oauth_state, upsert_google_user

client = TestClient(app)


def test_google_start_unconfigured() -> None:
    with patch("app.routers.auth.google_configured", return_value=False):
        res = client.get("/auth/google/start", follow_redirects=False)
        assert res.status_code == 503


def test_google_start_redirects() -> None:
    with (
        patch("app.routers.auth.google_configured", return_value=True),
        patch("app.routers.auth.google_authorize_url", return_value="https://accounts.google.com/o/oauth2/v2/auth?x=1"),
    ):
        res = client.get("/auth/google/start", follow_redirects=False)
        assert res.status_code == 302
        assert "accounts.google.com" in res.headers["location"]


def test_google_callback_rejects_bad_state() -> None:
    res = client.get("/auth/google/callback?code=abc&state=forged", follow_redirects=False)
    assert res.status_code == 302
    assert "google_error" in res.headers["location"]


def test_google_callback_success(monkeypatch) -> None:
    from app.database import SessionLocal
    from app.models import User

    state = make_oauth_state()

    def fake_exchange(_code: str) -> dict:
        return {"email": "oauth-user@example.com", "sub": "google-sub-123", "email_verified": True}

    monkeypatch.setattr("app.routers.auth.exchange_google_code", fake_exchange)
    res = client.get(f"/auth/google/callback?code=ok&state={state}", follow_redirects=False)
    assert res.status_code == 302
    loc = res.headers["location"]
    assert "#google=" in loc
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "oauth-user@example.com").first()
        assert user is not None
        assert user.google_sub == "google-sub-123"
        assert user.email_verified is True
    finally:
        db.close()


def test_upsert_google_user_links_existing_email() -> None:
    from app.auth import hash_password
    from app.database import SessionLocal
    from app.models import User

    db = SessionLocal()
    try:
        email = "link-me@example.com"
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            existing = User(email=email, hashed_password=hash_password("password123"), email_verified=False)
            db.add(existing)
            db.commit()
        user = upsert_google_user(db, {"email": email, "sub": "sub-link-1", "email_verified": True})
        assert user.email == email
        assert user.google_sub == "sub-link-1"
        assert user.email_verified is True
    finally:
        db.close()
