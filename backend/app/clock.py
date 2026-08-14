"""Clock process: enqueue ingest/digest onto RQ. Do not crawl inline."""

from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.jobs import send_digest_job
from app.queues import queue, retry
from app.scheduler import enqueue_scheduled_ingest


def tick_ingest() -> None:
    print("[clock] enqueue ingest")
    enqueue_scheduled_ingest()


def tick_digest() -> None:
    print("[clock] enqueue digest")
    queue("digest").enqueue(send_digest_job, retry=retry(), job_timeout=300)


def main() -> None:
    settings = get_settings()
    scheduler = BlockingScheduler()
    scheduler.add_job(
        tick_ingest,
        IntervalTrigger(minutes=settings.ingest_interval_minutes),
        id="ingest",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        tick_digest,
        CronTrigger(hour=settings.digest_hour_utc, minute=0),
        id="digest",
        replace_existing=True,
        max_instances=1,
    )
    print(
        f"[clock] ingest every {settings.ingest_interval_minutes}m, "
        f"digest at {settings.digest_hour_utc}:00 UTC"
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
