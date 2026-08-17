from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.database import SessionLocal
from app.ingestors import get_registered_ingestors
from app.limits import allow_call, circuit_open, trip_circuit
from app.models import Scan, Watchlist
from app.services import ingest_source_keyword


def _ingestors():
    return {i.platform: i for i in get_registered_ingestors()}


def ingest_source_keyword_job(source: str, keyword: str, scan_id: int | None = None) -> dict:
    """RQ job: one source × one keyword. Failures here retry; they do not abort other queues."""
    if circuit_open(source) and source != "x":
        stats = {"source": source, "keyword": keyword, "skipped": "circuit_open"}
        _finish_scan_job(scan_id, stats, ok=True)
        return stats
    if not circuit_open(source) and not allow_call(source):
        raise Exception(f"rate_limited:{source}")

    db = SessionLocal()
    try:
        ingestor = _ingestors().get(source)
        if ingestor is None:
            stats = {"source": source, "error": "unknown_source"}
            _finish_scan_job(scan_id, stats, ok=True)
            return stats
        stats = ingest_source_keyword(db, ingestor, keyword)
        stats["source"] = source
        stats["keyword"] = keyword
        _finish_scan_job(scan_id, stats, ok=True)
        return stats
    except Exception as exc:
        msg = str(exc).lower()
        if "402" in msg or "429" in msg or "rate" in msg or "credits" in msg:
            trip_circuit(source, 900, reason=str(exc)[:200])
            if source == "x":
                # Public fallback lives inside the X ingestor; treat as non-fatal.
                _finish_scan_job(scan_id, {"source": source, "degraded": True}, ok=True)
                return {"source": source, "degraded": True}
        _finish_scan_job(scan_id, {"source": source, "error": str(exc)[:300]}, ok=False)
        raise
    finally:
        db.close()


def send_digest_job(user_id: int | None = None) -> dict:
    from app.digest_job import run_digest

    db = SessionLocal()
    try:
        return run_digest(db, user_id=user_id)
    finally:
        db.close()


def _finish_scan_job(scan_id: int | None, stats: dict, ok: bool) -> None:
    if not scan_id:
        return
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if not scan:
            return
        scan.finished_jobs = int(scan.finished_jobs or 0) + 1
        scan.status = "running"
        blob = dict(scan.results or {})
        key = f"{stats.get('source')}:{stats.get('keyword')}"
        blob[key] = stats
        scan.results = blob
        flag_modified(scan, "results")
        if not ok:
            scan.error = (scan.error or "") + f"{key}: {stats.get('error')}; "
        if scan.finished_jobs >= (scan.total_jobs or 0):
            scan.status = "done" if not scan.error else "partial"
        db.commit()
    except Exception as exc:  # noqa: BLE001
        print(f"[scan] finish failed: {exc}")
        db.rollback()
    finally:
        db.close()


def _reddit_configured() -> bool:
    from app.config import get_settings

    s = get_settings()
    return bool(s.reddit_client_id and s.reddit_client_secret)


def _job_list(by_kw: dict[str, set[str]]) -> list[list[str]]:
    sources = ("hn", "github", "x", "reddit")
    pending: list[list[str]] = []
    reddit_ok = _reddit_configured()
    for keyword, plats in by_kw.items():
        for source in sources:
            if plats and source not in plats:
                continue
            if source == "reddit" and not reddit_ok:
                continue
            pending.append([source, keyword])
    return pending


def advance_scan(scan_id: int, max_jobs: int = 1) -> None:
    """Run a few pending ingest jobs. Safe for short serverless request timeouts."""
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if not scan or scan.status not in ("queued", "running"):
            return
        blob = dict(scan.results or {})
        pending = list(blob.get("pending") or [])
        if not pending:
            if int(scan.finished_jobs or 0) >= int(scan.total_jobs or 0):
                scan.status = "done" if not scan.error else "partial"
                db.commit()
            return
        for _ in range(max_jobs):
            if not pending:
                break
            source, keyword = pending.pop(0)
            blob["pending"] = pending
            scan.results = blob
            flag_modified(scan, "results")
            db.commit()
            try:
                ingest_source_keyword_job(source, keyword, scan_id)
            except Exception as exc:  # noqa: BLE001
                print(f"[scan] job failed {source} {keyword}: {exc}")
            scan = db.get(Scan, scan_id)
            if not scan:
                return
            blob = dict(scan.results or {})
            pending = list(blob.get("pending") or [])
        scan = db.get(Scan, scan_id)
        if scan and not list((scan.results or {}).get("pending") or []):
            if int(scan.finished_jobs or 0) >= int(scan.total_jobs or 0):
                scan.status = "done" if not scan.error else "partial"
                db.commit()
    finally:
        db.close()


def enqueue_scan(db, *, user_id: int | None, keywords: list[str] | None = None) -> Scan:

    if keywords is None:
        rows = list(db.scalars(select(Watchlist).where(Watchlist.active.is_(True))).all())
        by_kw: dict[str, set[str]] = defaultdict(set)
        for wl in rows:
            if user_id and wl.owner_id != user_id:
                continue
            plats = {p.strip().lower() for p in (wl.platforms or "").split(",") if p.strip()}
            by_kw[wl.keyword.strip().lower()] |= plats
    else:
        by_kw = {k.strip().lower(): {"hn", "github", "x", "reddit"} for k in keywords}

    pending = _job_list(by_kw)
    scan = Scan(
        user_id=user_id,
        status="queued",
        total_jobs=len(pending),
        finished_jobs=0,
        results={"pending": pending},
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    from app.queues import redis_live

    if redis_live() and pending:
        try:
            from app.queues import queue, retry

            for source, keyword in pending:
                queue(source).enqueue(
                    ingest_source_keyword_job,
                    source,
                    keyword,
                    scan.id,
                    retry=retry(),
                    job_timeout=240,
                )
            scan.results = {}
            flag_modified(scan, "results")
        except Exception as exc:  # noqa: BLE001
            print(f"[scan] RQ enqueue failed; polling will crawl: {exc}")

    scan.status = "running" if pending else "done"
    db.commit()
    db.refresh(scan)
    return scan
