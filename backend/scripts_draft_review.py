"""Pull real HN/GitHub posts, draft replies, print a review sheet."""

from __future__ import annotations

from collections import defaultdict

from app.classify import classify_post_fast, draft_reply
from app.config import get_settings
from app.ingestors.github import GitHubIngestor
from app.ingestors.hn import HackerNewsIngestor

QUERIES = [
    ("saas pricing", "hn"),
    ("indie hacker", "hn"),
    ("I wish there was", "hn"),
    ("how do I", "github"),
    ("broken", "github"),
    ("love this", "hn"),
]


def main() -> None:
    settings = get_settings()
    buckets: dict[str, list] = defaultdict(list)
    hn, gh = HackerNewsIngestor(), GitHubIngestor()

    for q, src in QUERIES:
        posts = (hn if src == "hn" else gh).fetch_for_keyword(q, limit=20)
        for p in posts:
            tag = classify_post_fast(p.title, p.body, q)["tag"]
            if tag == "irrelevant":
                continue
            if len(buckets[tag]) >= 8:
                continue
            buckets[tag].append((q, p))

    print("COUNTS", {k: len(v) for k, v in buckets.items()})
    n = 0
    for tag in ("pain", "question", "complaint", "praise"):
        print("\n" + "=" * 72)
        print("TAG", tag)
        for q, p in buckets[tag][:7]:
            n += 1
            draft = draft_reply(p.title, p.body, settings.product_description, tag=tag)
            print("-" * 72)
            print(f"#{n} [{p.platform}] {p.title[:140]}")
            print(f"URL {p.url}")
            print(f"BODY {p.body[:400].replace(chr(10), ' ')}")
            print(f"DRAFT {draft}")
    print(f"\nReviewed {n} drafts")


if __name__ == "__main__":
    main()
