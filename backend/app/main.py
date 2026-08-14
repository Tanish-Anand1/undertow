from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.limits import circuit_status
from app.middleware import SecurityHeadersMiddleware
from app.routers import auth, digest, feed, posts, watchlists


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


settings = get_settings()
app = FastAPI(title="Undertow", version="0.2.0", lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(watchlists.router)
app.include_router(feed.router)
app.include_router(digest.router)
app.include_router(posts.router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "undertow",
        "circuits": circuit_status(),
    }
