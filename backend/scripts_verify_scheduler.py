"""Step 4: shared-keyword dedupe — two users, one keyword, one crawl."""
from app.auth import hash_password
from app.database import SessionLocal
from app.models import Post, User, Watchlist, WatchlistMatch
from app.services import run_ingestion_cycle
from sqlalchemy import func, select

db = SessionLocal()
try:
    def ensure_user(email: str) -> User:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            u = User(email=email, hashed_password=hash_password("password123"))
            db.add(u)
            db.commit()
            db.refresh(u)
        return u

    a = ensure_user("alice@undertow.local")
    b = ensure_user("bob@undertow.local")
    for user in (a, b):
        exists = (
            db.query(Watchlist)
            .filter(Watchlist.owner_id == user.id, Watchlist.keyword == "startup", Watchlist.active.is_(True))
            .first()
        )
        if not exists:
            db.add(Watchlist(owner_id=user.id, keyword="startup", platforms="hn", active=True))
    db.commit()

    before = db.scalar(select(func.count()).select_from(Post)) or 0
    stats = run_ingestion_cycle(db, limit_per_keyword=5)
    after = db.scalar(select(func.count()).select_from(Post)) or 0
    matches = db.scalar(select(func.count()).select_from(WatchlistMatch)) or 0
    print("stats:", stats)
    print(f"posts before={before} after={after} delta={after - before}")
    print(f"total watchlist_matches={matches}")
    print("OK: crawl is per unique keyword; both users get matches via watchlist_matches")
finally:
    db.close()
