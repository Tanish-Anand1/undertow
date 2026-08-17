from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.jobs import advance_scan, enqueue_scan
from app.limits import circuit_open
from app.models import Scan, User
from app.schemas import PostOut, ScanOut, StatsOut
from app.security import sanitize_platform, sanitize_tag
from app.services import get_user_feed, get_user_stats

router = APIRouter(tags=["feed"])


def _post_out(post, wl) -> PostOut:
    return PostOut(
        id=post.id,
        platform=post.platform,
        source=post.source,
        title=post.title,
        body=post.body,
        url=post.url,
        author=post.author,
        engagement=post.engagement,
        posted_at=post.posted_at,
        ingested_at=post.ingested_at,
        tag=post.tag,
        relevance_score=post.relevance_score,
        watchlist_id=wl.id if wl else None,
        keyword=wl.keyword if wl else None,
    )


@router.get("/feed", response_model=list[PostOut])
def feed(
    platform: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[PostOut]:
    rows = get_user_feed(
        db,
        user.id,
        platform=sanitize_platform(platform),
        tag=sanitize_tag(tag),
        limit=limit,
    )
    return [_post_out(post, wl) for post, wl in rows]


@router.get("/stats", response_model=StatsOut)
def stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StatsOut:
    data = get_user_stats(db, user.id)
    return StatsOut(**data, x_circuit_open=circuit_open("x"))


def _scan_out(scan: Scan) -> ScanOut:
    return ScanOut(
        id=scan.id,
        status=scan.status,
        total_jobs=scan.total_jobs or 0,
        finished_jobs=scan.finished_jobs or 0,
        error=scan.error,
    )


@router.post("/ingest/run", response_model=ScanOut)
def trigger_ingest(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScanOut:
    settings = get_settings()
    if user.last_scan_at:
        last = user.last_scan_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        wait = timedelta(minutes=settings.scan_cooldown_minutes)
        remaining = (last + wait) - datetime.now(timezone.utc)
        if remaining.total_seconds() > 0:
            mins = max(1, int(remaining.total_seconds() // 60) + 1)
            raise HTTPException(
                status_code=429,
                detail=f"Scan available again in about {mins} minute(s).",
            )
    scan = enqueue_scan(db, user_id=user.id)
    user.last_scan_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(scan)
    return _scan_out(scan)


@router.get("/ingest/{scan_id}", response_model=ScanOut)
def ingest_status(
    scan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScanOut:
    scan = db.get(Scan, scan_id)
    if not scan or (scan.user_id and scan.user_id != user.id):
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status in ("queued", "running"):
        advance_scan(scan.id, max_jobs=1)
        db.expire_all()
        scan = db.get(Scan, scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
    return _scan_out(scan)
