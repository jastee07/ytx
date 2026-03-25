from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteCache:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    profile_name TEXT PRIMARY KEY,
                    channel_id TEXT,
                    channel_title TEXT,
                    scopes_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    cache_key TEXT PRIMARY KEY,
                    namespace TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def set(self, namespace: str, key: str, payload: Any, ttl_seconds: int) -> None:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        cache_key = f"{namespace}:{key}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cache_entries(cache_key, namespace, payload_json, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                  payload_json=excluded.payload_json,
                  expires_at=excluded.expires_at,
                  created_at=excluded.created_at
                """,
                (cache_key, namespace, json.dumps(payload), expires_at.isoformat(), now.isoformat()),
            )

    def get(self, namespace: str, key: str) -> Any | None:
        cache_key = f"{namespace}:{key}"
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json, expires_at FROM cache_entries WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if not row:
            return None
        payload_json, expires_at = row
        if datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
            self.delete(namespace, key)
            return None
        return json.loads(payload_json)

    def delete(self, namespace: str, key: str) -> None:
        cache_key = f"{namespace}:{key}"
        with self._connect() as conn:
            conn.execute("DELETE FROM cache_entries WHERE cache_key = ?", (cache_key,))
