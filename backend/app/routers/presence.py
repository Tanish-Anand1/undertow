from datetime import datetime, timezone
import hashlib
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.limits import allow_presence
from app.models import SiteVisitor

router = APIRouter(prefix="/presence", tags=["presence"])

_KEY = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")


class PresenceIn(BaseModel):
    visitor_id: str = Field(min_length=8, max_length=64)
    kind: str = Field(default="visit")


def _visitor_key(payload: PresenceIn, request: Request) -> str:
    raw = payload.visitor_id.strip()
    if _KEY.match(raw):
        return raw
    ip = request.client.host if request.client else "unknown"
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:32]


@router.post("/ping")
def ping(payload: PresenceIn, request: Request, db: Session = Depends(get_db)) -> dict:
    ip = request.client.host if request.client else "unknown"
    if not allow_presence(ip):
        raise HTTPException(status_code=429, detail="Slow down")
    kind = payload.kind.strip().lower()
    if kind not in {"visit", "click"}:
        kind = "visit"
    key = _visitor_key(payload, request)
    now = datetime.now(timezone.utc)
    row = db.query(SiteVisitor).filter(SiteVisitor.visitor_key == key).first()
    if row:
        row.hits += 1 if kind == "visit" else 0
        if kind == "click":
            row.cta_clicks += 1
            if row.hits < 1:
                row.hits = 1
        row.last_seen = now
    else:
        row = SiteVisitor(
            visitor_key=key,
            hits=1,
            cta_clicks=1 if kind == "click" else 0,
            first_seen=now,
            last_seen=now,
        )
        db.add(row)
    db.commit()
    return {"ok": True}
