from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password
from app.config import get_settings
from app.models import User

GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO = "https://www.googleapis.com/oauth2/v3/userinfo"


def google_configured() -> bool:
    settings = get_settings()
    return bool(settings.google_client_id and settings.google_client_secret)


def callback_uri() -> str:
    settings = get_settings()
    if settings.google_redirect_uri:
        return settings.google_redirect_uri.rstrip("/")
    return "http://127.0.0.1:8000/auth/google/callback"


def make_oauth_state() -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    return jwt.encode(
        {
            "purpose": "google_oauth",
            "redirect_uri": callback_uri(),
            "n": secrets.token_urlsafe(12),
            "exp": expire,
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def read_oauth_state(state: str) -> dict | None:
    if not state:
        return None
    settings = get_settings()
    try:
        payload = jwt.decode(state, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
    if payload.get("purpose") != "google_oauth":
        return None
    return payload


def consume_oauth_state(state: str) -> bool:
    return read_oauth_state(state) is not None


def google_authorize_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": callback_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH}?{urlencode(params)}"


def exchange_google_code(code: str, redirect_uri: str | None = None) -> dict:
    settings = get_settings()
    with httpx.Client(timeout=15.0) as client:
        token_resp = client.post(
            GOOGLE_TOKEN,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri or callback_uri(),
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
