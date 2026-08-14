"""Confirm classification is stored on Post and not re-run on a second watchlist match."""
from app.classify import classify_post_fast
from app.database import SessionLocal
from app.ingestors.base import RawPost
from app.models import Post
from app.services import upsert_raw_post


def main() -> None:
    db = SessionLocal()
    try:
        raw = RawPost(
            platform="hn",
            external_id="cache-test-1",
            source="HN",
            title="How do I fix auth friction in oauth",
            body="struggling with oauth tickets",
            url="https://example.com/p",
            author="tester",
            engagement=1,
            posted_at=None,
        )
        post = upsert_raw_post(db, raw)
        if not post.classified:
            result = classify_post_fast(post.title, post.body, "auth")
            post.tag = result["tag"]
            post.relevance_score = float(result["relevance_score"])
            post.classified = True
        db.commit()
        pid = post.id
        classified_before = db.get(Post, pid).classified
        # second match path
        post2 = upsert_raw_post(db, raw)
        skipped = post2.classified
        print({"classified_before": classified_before, "second_upsert_already_classified": skipped, "same_id": post2.id == pid})
        assert skipped and classified_before
    finally:
        db.close()


if __name__ == "__main__":
    main()
