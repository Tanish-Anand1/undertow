"""Step 8: X ingestor verification (requires X_BEARER_TOKEN + paid recent-search access)."""
from app.ingestors.x import XIngestor

ing = XIngestor()
posts = ing.fetch_for_keyword("saas", limit=10)
print(f"X posts: {len(posts)}")
for p in posts[:5]:
    print(f"  - [{p.external_id}] @{p.author} | {p.title[:80]} | eng={p.engagement}")
if not posts:
    print(
        "SKIP/EMPTY: X recent search needs a paid API tier and X_BEARER_TOKEN in backend/.env. "
        "Free tier typically cannot call /2/tweets/search/recent."
    )
