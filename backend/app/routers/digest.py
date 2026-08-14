from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import DigestGroup, DigestOut, PostOut
from app.services import get_digest_for_user

router = APIRouter(tags=["digest"])


@router.get("/digest", response_model=DigestOut)
def digest(
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DigestOut:
    data = get_digest_for_user(db, user.id, hours=hours)
    groups: list[DigestGroup] = []
    for g in data["by_tag"]:
        posts = [
            PostOut(
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
                watchlist_id=wl.id,
                keyword=wl.keyword,
            )
            for post, wl in g["posts"]
        ]
        groups.append(DigestGroup(tag=g["tag"], count=g["count"], posts=posts))
    return DigestOut(hours=data["hours"], total=data["total"], by_tag=groups)
