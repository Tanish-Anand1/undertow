from datetime import datetime, timedelta, timezone
import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.auth import oauth2_scheme
from app.config import get_settings
from app.database import get_db
from app.limits import allow_auth_attempt
from app.models import SiteVisitor, User

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminUnlockIn(BaseModel):
    password: str


class AdminTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminWatchOut(BaseModel):
    keyword: str
    platforms: list[str]
    active: bool


class AdminUserOut(BaseModel):
    id: int
    email: str
    created_at: datetime
    last_scan_at: datetime | None
    google: bool
    keywords: list[AdminWatchOut]


class AdminOverviewOut(BaseModel):
    user_count: int
    unique_visitors: int
    page_views: int
    cta_clicks: int
    users: list[AdminUserOut]


def _settings_password() -> str:
    return get_settings().admin_password.strip()


def create_admin_token() -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=12)
    return jwt.encode(
        {"sub": "admin", "role": "admin", "exp": expire},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def require_admin(token: str = Depends(oauth2_scheme)) -> None:
    if not _settings_password():
        raise HTTPException(status_code=503, detail="Admin is not configured.")
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid admin session") from exc
    if payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Invalid admin session")


@router.post("/unlock", response_model=AdminTokenOut)
def unlock(payload: AdminUnlockIn, request: Request) -> AdminTokenOut:
    expected = _settings_password()
    if not expected:
        raise HTTPException(status_code=503, detail="Admin is not configured.")
    ip = request.client.host if request.client else "unknown"
    if not allow_auth_attempt(f"admin:{ip}"):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
    given = hashlib.sha256(payload.password.encode("utf-8")).digest()
    want = hashlib.sha256(expected.encode("utf-8")).digest()
    if not hmac.compare_digest(given, want):
        raise HTTPException(status_code=401, detail="Wrong password")
    return AdminTokenOut(access_token=create_admin_token())


@router.get("/overview", response_model=AdminOverviewOut)
def overview(_admin: None = Depends(require_admin), db: Session = Depends(get_db)) -> AdminOverviewOut:
    rows = (
        db.query(User)
        .options(selectinload(User.watchlists))
        .order_by(User.created_at.desc())
        .all()
    )
    users = [
        AdminUserOut(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
            last_scan_at=user.last_scan_at,
            google=bool(user.google_sub),
            keywords=[
                AdminWatchOut(
                    keyword=item.keyword,
                    platforms=[p for p in item.platforms.split(",") if p],
                    active=item.active,
                )
                for item in user.watchlists
            ],
        )
        for user in rows
    ]
    unique_visitors = db.query(func.count(SiteVisitor.id)).scalar() or 0
    page_views = db.query(func.coalesce(func.sum(SiteVisitor.hits), 0)).scalar() or 0
    cta_clicks = db.query(func.coalesce(func.sum(SiteVisitor.cta_clicks), 0)).scalar() or 0
    return AdminOverviewOut(
        user_count=len(users),
        unique_visitors=int(unique_visitors),
        page_views=int(page_views),
        cta_clicks=int(cta_clicks),
        users=users,
    )
