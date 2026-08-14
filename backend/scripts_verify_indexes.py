"""EXPLAIN feed and digest-shaped queries. Needs a running Postgres."""
from sqlalchemy import text

from app.database import engine


FEED = """
EXPLAIN (ANALYZE, BUFFERS)
SELECT posts.id
FROM posts
JOIN watchlist_matches ON watchlist_matches.post_id = posts.id
JOIN watchlists ON watchlists.id = watchlist_matches.watchlist_id
WHERE watchlists.owner_id = 1
  AND watchlists.active IS TRUE
ORDER BY posts.relevance_score DESC NULLS LAST, posts.ingested_at DESC
LIMIT 50
"""

DIGEST = """
EXPLAIN (ANALYZE, BUFFERS)
SELECT posts.id
FROM posts
JOIN watchlist_matches ON watchlist_matches.post_id = posts.id
JOIN watchlists ON watchlists.id = watchlist_matches.watchlist_id
WHERE watchlists.owner_id = 1
  AND watchlists.active IS TRUE
  AND posts.ingested_at >= NOW() - INTERVAL '24 hours'
  AND posts.relevance_score >= 60
ORDER BY posts.relevance_score DESC NULLS LAST
"""


def main() -> None:
    with engine.connect() as conn:
        print("=== feed ===")
        print("\n".join(row[0] for row in conn.execute(text(FEED))))
        print("=== digest ===")
        print("\n".join(row[0] for row in conn.execute(text(DIGEST))))


if __name__ == "__main__":
    main()
