from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import User, Watchlist
from app.schemas import WatchlistCreate, WatchlistOut
from app.security import sanitize_keyword

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


def _to_out(wl: Watchlist) -> WatchlistOut:
    platforms = [p.strip() for p in (wl.platforms or "").split(",") if p.strip()]
    return WatchlistOut(
        id=wl.id,
        keyword=wl.keyword,
        platforms=platforms,
        active=wl.active,
        created_at=wl.created_at,
    )


@router.post("", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
def create_watchlist(
    payload: WatchlistCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WatchlistOut:
    settings = get_settings()
    active_count = db.scalar(
        select(func.count(Watchlist.id))
        .where(Watchlist.owner_id == user.id)
        .where(Watchlist.active.is_(True))
    ) or 0
    if active_count >= settings.max_keywords_per_user:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Keyword cap reached ({settings.max_keywords_per_user}). "
                "Remove a keyword before adding another."
            ),
        )
    keyword = sanitize_keyword(payload.keyword)
    if len(keyword) < 2:
        raise HTTPException(status_code=400, detail="Keyword is too short.")
    platforms = ",".join(p.strip().lower() for p in payload.platforms if p.strip()) or "hn,github,x"
    wl = Watchlist(
        owner_id=user.id,
        keyword=keyword,
        platforms=platforms,
        active=True,
    )
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return _to_out(wl)


@router.get("", response_model=list[WatchlistOut])
def list_watchlists(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[WatchlistOut]:
    rows = db.scalars(
        select(Watchlist)
        .where(Watchlist.owner_id == user.id)
        .where(Watchlist.active.is_(True))
        .order_by(Watchlist.created_at.desc())
    ).all()
    return [_to_out(wl) for wl in rows]


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    wl = db.get(Watchlist, watchlist_id)
    if not wl or wl.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    wl.active = False
    db.commit()
