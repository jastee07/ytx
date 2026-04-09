from __future__ import annotations


from ytx.errors import ApiError
from ytx.models.channel import ChannelProfile
from ytx.models.video import VideoSummary
from ytx.services.channel_service import ChannelService


# ---------------------------------------------------------------------------
# Fakes
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
        for v in FAKE_VIDEOS:
            if v["id"] == video_id:
                return v
        raise ApiError(code="RESOURCE_NOT_FOUND", message=f"Not found: {video_id}")


class DictCache:
    def __init__(self):
        self.data = {}

    def get(self, namespace, key):
        return self.data.get((namespace, key))

    def set(self, namespace, key, payload, ttl_seconds):
        self.data[(namespace, key)] = payload


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_channel_returns_profile() -> None:
    service = ChannelService(FakeDataClient(), DictCache())
    profile = service.get_channel("default")
    assert isinstance(profile, ChannelProfile)
    assert profile.channel_id == "UC123"
    assert profile.title == "Test Channel"
    assert profile.subscriber_count == 1000
    assert profile.view_count == 50000
    assert profile.custom_url == "@testchannel"


def test_get_channel_caches_result() -> None:
    class CountingClient(FakeDataClient):
        calls = 0

        def get_mine_channel(self):
            CountingClient.calls += 1
            return FAKE_CHANNEL

    cache = DictCache()
    service = ChannelService(CountingClient(), cache)
    service.get_channel("default")
    service.get_channel("default")
    assert CountingClient.calls == 1


def test_list_recent_videos_returns_summaries() -> None:
    service = ChannelService(FakeDataClient(), DictCache())
    videos, next_token = service.list_recent_videos("default", limit=10)
    assert len(videos) == 2
    assert all(isinstance(v, VideoSummary) for v in videos)
    assert videos[0].video_id == "vid1"
    assert videos[0].view_count == 100
    assert next_token is None


def test_list_recent_videos_respects_limit() -> None:
    service = ChannelService(FakeDataClient(), DictCache())
    videos, _ = service.list_recent_videos("default", limit=1)
    assert len(videos) == 1
    assert videos[0].video_id == "vid1"


def test_list_recent_videos_caches_result() -> None:
    class CountingClient(FakeDataClient):
        calls = 0

        def list_playlist_items(self, playlist_id, max_results, page_token=None):
            CountingClient.calls += 1
            return FAKE_PLAYLIST_RESPONSE

    cache = DictCache()
    service = ChannelService(CountingClient(), cache)
    service.list_recent_videos("default", limit=10)
    service.list_recent_videos("default", limit=10)
    assert CountingClient.calls == 1
