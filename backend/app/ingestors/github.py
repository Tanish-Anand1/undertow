from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.ingestors.base import Ingestor, RawPost


class GitHubIngestor(Ingestor):
    """Public GitHub issue search — a legal slice of the open web, keyword-scoped."""

    platform = "github"
    API_URL = "https://api.github.com/search/issues"

    def fetch_for_keyword(self, keyword: str, limit: int = 25) -> list[RawPost]:
        q = f"{keyword} is:issue is:open"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(
                    self.API_URL,
                    params={"q": q, "sort": "updated", "order": "desc", "per_page": min(limit, 30)},
                    headers={
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "undertow-research/0.1",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                )
                if resp.status_code >= 400:
                    print(f"[github] search {resp.status_code}")
                    return []
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            print(f"[github] fetch failed for '{keyword}': {exc}")
            return []

        posts: list[RawPost] = []
        for item in data.get("items", []) or []:
            issue_id = str(item.get("id") or "")
            if not issue_id:
                continue
            created = item.get("updated_at") or item.get("created_at")
            posted_at = datetime.now(timezone.utc)
            if created:
                try:
                    posted_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except ValueError:
                    pass
            title = (item.get("title") or "").strip()
            body = (item.get("body") or "")[:2000]
            user = (item.get("user") or {}).get("login") or "unknown"
            url = item.get("html_url") or ""
            repo = ""
            if "github.com/" in url:
                parts = url.split("github.com/")[-1].split("/issues")[0]
                repo = parts
            posts.append(
                RawPost(
                    platform=self.platform,
                    external_id=issue_id,
                    source=f"GitHub · {repo}" if repo else "GitHub",
                    title=title,
                    body=body or title,
                    url=url,
                    author=user,
                    engagement=int(item.get("comments") or 0),
                    posted_at=posted_at,
                )
            )
        print(f"[github] '{keyword}' -> {len(posts)} issues")
        return posts
