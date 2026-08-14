from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawPost:
    platform: str
    external_id: str
    source: str
    title: str
    body: str
    url: str
    author: str
    engagement: int
    posted_at: datetime | None = None
    extras: dict = field(default_factory=dict)


class Ingestor(ABC):
    platform: str

    @abstractmethod
    def fetch_for_keyword(self, keyword: str, limit: int = 25) -> list[RawPost]:
        """Fetch recent posts for a keyword. Must not raise — return [] on failure."""
