"""Step 3: Reddit ingestor verification (requires REDDIT_* env vars)."""
from app.ingestors.reddit import RedditIngestor

ing = RedditIngestor()
posts = ing.fetch_for_keyword("saas", limit=5)
print(f"Reddit posts: {len(posts)}")
for p in posts[:5]:
    print(f"  - [{p.external_id}] r={p.source} | {p.title[:80]} | ↑{p.engagement}")
if not posts:
    print("SKIP/EMPTY: set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in backend/.env")
