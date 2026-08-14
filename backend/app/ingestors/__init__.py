from app.ingestors.base import Ingestor, RawPost
from app.ingestors.github import GitHubIngestor
from app.ingestors.hn import HackerNewsIngestor
from app.ingestors.reddit import RedditIngestor
from app.ingestors.x import XIngestor


def get_registered_ingestors() -> list[Ingestor]:
    return [
        HackerNewsIngestor(),
        RedditIngestor(),
        XIngestor(),
        GitHubIngestor(),
    ]


__all__ = [
    "Ingestor",
    "RawPost",
    "HackerNewsIngestor",
    "RedditIngestor",
    "XIngestor",
    "GitHubIngestor",
    "get_registered_ingestors",
]
