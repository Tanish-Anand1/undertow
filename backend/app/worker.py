"""RQ worker. Run separately from uvicorn.

    cd backend
    .venv/Scripts/python -m app.worker
    # or: rq worker hn github x reddit digest --url $REDIS_URL
"""

from __future__ import annotations

from rq import Worker

from app.queues import QUEUE_NAMES, redis_conn


def main() -> None:
    Worker(list(QUEUE_NAMES), connection=redis_conn()).work(with_scheduler=True)


if __name__ == "__main__":
    main()
