from __future__ import annotations

from pathlib import Path

from ytx.auth.profiles import ProfileStore


def test_profile_store_round_trip(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profiles.json")
    store.upsert_profile("default", "UC123", "Example", ["scope:a"])
    profile = store.get_profile("default")
    assert profile is not None
    assert profile["channel_id"] == "UC123"
    assert store.default_profile() == "default"
