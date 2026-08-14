from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import unquote

import httpx
import requests
from requests_oauthlib import OAuth1

from app.config import get_settings
from app.ingestors.base import Ingestor, RawPost

STATUS_RE = re.compile(r"(?:x|twitter)\.com/(?:#!/)?([^/\s]+)/status(?:es)?/(\d+)", re.I)
_OFFICIAL_DEAD = False


class XIngestor(Ingestor):
    """X search: official API first, then public tweet URLs found via HN Algolia."""

    platform = "x"
    V2_URL = "https://api.twitter.com/2/tweets/search/recent"
    TOKEN_URL = "https://api.twitter.com/oauth2/token"

    def fetch_for_keyword(self, keyword: str, limit: int = 25) -> list[RawPost]:
        from app.limits import circuit_open, trip_circuit

        global _OFFICIAL_DEAD
        settings = get_settings()
        cap = min(max(limit, 8), 20)
        posts: list[RawPost] = []
        if not _OFFICIAL_DEAD and not circuit_open("x"):
            posts = self._official_search(settings, keyword, cap)
            if not posts:
                _OFFICIAL_DEAD = True
                trip_circuit("x", 900, reason="official search empty or limited")
        if posts:
            print(f"[x] official search '{keyword}' -> {len(posts)}")
            return posts
        posts = self._public_search(keyword, cap)
        print(f"[x] public search '{keyword}' -> {len(posts)}")
        return posts

    def _official_search(self, settings, keyword: str, limit: int) -> list[RawPost]:
        params_v2 = {
            "query": f"{keyword} -is:retweet lang:en",
            "max_results": min(max(limit, 10), 100),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username",
        }
        bearer = self._bearer(settings)
        if bearer:
            data = self._get_json(
                self.V2_URL,
                params=params_v2,
                headers={"Authorization": f"Bearer {bearer}"},
            )
            if data and data.get("data"):
                return self._parse_v2(data)
        if self._has_oauth(settings):
            try:
                resp = requests.get(
                    self.V2_URL,
                    params=params_v2,
                    auth=self._oauth(settings),
                    timeout=8,
                )
                if resp.status_code == 200 and resp.json().get("data"):
                    return self._parse_v2(resp.json())
                print(f"[x] v2 oauth {resp.status_code}")
            except Exception as exc:  # noqa: BLE001
                print(f"[x] v2 oauth failed: {exc}")
        return []

    def _bearer(self, settings) -> str:
        pasted = unquote((settings.x_bearer_token or "").strip())
        if settings.x_consumer_key and settings.x_consumer_secret:
            try:
                resp = requests.post(
                    self.TOKEN_URL,
                    data={"grant_type": "client_credentials"},
                    auth=(settings.x_consumer_key, settings.x_consumer_secret),
                    timeout=8,
                )
                if resp.status_code == 200:
                    token = (resp.json() or {}).get("access_token") or ""
                    if token:
                        return token
            except Exception:
                pass
        return pasted

    def _has_oauth(self, settings) -> bool:
        return all(
            [
                settings.x_consumer_key,
                settings.x_consumer_secret,
                settings.x_access_token,
                settings.x_access_token_secret,
            ]
        )

    def _oauth(self, settings) -> OAuth1:
        return OAuth1(
            settings.x_consumer_key,
            settings.x_consumer_secret,
            settings.x_access_token,
            settings.x_access_token_secret,
        )

    def _get_json(self, url: str, params=None, headers=None) -> dict | None:
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(url, params=params, headers=headers)
            if resp.status_code >= 400:
                print(f"[x] recent {resp.status_code}")
                if resp.status_code in (402, 429, 503):
                    from app.limits import trip_circuit

                    trip_circuit("x", 900, reason=f"http {resp.status_code}")
                return None
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            print(f"[x] get failed: {exc}")
            return None

    def _public_search(self, keyword: str, limit: int) -> list[RawPost]:
        found = self._discover(keyword, limit)
        posts: list[RawPost] = []
        seen: set[str] = set()
        for tweet_id, author_hint, title in found:
            if tweet_id in seen:
                continue
            seen.add(tweet_id)
            author = (author_hint or "unknown").lstrip("@")
            text = (title or f"Post by @{author}").strip()
            posts.append(
                RawPost(
                    platform=self.platform,
                    external_id=tweet_id,
                    source="X",
                    title=text[:120],
                    body=text,
                    url=f"https://x.com/{author}/status/{tweet_id}",
                    author=author,
                    engagement=0,
                    posted_at=datetime.now(timezone.utc),
                )
            )
            if len(posts) >= limit:
                break
        return posts

    def _discover(self, keyword: str, want: int) -> list[tuple[str, str, str]]:
        found: list[tuple[str, str, str]] = []
        seen: set[str] = set()
        queries = [f"{keyword} x.com/status", f"{keyword} twitter.com/status"]
        try:
            with httpx.Client(timeout=10.0) as client:
                for q in queries:
                    resp = client.get(
                        "https://hn.algolia.com/api/v1/search",
                        params={"query": q, "hitsPerPage": 30},
                    )
                    if resp.status_code != 200:
                        continue
                    for hit in resp.json().get("hits", []):
                        title = (hit.get("title") or hit.get("story_title") or "").strip()
                        blob = " ".join(
                            str(hit.get(k) or "")
                            for k in ("title", "url", "story_text", "comment_text", "story_url")
                        )
                        for author, tid in STATUS_RE.findall(blob):
                            if tid in seen:
                                continue
                            seen.add(tid)
                            found.append((tid, author, title))
                            if len(found) >= want:
                                return found
        except Exception as exc:  # noqa: BLE001
            print(f"[x] discover failed: {exc}")
        return found

    def _parse_v2(self, data: dict) -> list[RawPost]:
        users = {
            u["id"]: u.get("username", "unknown")
            for u in data.get("includes", {}).get("users", [])
        }
        posts: list[RawPost] = []
        for tweet in data.get("data", []) or []:
            tweet_id = str(tweet.get("id") or "")
            if not tweet_id:
                continue
            created = tweet.get("created_at")
            posted_at = datetime.now(timezone.utc)
            if created:
                try:
                    posted_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except ValueError:
                    pass
            metrics = tweet.get("public_metrics") or {}
            engagement = int(metrics.get("like_count", 0)) + int(metrics.get("retweet_count", 0))
            author = users.get(tweet.get("author_id"), "unknown")
            text = tweet.get("text") or ""
            posts.append(
                RawPost(
                    platform=self.platform,
                    external_id=tweet_id,
                    source="X",
                    title=text[:120],
                    body=text,
                    url=f"https://x.com/{author}/status/{tweet_id}",
                    author=author,
                    engagement=engagement,
                    posted_at=posted_at,
                )
            )
        return posts
