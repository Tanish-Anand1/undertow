from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import authenticate_user, create_access_token, get_current_user, hash_password
from app.config import get_settings
from app.database import get_db
from app.emailer import send_email
from app.limits import allow_auth_attempt
from app.models import User
from app.oauth_google import (
    exchange_google_code,
    google_authorize_url,
    google_configured,
    issue_frontend_redirect,
    make_oauth_state,
    read_oauth_state,
    upsert_google_user,
)
from app.schemas import ForgotPasswordIn, ResetPasswordIn, TokenOut, UserCreate, UserOut, VerifyEmailIn, GuestUpgradeIn
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])

# Guest accounts never log in with a password (they're reached only via JWT, and
# claim() overwrites this entirely), so the hash content is irrelevant — precompute
# it once instead of paying a fresh bcrypt hash on every guest signup.
_GUEST_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


def _client_key(request: Request, email: str) -> str:
    ip = request.client.host if request.client else "unknown"
    return f"{ip}:{email.lower()}"


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> User:
    if not allow_auth_attempt(f"reg:{_client_key(request, payload.email)}"):
        raise HTTPException(status_code=429, detail="Too many signup attempts. Try again later.")
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        name=(sanitize_keyword(payload.name, max_len=120) or None) if payload.name else None,
        email_verified=not settings.require_email_verify,
        email_verify_token=token if settings.require_email_verify else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    if settings.require_email_verify:
        link = f"{settings.public_base_url}/app?verify={token}"
        send_email(
            user.email,
            "Verify your Sudo email",
            f"Confirm this address to finish signup:\n{link}\n",
        )
    return user


@router.post("/guest/start", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def guest_start(db: Session = Depends(get_db)) -> TokenOut:
    guest_email = f"guest-{uuid.uuid4()}@trysudo.in"
    user = User(
        email=guest_email,
        hashed_password=None,
        is_guest=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user.email))


@router.post("/upgrade", response_model=UserOut)
def upgrade_guest(
    payload: GuestUpgradeIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_guest:
        raise HTTPException(status_code=400, detail="User is not a guest")
    
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user.email = payload.email.lower()
    user.name = payload.name
    user.hashed_password = hash_password(payload.password)
    user.is_guest = False
    
    settings = get_settings()
    if settings.require_email_verify:
        user.email_verified = False
        token = secrets.token_urlsafe(32)
        user.email_verify_token = token
        link = f"{settings.public_base_url}/app?verify={token}"
        send_email(
            user.email,
            "Verify your Sudo email",
            f"Confirm this address to finish signup:\n{link}\n",
        )
    else:
        user.email_verified = True

    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenOut:
    email = form_data.username.lower()
    if not allow_auth_attempt(_client_key(request, email)):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    user = authenticate_user(db, email, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if get_settings().require_email_verify and not user.email_verified:
        raise HTTPException(status_code=403, detail="Verify your email before signing in.")
    return TokenOut(access_token=create_access_token(user.email))


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordIn, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=2)
        db.commit()
        settings = get_settings()
        link = f"{settings.public_base_url}/app?reset={token}"
        send_email(
            user.email,
            "Reset your Sudo password",
            f"Use this link within two hours:\n{link}\n",
        )
    return {"ok": True}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.reset_token == payload.token).first()
    if not user or not user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    expires = user.reset_token_expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    user.hashed_password = hash_password(payload.password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return {"ok": True}


@router.post("/verify-email")
def verify_email(payload: VerifyEmailIn, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email_verify_token == payload.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification link")
    user.email_verified = True
    user.email_verify_token = None
    db.commit()
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/guest", response_model=AuthSessionOut)
def start_guest(payload: GuestStartIn, request: Request, db: Session = Depends(get_db)) -> AuthSessionOut:
    ip = request.client.host if request.client else "unknown"
    if not allow_auth_attempt(f"guest:{ip}"):
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
    device_id = sanitize_device_id(payload.device_id)
    if not device_id:
        raise HTTPException(status_code=400, detail="Invalid device id")

    user = db.query(User).filter(User.guest_device_id == device_id).first()
    if not user:
        user = User(
            email=f"guest-{secrets.token_hex(12)}@guest.trysudo.in",
            hashed_password=_GUEST_PASSWORD_HASH,
            email_verified=True,
            is_guest=True,
            guest_device_id=device_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return AuthSessionOut(access_token=create_access_token(user.email), user=user)


@router.post("/claim", response_model=AuthSessionOut)
def claim_account(
    payload: ClaimAccountIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AuthSessionOut:
    if not user.is_guest:
        raise HTTPException(status_code=400, detail="This account is already active.")
    if not allow_auth_attempt(f"claim:{_client_key(request, payload.email)}"):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
    email = payload.email.lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing and existing.id != user.id:
        raise HTTPException(status_code=400, detail="Email already registered")

    settings = get_settings()
    user.email = email
    user.hashed_password = hash_password(payload.password)
    user.name = sanitize_keyword(payload.name, max_len=120) or None
    user.is_guest = False
    user.guest_device_id = None
    user.email_verified = not settings.require_email_verify
    if settings.require_email_verify:
        token = secrets.token_urlsafe(32)
        user.email_verify_token = token
        link = f"{settings.public_base_url}/app?verify={token}"
        send_email(
            user.email,
            "Verify your Sudo email",
            f"Confirm this address to finish signup:\n{link}\n",
        )
    db.commit()
    db.refresh(user)
    if settings.require_email_verify and not user.email_verified:
        raise HTTPException(status_code=403, detail="Verify your email before signing in.")
    return AuthSessionOut(access_token=create_access_token(user.email), user=user)


@router.get("/google/start")
def google_start() -> RedirectResponse:
    if not google_configured():
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    state = make_oauth_state()
    return RedirectResponse(google_authorize_url(state), status_code=302)


@router.get("/google/callback")
def google_callback(
    db: Session = Depends(get_db),
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> RedirectResponse:
    settings = get_settings()
    fail = f"{settings.public_base_url.rstrip('/')}/app#google_error=1"
    if error:
        return RedirectResponse(fail, status_code=302)
    payload = read_oauth_state(state or "")
    if not code or not payload:
        return RedirectResponse(fail, status_code=302)
    try:
        info = exchange_google_code(code, payload.get("redirect_uri"))
        user = upsert_google_user(db, info)
    except HTTPException:
        return RedirectResponse(fail, status_code=302)
    return RedirectResponse(issue_frontend_redirect(user), status_code=302)
