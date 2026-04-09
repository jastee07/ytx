from __future__ import annotations

from ytx.clients.youtube_data import YouTubeDataClient
from ytx.models.video import VideoSummary
from ytx.services.channel_service import normalize_video


class VideoService:
    def __init__(self, client: YouTubeDataClient, cache) -> None:
        self.client = client
        self.cache = cache

    def get_video(self, video_id: str) -> VideoSummary:
        cached = self.cache.get("video_details", video_id)
        if cached:
            return VideoSummary.model_validate(cached)
        video = normalize_video(self.client.get_video(video_id))
        self.cache.set(
            "video_details", video_id, video.model_dump(), ttl_seconds=30 * 60
        )
        return video
