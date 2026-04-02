from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

import json
import re
import unittest.mock

import pytest

YT_READONLY = "https://www.googleapis.com/auth/youtube.readonly"
YT_ANALYTICS = "https://www.googleapis.com/auth/yt-analytics.readonly"
ALL_SCOPES = [YT_READONLY, YT_ANALYTICS]

# ---------------------------------------------------------------------------
# Shared fake API data
# ---------------------------------------------------------------------------

FAKE_CHANNEL = {
    "id": "UC123",
    "snippet": {
        "title": "Test Channel",
        "publishedAt": "2021-01-01T00:00:00Z",
        "country": "US",
    },
    "statistics": {
        "subscriberCount": "1000",
        "videoCount": "10",
        "viewCount": "50000",
    },
    "brandingSettings": {"channel": {"customUrl": "@testchannel"}},
    "contentDetails": {"relatedPlaylists": {"uploads": "UUPL123"}},
}

FAKE_PLAYLIST_RESPONSE = {
    "items": [
        {"contentDetails": {"videoId": "vid1"}},
        {"contentDetails": {"videoId": "vid2"}},
    ],
    "nextPageToken": None,
}

FAKE_VIDEOS = [
    {
        "id": "vid1",
        "snippet": {
            "title": "Video One",
            "publishedAt": "2026-03-01T00:00:00Z",
            "description": "desc1",
            "channelId": "UC123",
        },
        "statistics": {"viewCount": "100", "likeCount": "5", "commentCount": "2"},
        "status": {"privacyStatus": "public"},
        "contentDetails": {"duration": "PT5M"},
    },
    {
        "id": "vid2",
        "snippet": {
            "title": "Video Two",
            "publishedAt": "2026-02-15T00:00:00Z",
            "description": "desc2",
            "channelId": "UC123",
        },
        "statistics": {"viewCount": "200", "likeCount": "10", "commentCount": "4"},
        "status": {"privacyStatus": "public"},
        "contentDetails": {"duration": "PT8M"},
    },
]

# columnHeaders use Google API names; "views" maps to itself so this is simple.
FAKE_ANALYTICS_RESPONSE = {
    "columnHeaders": [{"name": "views", "dataType": "INTEGER"}],
    "rows": [[500]],
}

# ---------------------------------------------------------------------------
# Fake classes
# ---------------------------------------------------------------------------


def make_profile(name="default", channel_id="UC123", title="Test Channel", scopes=None):
    return {
        "profile_name": name,
        "channel_id": channel_id,
        "channel_title": title,
        "granted_scopes": scopes if scopes is not None else ALL_SCOPES,
    }


class FakeProfileStore:
    def __init__(self, profiles=None, default="default"):
        self._profiles = profiles if profiles is not None else {"default": make_profile()}
        self._default = default

    def get_profile(self, name):
        return self._profiles.get(name)

    def list_profiles(self):
        return list(self._profiles.values())

    def default_profile(self):
        return self._default

    def set_default_profile(self, name):
        self._default = name

    def upsert_profile(self, name, **kwargs):
        entry = {"profile_name": name, **kwargs}
        self._profiles[name] = entry
        return entry

    def delete_profile(self, name):
        self._profiles.pop(name, None)


class FakeSecretStore:
    def __init__(self, data=None):
        self._data = data or {}

    def load_json(self, name):
        return self._data.get(name)

    def save_json(self, name, payload):
        self._data[name] = payload

    def delete(self, name):
        self._data.pop(name, None)


class FakeCache:
    def __init__(self):
        self.store = {}

    def get(self, ns, key):
        return self.store.get((ns, key))

    def set(self, ns, key, payload, ttl_seconds):
        self.store[(ns, key)] = payload

    def list_all(self):
        return [
            {"namespace": ns, "cache_key": f"{ns}:{key}", "expires_at": "2099-01-01T00:00:00+00:00", "created_at": "2026-01-01T00:00:00+00:00"}
            for (ns, key) in self.store
        ]

    def clear(self, namespace=None):
        if namespace:
            keys = [(ns, k) for (ns, k) in list(self.store) if ns == namespace]
        else:
            keys = list(self.store)
        for k in keys:
            del self.store[k]
        return len(keys)


class FakeDataClient:
    def get_mine_channel(self):
        return FAKE_CHANNEL

    def get_uploads_playlist_id(self):
        return "UUPL123"

    def list_playlist_items(self, playlist_id, max_results, page_token=None):
        return FAKE_PLAYLIST_RESPONSE

    def get_videos(self, video_ids):
        return [v for v in FAKE_VIDEOS if v["id"] in video_ids]

    def get_video(self, video_id):
        from ytx.errors import ApiError

        for v in FAKE_VIDEOS:
            if v["id"] == video_id:
                return v
        raise ApiError(code="RESOURCE_NOT_FOUND", message=f"Not found: {video_id}")


class FakeAnalyticsClient:
    def query(self, **kwargs):
        return FAKE_ANALYTICS_RESPONSE


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app_ctx(tmp_path):
    """A fully-wired AppContext with no real filesystem access."""
    from ytx.config import AppContext, AppPaths, Settings

    ctx = object.__new__(AppContext)  # bypass __init__
    ctx.paths = AppPaths(
        root=tmp_path,
        config_toml=tmp_path / "config.toml",
        profiles_json=tmp_path / "profiles.json",
        cache_db=tmp_path / "cache.db",
        credentials_dir=tmp_path / "credentials",
    )
    ctx.settings = Settings()
    ctx.profile_store = FakeProfileStore()
    ctx.secret_store = FakeSecretStore()
    ctx.cache = FakeCache()
    return ctx


@pytest.fixture(autouse=True)
def no_color(monkeypatch):
    """Disable Rich ANSI codes so JSON parsing works on raw output."""
    monkeypatch.setenv("NO_COLOR", "1")
