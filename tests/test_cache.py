from __future__ import annotations

from pathlib import Path

from ytx.cache.sqlite_cache import SQLiteCache


def test_cache_round_trip(tmp_path: Path) -> None:
    cache = SQLiteCache(tmp_path / "cache.db")
    cache.set("analytics_query", "abc", {"ok": True}, ttl_seconds=60)
    assert cache.get("analytics_query", "abc") == {"ok": True}


def test_cache_expiration(tmp_path: Path) -> None:
    cache = SQLiteCache(tmp_path / "cache.db")
    cache.set("analytics_query", "expired", {"ok": True}, ttl_seconds=-1)
    assert cache.get("analytics_query", "expired") is None
