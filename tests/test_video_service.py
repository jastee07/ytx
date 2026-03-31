from __future__ import annotations

import pytest

from ytx.errors import ApiError
from ytx.models.video import VideoSummary
from ytx.services.video_service import VideoService


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

FAKE_VIDEO = {
    "id": "vidABC",
    "snippet": {
        "title": "My Great Video",
        "publishedAt": "2026-03-10T12:00:00Z",
        "description": "A great video",
        "channelId": "UC999",
    },
    "statistics": {"viewCount": "4200", "likeCount": "88", "commentCount": "12"},
    "status": {"privacyStatus": "public"},
    "contentDetails": {"duration": "PT12M30S"},
}


class FakeDataClient:
    def get_video(self, video_id):
        if video_id == "vidABC":
            return FAKE_VIDEO
        raise ApiError(code="RESOURCE_NOT_FOUND", message=f"Not found: {video_id}")

    def get_videos(self, video_ids):
        return [FAKE_VIDEO] if "vidABC" in video_ids else []


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

def test_get_video_returns_summary() -> None:
    service = VideoService(FakeDataClient(), DictCache())
    video = service.get_video("vidABC")
    assert isinstance(video, VideoSummary)
    assert video.video_id == "vidABC"
    assert video.title == "My Great Video"
    assert video.view_count == 4200
    assert video.like_count == 88
    assert video.duration == "PT12M30S"
    assert video.privacy_status == "public"


def test_get_video_caches_result() -> None:
    class CountingClient(FakeDataClient):
        calls = 0

        def get_video(self, video_id):
            CountingClient.calls += 1
            return FAKE_VIDEO

    cache = DictCache()
    service = VideoService(CountingClient(), cache)
    service.get_video("vidABC")
    service.get_video("vidABC")
    assert CountingClient.calls == 1


def test_get_video_not_found_raises_api_error() -> None:
    service = VideoService(FakeDataClient(), DictCache())
    with pytest.raises(ApiError) as exc:
        service.get_video("missing")
    assert exc.value.code == "RESOURCE_NOT_FOUND"
