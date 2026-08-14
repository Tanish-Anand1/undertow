"""API process does not crawl. Clock + RQ workers own ingest/digest."""

from __future__ import annotations

from app.database import SessionLocal
from app.jobs import enqueue_scan, send_digest_job
from app.queues import queue, retry


def enqueue_scheduled_ingest() -> None:
    db = SessionLocal()
    try:
        enqueue_scan(db, user_id=None)
    finally:
        db.close()


def job_ingest() -> None:
    enqueue_scheduled_ingest()


def job_daily_digest() -> None:
    queue("digest").enqueue(send_digest_job, retry=retry(), job_timeout=300)


def start_scheduler() -> None:
    return


def stop_scheduler() -> None:
    return
