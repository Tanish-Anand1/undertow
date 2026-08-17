from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)


def test_admin_rejects_wrong_password(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_PASSWORD", "ledger-test-pass")
    get_settings.cache_clear()
    res = client.post("/admin/unlock", json={"password": "nope"})
    get_settings.cache_clear()
    assert res.status_code == 401


def test_admin_unlock_and_overview(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_PASSWORD", "ledger-test-pass")
    get_settings.cache_clear()
    unlock = client.post("/admin/unlock", json={"password": "ledger-test-pass"})
    assert unlock.status_code == 200
    token = unlock.json()["access_token"]
    overview = client.get("/admin/overview", headers={"Authorization": f"Bearer {token}"})
    get_settings.cache_clear()
    assert overview.status_code == 200
    body = overview.json()
    assert "users" in body
    assert "user_count" in body
    assert "unique_visitors" in body
    assert "page_views" in body
    assert "cta_clicks" in body


def test_presence_ping_counts_unique_people(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_PASSWORD", "ledger-test-pass")
    get_settings.cache_clear()
    first = client.post("/presence/ping", json={"visitor_id": "visitor-aaaa", "kind": "visit"})
    second = client.post("/presence/ping", json={"visitor_id": "visitor-aaaa", "kind": "visit"})
    click = client.post("/presence/ping", json={"visitor_id": "visitor-aaaa", "kind": "click"})
    other = client.post("/presence/ping", json={"visitor_id": "visitor-bbbb", "kind": "visit"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert click.status_code == 200
    assert other.status_code == 200
    token = client.post("/admin/unlock", json={"password": "ledger-test-pass"}).json()["access_token"]
    overview = client.get("/admin/overview", headers={"Authorization": f"Bearer {token}"})
    get_settings.cache_clear()
    assert overview.status_code == 200
    body = overview.json()
    assert body["unique_visitors"] >= 2
    assert body["page_views"] >= 3
    assert body["cta_clicks"] >= 1
