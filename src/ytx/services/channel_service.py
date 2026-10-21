from __future__ import annotations

from typing import Any

from ytx.clients.youtube_data import YouTubeDataClient
from ytx.models.channel import ChannelProfile
from ytx.models.video import VideoSummary
from ytx.utils.paging import clamp_page_size


def normalize_channel(channel: dict[str, Any]) -> ChannelProfile:
    snippet = channel.get("snippet", {})
    stats = channel.get("statistics", {})
    branding = channel.get("brandingSettings", {}).get("channel", {})
    return ChannelProfile(
        channel_id=channel["id"],
        title=snippet.get("title", ""),
        custom_url=branding.get("customUrl"),
        published_at=snippet.get("publishedAt"),
        country=snippet.get("country"),
        subscriber_count=_to_int(stats.get("subscriberCount")),
        video_count=_to_int(stats.get("videoCount")),
        view_count=_to_int(stats.get("viewCount")),
    )


def normalize_video(video: dict[str, Any]) -> VideoSummary:
    snippet = video.get("snippet", {})
    stats = video.get("statistics", {})
    status = video.get("status", {})
    content = video.get("contentDetails", {})
    return VideoSummary(
        video_id=video["id"],
        title=snippet.get("title", ""),
        published_at=snippet.get("publishedAt", ""),
        description=snippet.get("description"),
        channel_id=snippet.get("channelId", ""),
        privacy_status=status.get("privacyStatus"),
        duration=content.get("duration"),
        view_count=_to_int(stats.get("viewCount")),
        like_count=_to_int(stats.get("likeCount")),
        comment_count=_to_int(stats.get("commentCount")),
    )


class ChannelService:
    def __init__(self, client: YouTubeDataClient, cache) -> None:
        self.client = client
        self.cache = cache

    def get_channel(self, profile_name: str) -> ChannelProfile:
        cache_key = profile_name
        cached = self.cache.get("channel_profile", cache_key)
        if cached:
            return ChannelProfile.model_validate(cached)
        channel = normalize_channel(self.client.get_mine_channel())
        self.cache.set(
            "channel_profile", cache_key, channel.model_dump(), ttl_seconds=24 * 60 * 60
        )
        return channel

    def list_recent_videos(
        self, profile_name: str, limit: int, page_token: str | None = None
    ) -> tuple[list[VideoSummary], str | None]:
        cache_key = f"{profile_name}:limit={limit}:page_token={page_token or ''}"
        cached = self.cache.get("channel_videos", cache_key)
        if cached:
            items = [VideoSummary.model_validate(item) for item in cached["items"]]
            return items, cached.get("next_page_token")
        page_size = clamp_page_size(limit)
        uploads_playlist_id = self.client.get_uploads_playlist_id()
        playlist = self.client.list_playlist_items(
            uploads_playlist_id, max_results=page_size, page_token=page_token
        )
        video_ids = [
            item["contentDetails"]["videoId"]
            for item in playlist.get("items", [])
            if item.get("contentDetails", {}).get("videoId")
        ]
        videos = {video["id"]: video for video in self.client.get_videos(video_ids)}
        ordered = [
            normalize_video(videos[video_id])
            for video_id in video_ids
            if video_id in videos
        ]
        next_page_token = playlist.get("nextPageToken")
        self.cache.set(
            "channel_videos",
            cache_key,
            {
                "items": [video.model_dump() for video in ordered[:limit]],
                "next_page_token": next_page_token,
            },
            ttl_seconds=15 * 60,
        )
        return ordered[:limit], next_page_token

    def list_recent_videos_all(
        self,
        profile_name: str,
        limit: int,
        page_token: str | None = None,
        max_pages: int | None = None,
    ) -> tuple[list[VideoSummary], str | None]:
        """Collect videos across pages until limit/max_pages is reached."""
        if limit <= 0:
            return [], page_token
        remaining = limit
        current_token = page_token
        pages_read = 0
        items: list[VideoSummary] = []
        while remaining > 0:
            if max_pages is not None and pages_read >= max_pages:
                break
            page_items, next_token = self.list_recent_videos(
                profile_name=profile_name,
                limit=remaining,
                page_token=current_token,
            )
            items.extend(page_items)
            pages_read += 1
            remaining = limit - len(items)
            if not next_token:
                return items[:limit], None
            current_token = next_token
        return items[:limit], current_token


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
