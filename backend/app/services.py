from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.classify import classify_post_fast
from app.ingestors import get_registered_ingestors
from app.ingestors.base import Ingestor, RawPost
from app.models import Post, Watchlist, WatchlistMatch
from app.security import sanitize_http_url


def _platform_allowed(watchlist: Watchlist, platform: str) -> bool:
    allowed = {p.strip().lower() for p in (watchlist.platforms or "").split(",") if p.strip()}
    return platform.lower() in allowed


def upsert_raw_post(db: Session, raw: RawPost) -> Post:
    stmt = (
        pg_insert(Post)
        .values(
            platform=raw.platform,
            external_id=raw.external_id,
            source=raw.source,
            title=raw.title,
            body=raw.body,
            url=sanitize_http_url(raw.url),
            author=raw.author,
            engagement=raw.engagement,
            posted_at=raw.posted_at,
            classified=False,
        )
        .on_conflict_do_update(
            constraint="uq_posts_platform_external",
            set_={
                "source": raw.source,
                "title": raw.title,
                "body": raw.body,
                "url": sanitize_http_url(raw.url),
                "author": raw.author,
                "engagement": raw.engagement,
                "posted_at": raw.posted_at,
            },
        )
        .returning(Post.id)
    )
    post_id = db.execute(stmt).scalar_one()
    db.flush()
    post = db.get(Post, post_id)
    assert post is not None
    return post


def ensure_match(db: Session, watchlist_id: int, post_id: int, match_score: float) -> None:
    stmt = (
        pg_insert(WatchlistMatch)
        .values(
            watchlist_id=watchlist_id,
            post_id=post_id,
            match_score=match_score,
        )
        .on_conflict_do_update(
            constraint="uq_watchlist_post",
            set_={"match_score": match_score, "matched_at": func.now()},
        )
    )
    db.execute(stmt)


def ingest_source_keyword(
    db: Session,
    ingestor: Ingestor,
    keyword: str,
    limit_per_keyword: int = 30,
) -> dict[str, int]:
    """Crawl one source for one keyword. Classify each post at most once."""
    needle = keyword.strip().lower()
    watchlists = list(
        db.scalars(
            select(Watchlist)
            .where(Watchlist.active.is_(True))
            .where(func.lower(Watchlist.keyword) == needle)
        ).all()
    )
    stats = {"fetched": 0, "upserted": 0, "classified": 0, "matches": 0, "skipped_classified": 0}
    raw_posts = ingestor.fetch_for_keyword(keyword, limit=limit_per_keyword)
    stats["fetched"] = len(raw_posts)
    for raw in raw_posts:
        post = upsert_raw_post(db, raw)
        stats["upserted"] += 1
        if post.classified:
            stats["skipped_classified"] += 1
        else:
            result = classify_post_fast(post.title, post.body, keyword)
            post.tag = result["tag"]
            post.relevance_score = float(result["relevance_score"])
            post.classified = True
            stats["classified"] += 1
        score = float(post.relevance_score or 0)
        for wl in watchlists:
            if not _platform_allowed(wl, raw.platform):
                continue
            ensure_match(db, wl.id, post.id, score)
            stats["matches"] += 1
    db.commit()
    return stats


def run_ingestion_cycle(db: Session, limit_per_keyword: int = 30) -> dict[str, int]:
    """Sync helper for tests/scripts. Production ingest goes through RQ."""
    watchlists = list(db.scalars(select(Watchlist).where(Watchlist.active.is_(True))).all())
    by_keyword: dict[str, list[Watchlist]] = defaultdict(list)
    for wl in watchlists:
        by_keyword[wl.keyword.strip().lower()].append(wl)

    ingestors = get_registered_ingestors()
    stats = {"keywords": len(by_keyword), "fetched": 0, "upserted": 0, "classified": 0, "matches": 0}

    for keyword in by_keyword:
        for ingestor in ingestors:
            part = ingest_source_keyword(db, ingestor, keyword, limit_per_keyword)
            for k in ("fetched", "upserted", "classified", "matches"):
                stats[k] += part[k]

    return stats


def get_user_feed(
    db: Session,
    user_id: int,
    platform: str | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> list[tuple[Post, Watchlist]]:
    q = (
        select(Post, Watchlist)
        .join(WatchlistMatch, WatchlistMatch.post_id == Post.id)
        .join(Watchlist, Watchlist.id == WatchlistMatch.watchlist_id)
        .where(Watchlist.owner_id == user_id)
        .where(Watchlist.active.is_(True))
        .order_by(Post.relevance_score.desc().nulls_last(), Post.ingested_at.desc())
        .limit(limit)
    )
    if platform:
        q = q.where(Post.platform == platform)
    if tag:
        q = q.where(Post.tag == tag)
    return list(db.execute(q).all())


def get_digest_for_user(db: Session, user_id: int, hours: int = 24) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = db.execute(
        select(Post, Watchlist)
        .join(WatchlistMatch, WatchlistMatch.post_id == Post.id)
        .join(Watchlist, Watchlist.id == WatchlistMatch.watchlist_id)
        .where(Watchlist.owner_id == user_id)
        .where(Watchlist.active.is_(True))
        .where(Post.ingested_at >= cutoff)
        .where(Post.relevance_score >= 60)
        .where((Post.tag.is_(None)) | (Post.tag != "irrelevant"))
        .order_by(Post.relevance_score.desc().nulls_last())
    ).all()

    # Deduplicate posts while preserving best score order
    seen: set[int] = set()
    by_tag: dict[str, list] = defaultdict(list)
    for post, wl in rows:
        if post.id in seen:
            continue
        seen.add(post.id)
        tag = post.tag or "pain"
        by_tag[tag].append((post, wl))

    groups = []
    for tag, items in sorted(by_tag.items(), key=lambda x: -len(x[1])):
        groups.append({"tag": tag, "count": len(items), "posts": items})

    return {"hours": hours, "total": len(seen), "by_tag": groups}


def get_user_stats(db: Session, user_id: int) -> dict[str, int]:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    posts_scanned = db.scalar(
        select(func.count(func.distinct(Post.id)))
        .join(WatchlistMatch, WatchlistMatch.post_id == Post.id)
        .join(Watchlist, Watchlist.id == WatchlistMatch.watchlist_id)
        .where(Watchlist.owner_id == user_id)
        .where(Post.ingested_at >= week_ago)
    ) or 0
    high_relevance = db.scalar(
        select(func.count(func.distinct(Post.id)))
        .join(WatchlistMatch, WatchlistMatch.post_id == Post.id)
        .join(Watchlist, Watchlist.id == WatchlistMatch.watchlist_id)
        .where(Watchlist.owner_id == user_id)
        .where(Post.ingested_at >= week_ago)
        .where(Post.relevance_score >= 60)
    ) or 0
    return {
        "posts_scanned": int(posts_scanned),
        "high_relevance_hits": int(high_relevance),
        "replies_drafted": 0,  # stub counter for v1 UI
    }
