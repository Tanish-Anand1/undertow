from __future__ import annotations

import re
from urllib.parse import urlparse

_DEVICE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")


def sanitize_http_url(url: str | None, *, max_len: int = 2000) -> str:
    """Allow only http(s) URLs. Blocks javascript:, data:, and protocol-relative tricks."""
    raw = (url or "").strip()
    if not raw or len(raw) > max_len:
        return ""
    if raw.startswith("//"):
        return ""
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        return ""
    if not parsed.netloc or parsed.netloc.startswith("."):
        return ""
    return raw


def sanitize_keyword(value: str, *, max_len: int = 255) -> str:
    cleaned = " ".join((value or "").split())
    cleaned = "".join(ch for ch in cleaned if ch.isprintable() and ch != "\x00")
    return cleaned[:max_len].strip()


ALLOWED_PLATFORMS = frozenset({"hn", "github", "x", "reddit"})
ALLOWED_TAGS = frozenset({"pain", "question", "complaint", "praise", "irrelevant"})


def sanitize_platform(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    return v if v in ALLOWED_PLATFORMS else None


def sanitize_tag(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    return v if v in ALLOWED_TAGS else None


def sanitize_device_id(value: str) -> str | None:
    v = (value or "").strip()
    return v if _DEVICE_ID_RE.match(v) else None
