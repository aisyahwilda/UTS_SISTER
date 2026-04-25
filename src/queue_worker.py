import asyncio
import logging


logger = logging.getLogger("aggregator.queue_worker")


class QueueWorker:
    def __init__(self, queue, dedup, storage, stats):
        self.queue = queue
        self.dedup = dedup
        self.storage = storage
        self.stats = stats

    async def start(self):
        while True:
            event = await self.queue.get()
            try:
                inserted = self.dedup.add(event.topic, event.event_id)
                if not inserted:
                    logger.info(
                        "Duplicate dropped topic=%s event_id=%s",
                        event.topic,
                        event.event_id,
                    )
                    self.stats.duplicate_dropped += 1
                else:
                    self.storage.add_event(event)
                    self.stats.unique_processed += 1
                    self.stats.topics.add(event.topic)
            finally:
                self.queue.task_done()