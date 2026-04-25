import sqlite3
from threading import Lock


class DedupStore:
    def __init__(self, db_path="dedup.db"):
        self.db_path = db_path
        self._lock = Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS dedup (
            topic TEXT,
            event_id TEXT,
            PRIMARY KEY (topic, event_id)
        )
        """)
        self.conn.commit()

    def is_duplicate(self, topic, event_id):
        with self._lock:
            cursor = self.conn.execute(
                "SELECT 1 FROM dedup WHERE topic=? AND event_id=?",
                (topic, event_id)
            )
            return cursor.fetchone() is not None

    def add(self, topic, event_id):
        with self._lock:
            try:
                self.conn.execute(
                    "INSERT INTO dedup (topic, event_id) VALUES (?, ?)",
                    (topic, event_id)
                )
                self.conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def close(self):
        with self._lock:
            self.conn.close()