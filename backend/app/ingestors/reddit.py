from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.ingestors.base import Ingestor, RawPost


class RedditIngestor(Ingestor):
    platform = "reddit"

    def fetch_for_keyword(self, keyword: str, limit: int = 25) -> list[RawPost]:
        settings = get_settings()
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            print("[reddit] missing REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET — skipping")
            return []

        try:
            import praw

            # Web app + installed app: client-credentials, read-only public search.
            # No Reddit username/password. Redirect URI is required for web-app type.
            reddit = praw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent,
                redirect_uri=settings.reddit_redirect_uri,
            )
            reddit.read_only = True
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            results = reddit.subreddit("all").search(
                keyword,
                sort="new",
                time_filter="day",
                limit=min(limit, 50),
            )

            posts: list[RawPost] = []
            for submission in results:
                posted_at = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                if posted_at < cutoff:
                    continue
                posts.append(
                    RawPost(
                        platform=self.platform,
                        external_id=str(submission.id),
                        source=f"r/{submission.subreddit.display_name}",
                        title=submission.title or "",
                        body=submission.selftext or "",
                        url=f"https://www.reddit.com{submission.permalink}",
                        author=str(submission.author) if submission.author else "[deleted]",
                        engagement=int(submission.score or 0),
                        posted_at=posted_at,
                    )
                )
            return posts
        except Exception as exc:  # noqa: BLE001 — platform isolation
            print(f"[reddit] fetch failed for '{keyword}': {exc}")
            return []
