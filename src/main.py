from contextlib import asynccontextmanager
import asyncio
import logging
from typing import List, Union

from fastapi import FastAPI
import uvicorn

from src.models import Event
from src.queue_worker import QueueWorker
from src.dedup_store import DedupStore
from src.storage import EventStorage
from src.stats import Stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


def create_app(dedup_db_path: str = "dedup.db") -> FastAPI:
    queue = asyncio.Queue()
    dedup = DedupStore(db_path=dedup_db_path)
    storage = EventStorage()
    stats = Stats()
    worker = QueueWorker(queue, dedup, storage, stats)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        worker_task = asyncio.create_task(worker.start())
        try:
            yield
        finally:
            worker_task.cancel()
            await asyncio.gather(worker_task, return_exceptions=True)
            dedup.close()

    app = FastAPI(lifespan=lifespan)
    app.state.queue = queue
    app.state.storage = storage
    app.state.stats = stats

    @app.post("/publish")
    async def publish(events: Union[Event, List[Event]]):
        normalized_events = events if isinstance(events, list) else [events]

        for event in normalized_events:
            stats.received += 1
            await queue.put(event)

        return {"message": "Events queued", "count": len(normalized_events)}

    @app.get("/events")
    def get_events(topic: str | None = None):
        if topic is None:
            return storage.get_events()
        return storage.get_events(topic)

    @app.get("/stats")
    def get_stats():
        return stats.snapshot()

    return app


app = create_app()


def main():
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    main()