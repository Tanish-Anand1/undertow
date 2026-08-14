from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.classify import draft_reply
from app.config import get_settings
from app.database import get_db
from app.models import Post, User, Watchlist, WatchlistMatch
from app.schemas import DraftReplyOut
from sqlalchemy import select

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/{post_id}/draft-reply", response_model=DraftReplyOut)
def create_draft_reply(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DraftReplyOut:
    # Ensure the post is matched to one of the user's watchlists
    owned = db.execute(
        select(Post)
        .join(WatchlistMatch, WatchlistMatch.post_id == Post.id)
        .join(Watchlist, Watchlist.id == WatchlistMatch.watchlist_id)
        .where(Post.id == post_id)
        .where(Watchlist.owner_id == user.id)
    ).scalar_one_or_none()
    if not owned:
        raise HTTPException(status_code=404, detail="Post not found")

    if owned.draft_text:
        return DraftReplyOut(post_id=post_id, draft=owned.draft_text)

    settings = get_settings()
    draft = draft_reply(
        owned.title,
        owned.body,
        settings.product_description,
        tag=owned.tag,
        source=owned.source,
    )
    owned.draft_text = draft
    db.commit()
    return DraftReplyOut(post_id=post_id, draft=draft)
