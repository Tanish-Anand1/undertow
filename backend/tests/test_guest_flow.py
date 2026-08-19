import pytest
from fastapi.testclient import TestClient

from app.models import User
from app.database import SessionLocal

from app.main import app

def test_guest_flow():
    client = TestClient(app)
    # 1. Start guest session
    resp = client.post("/auth/guest/start")
    assert resp.status_code == 201
    data = resp.json()
    token = data["access_token"]
    assert token

    headers = {"Authorization": f"Bearer {token}"}

    # Verify guest state
    me_resp = client.get("/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me = me_resp.json()
    assert me["is_guest"] is True
    assert me["email"].startswith("guest-")

    # 2. Add some keywords (requires watchlists endpoint, assuming it exists and allows guests)
    wl_resp = client.post("/watchlists", headers=headers, json={"keyword": "test keyword"})
    assert wl_resp.status_code == 200

    # 3. Trigger 2 scans
    scan1 = client.post("/ingest/run", headers=headers)
    assert scan1.status_code == 200

    scan2 = client.post("/ingest/run", headers=headers)
    assert scan2.status_code == 200

    # 4. Trigger 3rd scan -> Should fail with 403
    scan3 = client.post("/ingest/run", headers=headers)
    assert scan3.status_code == 403
    assert "limit" in scan3.json()["detail"].lower()

    # 5. Upgrade account
    upgrade_payload = {
        "name": "John Wick",
        "email": "wick@example.com",
        "password": "supersecretpassword"
    }
    upgrade_resp = client.post("/auth/upgrade", headers=headers, json=upgrade_payload)
    assert upgrade_resp.status_code == 200
    upgraded = upgrade_resp.json()
    assert upgraded["is_guest"] is False
    assert upgraded["email"] == "wick@example.com"
    assert upgraded["name"] == "John Wick"

    # 6. Verify we can login now
    login_resp = client.post("/auth/login", data={"username": "wick@example.com", "password": "supersecretpassword"})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()
