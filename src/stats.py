import time


class Stats:
    def __init__(self):
        self.received = 0
        self.unique_processed = 0
        self.duplicate_dropped = 0
        self.topics = set()
        self.start_time = time.time()

    def uptime(self):
        return time.time() - self.start_time

    def snapshot(self):
        return {
            "received": self.received,
            "unique_processed": self.unique_processed,
            "duplicate_dropped": self.duplicate_dropped,
            "topics": sorted(self.topics),
            "uptime": self.uptime(),
        }