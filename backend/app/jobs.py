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


def enqueue_scan(db, *, user_id: int | None, keywords: list[str] | None = None) -> Scan:
    from app.queues import queue, retry

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

    scan = Scan(user_id=user_id, status="queued", total_jobs=0, finished_jobs=0, results={})
    db.add(scan)
    db.commit()
    db.refresh(scan)

    n = 0
    sources = ("hn", "github", "x", "reddit")
    for keyword, plats in by_kw.items():
        for source in sources:
            if plats and source not in plats:
                continue
            try:
                queue(source).enqueue(
                    ingest_source_keyword_job,
                    source,
                    keyword,
                    scan.id,
                    retry=retry(),
                    job_timeout=240,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[scan] enqueue failed {source} {keyword}: {exc}")
                continue
            n += 1
    scan.total_jobs = n
    scan.status = "running" if n else "done"
    db.commit()
    db.refresh(scan)
    return scan
