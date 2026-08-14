"""Step 2 verification: HN ingest + classify + feed."""
from app.auth import hash_password
from app.database import SessionLocal
from app.ingestors.hn import HackerNewsIngestor
from app.models import User, Watchlist
from app.services import get_user_feed, run_ingestion_cycle

db = SessionLocal()
try:
    # Smoke-test raw HN API
    hn = HackerNewsIngestor()
    raw = hn.fetch_for_keyword("saas", limit=5)
    print(f"HN raw posts: {len(raw)}")
    for p in raw[:3]:
        print(f"  - [{p.external_id}] {p.title[:80]} (pts={p.engagement})")

    email = "demo@undertow.local"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, hashed_password=hash_password("password123"))
        db.add(user)
        db.commit()
        db.refresh(user)

    wl = (
        db.query(Watchlist)
        .filter(Watchlist.owner_id == user.id, Watchlist.keyword == "saas", Watchlist.active.is_(True))
        .first()
    )
    if not wl:
        wl = Watchlist(owner_id=user.id, keyword="saas", platforms="hn", active=True)
        db.add(wl)
        db.commit()

    stats = run_ingestion_cycle(db, limit_per_keyword=10)
    print("ingestion stats:", stats)

    feed = get_user_feed(db, user.id, platform="hn", limit=5)
    print(f"feed rows: {len(feed)}")
    for post, w in feed:
        print(
            f"  - score={post.relevance_score} tag={post.tag} | {post.title[:70]} | {post.url}"
        )
finally:
    db.close()
