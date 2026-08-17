from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _user() -> tuple[str, str]:
    email = f"sec-{uuid.uuid4().hex[:10]}@example.com"
    password = "correcthorsebatterystaple"
    res = client.post("/auth/register", json={"email": email, "password": password})
    assert res.status_code == 201, res.text
    login = client.post("/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200, login.text
    return email, login.json()["access_token"]


def test_health_and_security_headers() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["x-frame-options"] == "DENY"
    assert "content-security-policy" in res.headers


def test_cors_allows_trysudo() -> None:
    res = client.options(
        "/health",
        headers={
            "Origin": "https://www.trysudo.in",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res.status_code in {200, 204}
    assert res.headers.get("access-control-allow-origin") == "https://www.trysudo.in"


def test_feed_requires_auth() -> None:
    assert client.get("/feed").status_code == 401
    assert client.post("/ingest/run").status_code == 401


def test_sql_injection_in_email_rejected() -> None:
    res = client.post(
        "/auth/register",
        json={"email": "a'; DROP TABLE users;--@x.com", "password": "password123"},
    )
    assert res.status_code == 422


def test_sql_injection_in_keyword_is_data_not_query() -> None:
    _, token = _user()
    payload = "'; DROP TABLE posts;--"
    res = client.post(
        "/watchlists",
        headers={"Authorization": f"Bearer {token}"},
        json={"keyword": payload, "platforms": ["hn"]},
    )
    assert res.status_code == 201
    listed = client.get("/watchlists", headers={"Authorization": f"Bearer {token}"})
    assert listed.status_code == 200
    assert any(payload.replace("  ", " ") in w["keyword"] or payload in w["keyword"] for w in listed.json())
    # table still answers
    assert client.get("/health").status_code == 200


def test_xss_javascript_url_stripped_on_upsert() -> None:
    from app.database import SessionLocal
    from app.ingestors.base import RawPost
    from app.services import upsert_raw_post

    db = SessionLocal()
    try:
        post = upsert_raw_post(
            db,
            RawPost(
                platform="hn",
                external_id=f"xss-{uuid.uuid4().hex[:8]}",
                source="HN",
                title="<script>alert(1)</script>",
                body="<img src=x onerror=alert(1)>",
                url="javascript:alert(1)",
                author="x",
                engagement=0,
            ),
        )
        db.commit()
        assert post.url == ""
        assert "<script>" in post.title  # stored as text; React must not eval it
    finally:
        db.close()


def test_platform_filter_injection_ignored() -> None:
    _, token = _user()
    res = client.get(
        "/feed",
        headers={"Authorization": f"Bearer {token}"},
        params={"platform": "hn;drop table posts", "tag": "pain<script>"},
    )
    assert res.status_code == 200
    assert res.json() == []


def test_sanitize_http_url() -> None:
    from app.security import sanitize_http_url

    assert sanitize_http_url("javascript:alert(1)") == ""
    assert sanitize_http_url("data:text/html,hi") == ""
    assert sanitize_http_url("//evil.example/steal") == ""
    assert sanitize_http_url("https://news.ycombinator.com/item?id=1").startswith("https://")
