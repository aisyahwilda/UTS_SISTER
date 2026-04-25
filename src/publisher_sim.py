import argparse
import asyncio
import math
import random
from datetime import datetime, timezone

import httpx


def build_event(event_id: str, index: int):
    return {
        "topic": "demo",
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "publisher-sim",
        "payload": {"index": index, "event_id": event_id},
    }


async def publish_events(base_url: str, total: int, duplicate_ratio: float):
    duplicate_ratio = max(0.0, min(duplicate_ratio, 0.95))
    unique_count = max(1, int(round(total * (1 - duplicate_ratio))))
    duplicate_count = total - unique_count

    unique_event_ids = [f"evt-{index}" for index in range(unique_count)]
    events = [build_event(event_id, index) for index, event_id in enumerate(unique_event_ids)]

    if duplicate_count > 0:
        duplicate_ids = random.choices(unique_event_ids, k=duplicate_count)
        events.extend(
            build_event(event_id, unique_count + offset)
            for offset, event_id in enumerate(duplicate_ids)
        )

    random.shuffle(events)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{base_url}/publish", json=events)
        response.raise_for_status()
        print(response.json())

        stats = await client.get(f"{base_url}/stats")
        print(stats.json())


def main():
    parser = argparse.ArgumentParser(description="Simulate at-least-once delivery with duplicates")
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--total", type=int, default=5000)
    parser.add_argument("--duplicate-ratio", type=float, default=0.2)
    args = parser.parse_args()

    asyncio.run(publish_events(args.base_url, args.total, args.duplicate_ratio))


if __name__ == "__main__":
    main()
