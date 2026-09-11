import json
import os
import sqlite3
import time
from contextlib import contextmanager
from threading import Lock
from typing import Any


class DiskCache:
    def __init__(self, db_path: str = "cache/smartpath.db"):
        self.db_path = db_path
        self._lock = Lock()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)
            """)

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get(self, key: str) -> Any | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?",
                (key,)
            ).fetchone()

            if row is None:
                return None

            if row['expires_at'] and row['expires_at'] < time.time():
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                return None

            return json.loads(row['value'])

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expires_at = time.time() + ttl if ttl else None
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), expires_at)
            )
            conn.commit()

    def delete(self, key: str) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()

    def clear_expired(self) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?", (time.time(),))
            conn.commit()
            return cursor.rowcount


_cache_instance: DiskCache | None = None


def init_cache(db_path: str = "cache/smartpath.db") -> DiskCache:
    global _cache_instance
    _cache_instance = DiskCache(db_path)
    return _cache_instance


def get_cache() -> DiskCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = init_cache()
    return _cache_instance
