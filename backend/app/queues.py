from __future__ import annotations

import redis
from rq import Queue, Retry

from app.config import get_settings

QUEUE_NAMES = ("hn", "github", "x", "reddit", "digest")


def redis_conn() -> redis.Redis:
    return redis.from_url(
        get_settings().redis_url,
        socket_connect_timeout=0.25,
        socket_timeout=0.25,
    )


def redis_live() -> bool:
    url = (get_settings().redis_url or "").strip()
    if not url or "localhost" in url or "127.0.0.1" in url:
        return False
    try:
        redis_conn().ping()
        return True
    except Exception:
        return False


def queue(name: str) -> Queue:
    if name not in QUEUE_NAMES:
        raise ValueError(f"unknown queue {name}")
    return Queue(name, connection=redis_conn())


def retry() -> Retry:
    return Retry(max=5, interval=[15, 45, 120, 300, 600])
