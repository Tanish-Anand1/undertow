from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.limits import circuit_status
from app.middleware import SecurityHeadersMiddleware
from app.database import Base, engine
from app.models import SiteVisitor
from app.routers import admin, auth, digest, feed, posts, presence, watchlists


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Base.metadata.create_all(bind=engine, tables=[SiteVisitor.__table__])
    yield


settings = get_settings()
app = FastAPI(title="Sudo", version="0.2.0", lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://((www\.)?trysudo\.in|.*\.vercel\.app)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(presence.router)
app.include_router(watchlists.router)
app.include_router(feed.router)
app.include_router(digest.router)
app.include_router(posts.router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "sudo",
        "circuits": circuit_status(),
    }
