from __future__ import annotations

import secrets
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password
from app.config import get_settings
from app.limits import _client
from app.models import User

GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO = "https://www.googleapis.com/oauth2/v3/userinfo"


def google_configured() -> bool:
    settings = get_settings()
    return bool(settings.google_client_id and settings.google_client_secret)


def make_oauth_state() -> str:
    state = secrets.token_urlsafe(24)
    r = _client()
    if r:
        r.setex(f"oauth:google:{state}", 600, "1")
    else:
        # Fallback so local-without-redis still works for a single process.
        from app.limits import _memory
        import time

        _memory[f"oauth:google:{state}"] = (int(time.time()) + 600, time.time())
    return state


def consume_oauth_state(state: str) -> bool:
    if not state:
        return False
    r = _client()
    if r:
        key = f"oauth:google:{state}"
        ok = r.delete(key)
        return bool(ok)
    from app.limits import _memory
    import time

    key = f"oauth:google:{state}"
    until, _ = _memory.pop(key, (0, 0))
    return until > time.time()


def google_authorize_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH}?{urlencode(params)}"


def exchange_google_code(code: str) -> dict:
    settings = get_settings()
    with httpx.Client(timeout=15.0) as client:
        token_resp = client.post(
            GOOGLE_TOKEN,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code >= 400:
            raise HTTPException(status_code=400, detail="Google sign-in failed")
        tokens = token_resp.json()
        access = tokens.get("access_token")
        if not access:
            raise HTTPException(status_code=400, detail="Google sign-in failed")
        info_resp = client.get(
            GOOGLE_USERINFO,
            headers={"Authorization": f"Bearer {access}"},
        )
        if info_resp.status_code >= 400:
            raise HTTPException(status_code=400, detail="Google sign-in failed")
        return info_resp.json()


def upsert_google_user(db: Session, info: dict) -> User:
    email = str(info.get("email") or "").lower().strip()
    sub = str(info.get("sub") or "").strip()
    if not email or not sub:
        raise HTTPException(status_code=400, detail="Google did not return an email")
    if info.get("email_verified") is False:
        raise HTTPException(status_code=400, detail="Google email is not verified")

    user = db.query(User).filter(User.google_sub == sub).first()
    if user:
        return user
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.google_sub = sub
        user.email_verified = True
        db.commit()
        db.refresh(user)
        return user
    user = User(
        email=email,
        hashed_password=hash_password(secrets.token_urlsafe(48)),
        email_verified=True,
        google_sub=sub,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def issue_frontend_redirect(user: User) -> str:
    settings = get_settings()
    token = create_access_token(user.email)
    # Fragment keeps the JWT out of server access logs on the frontend host.
    base = settings.public_base_url.rstrip("/")
    return f"{base}/app#google={token}"
