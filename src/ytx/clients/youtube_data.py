from __future__ import annotations

from typing import Any

from ytx.errors import ApiError, map_google_http_error


class YouTubeDataClient:
    def __init__(self, credentials: Any) -> None:
        try:
            import httplib2
            from google_auth_httplib2 import AuthorizedHttp
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise ApiError(code="API_ERROR", message="google-api-python-client is required for YouTube Data access.") from exc
        http = AuthorizedHttp(credentials, http=httplib2.Http(timeout=30))
        self._service = build("youtube", "v3", http=http, cache_discovery=False)

    def get_mine_channel(self) -> dict[str, Any]:
        try:
            response = (
                self._service.channels()
                .list(part="id,snippet,statistics,contentDetails,brandingSettings", mine=True)
                .execute(num_retries=3)
            )
        except Exception as exc:
            raise map_google_http_error(exc) from exc
        items = response.get("items", [])
        if not items:
            raise ApiError(code="RESOURCE_NOT_FOUND", message="No channel found for the authenticated account.")
        return items[0]

    def get_uploads_playlist_id(self) -> str:
        channel = self.get_mine_channel()
        return channel["contentDetails"]["relatedPlaylists"]["uploads"]

    def list_playlist_items(self, playlist_id: str, max_results: int, page_token: str | None = None) -> dict[str, Any]:
        try:
            return (
                self._service.playlistItems()
                .list(
                    part="contentDetails,snippet",
                    playlistId=playlist_id,
                    maxResults=max_results,
                    pageToken=page_token,
                )
                .execute(num_retries=3)
            )
        except Exception as exc:
            raise map_google_http_error(exc) from exc

    def get_videos(self, video_ids: list[str]) -> list[dict[str, Any]]:
        if not video_ids:
            return []
        try:
            response = (
                self._service.videos()
                .list(part="id,snippet,contentDetails,statistics,status", id=",".join(video_ids))
                .execute(num_retries=3)
            )
        except Exception as exc:
            raise map_google_http_error(exc) from exc
        return response.get("items", [])

    def get_video(self, video_id: str) -> dict[str, Any]:
        items = self.get_videos([video_id])
        if not items:
            raise ApiError(code="RESOURCE_NOT_FOUND", message=f"Video not found: {video_id}")
        return items[0]
