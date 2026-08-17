from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.ingestors.base import Ingestor, RawPost


class HackerNewsIngestor(Ingestor):
    platform = "hn"
    API_URL = "https://hn.algolia.com/api/v1/search_by_date"

    def fetch_for_keyword(self, keyword: str, limit: int = 25) -> list[RawPost]:
        posts: list[RawPost] = []
        seen: set[str] = set()
        per = max(12, min(limit, 50) // 2)
        for tags in ("comment", "story"):
            posts.extend(self._search(keyword, tags, per, seen))
        print(f"[hn] '{keyword}' -> {len(posts)} posts")
        return posts[:limit]

    def _search(self, keyword: str, tags: str, limit: int, seen: set[str]) -> list[RawPost]:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(
                    self.API_URL,
                    params={
                        "query": keyword,
                        "tags": tags,
                        "hitsPerPage": min(limit, 50),
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            print(f"[hn] {tags} fetch failed for '{keyword}': {exc}")
            return []

        posts: list[RawPost] = []
        for hit in data.get("hits", []):
            object_id = str(hit.get("objectID") or "")
            if not object_id or object_id in seen:
                continue
            seen.add(object_id)
            created = hit.get("created_at")
            posted_at = datetime.now(timezone.utc)
            if created:
                try:
                    posted_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except ValueError:
                    pass
            title = (hit.get("title") or hit.get("story_title") or "").strip()
            body = (hit.get("comment_text") or hit.get("story_text") or hit.get("url") or "").strip()
            if not title and not body:
                continue
            url = hit.get("story_url") or hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
            if tags == "comment":
                url = f"https://news.ycombinator.com/item?id={object_id}"
            posts.append(
                RawPost(
                    platform=self.platform,
                    external_id=object_id,
                    source="Hacker News",
                    title=title or (body[:120] + ("…" if len(body) > 120 else "")),
                    body=body or title,
                    url=url,
                    author=hit.get("author") or "unknown",
                    engagement=int(hit.get("points") or hit.get("num_comments") or 0),
                    posted_at=posted_at,
                )
            )
        return posts
