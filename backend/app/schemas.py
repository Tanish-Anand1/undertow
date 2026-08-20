from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = Field(default=None, max_length=120)


class UserOut(BaseModel):
    id: int
    email: EmailStr | None = None
    name: str | None = None
    is_guest: bool
    email_verified: bool = True
    is_guest: bool = False
    guest_scans_used: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GuestUpgradeIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8)


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    password: str = Field(min_length=8)


class VerifyEmailIn(BaseModel):
    token: str


class ScanOut(BaseModel):
    id: int
    status: str
    total_jobs: int
    finished_jobs: int
    error: str | None = None


class WatchlistCreate(BaseModel):
    keyword: str = Field(min_length=1, max_length=255)
    platforms: list[str] = Field(default_factory=lambda: ["hn", "reddit", "x"])


class WatchlistOut(BaseModel):
    id: int
    keyword: str
    platforms: list[str]
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PostOut(BaseModel):
    id: int
    platform: str
    source: str
    title: str
    body: str
    url: str
    author: str
    engagement: int
    posted_at: datetime | None
    ingested_at: datetime
    tag: str | None
    relevance_score: float | None
    watchlist_id: int | None = None
    keyword: str | None = None

    model_config = {"from_attributes": True}


class DigestGroup(BaseModel):
    tag: str
    count: int
    posts: list[PostOut]


class DigestOut(BaseModel):
    hours: int
    total: int
    by_tag: list[DigestGroup]


class DraftReplyOut(BaseModel):
    post_id: int
    draft: str


class StatsOut(BaseModel):
    posts_scanned: int
    high_relevance_hits: int
    replies_drafted: int
    x_circuit_open: bool = False
