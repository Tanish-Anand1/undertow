from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.emailer import build_digest_email_body, send_email
from app.models import User
from app.services import get_digest_for_user


def run_digest(db: Session, user_id: int | None = None) -> dict:
    settings = get_settings()
    q = db.query(User)
    if user_id is not None:
        q = q.filter(User.id == user_id)
    users = q.all()
    sent = 0
    skipped = 0
    for user in users:
        hours = 24
        if user.last_digest_at:
            delta = datetime.now(timezone.utc) - user.last_digest_at
            hours = max(1, min(168, int(delta.total_seconds() // 3600) or 1))
        digest = get_digest_for_user(db, user.id, hours=hours)
        if settings.digest_skip_empty and not digest["total"]:
            skipped += 1
            continue
        body = build_digest_email_body(user.email, digest)
        send_email(user.email, "Your Sudo daily digest", body)
        user.last_digest_at = datetime.now(timezone.utc)
        sent += 1
    db.commit()
    return {"users": len(users), "sent": sent, "skipped_empty": skipped}
