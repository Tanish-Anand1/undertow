from __future__ import annotations

import time

import redis

from app.config import get_settings

SOURCE_LIMITS = {
    "hn": (30, 10),
    "github": (8, 10),
    "x": (3, 15),
    "reddit": (4, 10),
}

_memory: dict[str, tuple[int, float]] = {}


def _client() -> redis.Redis | None:
    try:
        r = redis.from_url(get_settings().redis_url, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None


def circuit_open(source: str) -> bool:
    r = _client()
    if r:
        until = r.get(f"circuit:{source}")
        return bool(until and float(until) > time.time())
    until, _ = _memory.get(f"circuit:{source}", (0, 0))
    return until > time.time()


def trip_circuit(source: str, seconds: int = 900, reason: str = "") -> None:
    until = time.time() + seconds
    r = _client()
    if r:
        r.setex(f"circuit:{source}", seconds, str(until))
        if reason:
            r.setex(f"circuit:{source}:reason", seconds, reason)
    _memory[f"circuit:{source}"] = (until, time.time())
    print(f"[circuit] {source} OPEN {seconds}s {reason}")


def circuit_status() -> dict[str, dict]:
    out = {}
    r = _client()
    for source in SOURCE_LIMITS:
        open_ = circuit_open(source)
        reason = ""
        if r:
            reason = r.get(f"circuit:{source}:reason") or ""
        out[source] = {"open": open_, "reason": reason}
    return out


def allow_call(source: str) -> bool:
    max_n, window = SOURCE_LIMITS.get(source, (10, 10))
    r = _client()
    key = f"rl:{source}"
    if r:
        n = r.incr(key)
        if n == 1:
            r.expire(key, window)
        return n <= max_n
    now = time.time()
    count, start = _memory.get(key, (0, now))
    if now - start >= window:
        count, start = 0, now
    count += 1
    _memory[key] = (count, start)
    return count <= max_n


def allow_auth_attempt(key: str) -> bool:
    settings = get_settings()
    max_n = settings.auth_login_max_attempts
    window = settings.auth_login_window_seconds
    r = _client()
    redis_key = f"auth:{key}"
    if r:
        n = r.incr(redis_key)
        if n == 1:
            r.expire(redis_key, window)
        return n <= max_n
    now = time.time()
    count, start = _memory.get(redis_key, (0, now))
    if now - start >= window:
        count, start = 0, now
    count += 1
    _memory[redis_key] = (count, start)
    return count <= max_n
