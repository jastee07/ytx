"""Unit tests for ytx/clients/youtube_data.py."""

from __future__ import annotations

import unittest.mock

import pytest

from ytx.clients.youtube_data import YouTubeDataClient
from ytx.errors import ApiError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(service_mock):
    """Return a YouTubeDataClient with _service replaced by a mock."""
    client = object.__new__(YouTubeDataClient)
    client._service = service_mock
    return client


def _chain(*return_value):
    """Build a mock that supports .foo().bar().execute() chaining."""
    execute = unittest.mock.MagicMock(
        return_value=return_value[0] if return_value else {}
    )
    inner = unittest.mock.MagicMock()
    inner.execute = execute
    outer = unittest.mock.MagicMock(return_value=inner)
    return outer, execute


# ---------------------------------------------------------------------------
# get_mine_channel
# ---------------------------------------------------------------------------


class TestGetMineChannel:
    def test_returns_first_item(self):
        channel = {"id": "UC123", "snippet": {"title": "My Channel"}}
        svc = unittest.mock.MagicMock()
        svc.channels().list().execute.return_value = {"items": [channel]}
        client = _make_client(svc)
        result = client.get_mine_channel()
        assert result["id"] == "UC123"

    def test_raises_when_no_items(self):
        svc = unittest.mock.MagicMock()
        svc.channels().list().execute.return_value = {"items": []}
        client = _make_client(svc)
        with pytest.raises(ApiError) as exc_info:
            client.get_mine_channel()
        assert exc_info.value.code == "RESOURCE_NOT_FOUND"

    def test_propagates_http_error(self):
        from googleapiclient.errors import HttpError

        svc = unittest.mock.MagicMock()
        resp = unittest.mock.MagicMock()
        resp.status = 403
        svc.channels().list().execute.side_effect = HttpError(
            resp=resp, content=b"Forbidden"
        )
        client = _make_client(svc)
        with pytest.raises(ApiError):
            client.get_mine_channel()


# ---------------------------------------------------------------------------
# get_uploads_playlist_id
# ---------------------------------------------------------------------------


class TestGetUploadsPlaylistId:
    def test_extracts_playlist_id(self):
        channel = {
            "id": "UC123",
            "contentDetails": {"relatedPlaylists": {"uploads": "UUPL123"}},
        }
        svc = unittest.mock.MagicMock()
        svc.channels().list().execute.return_value = {"items": [channel]}
        client = _make_client(svc)
        assert client.get_uploads_playlist_id() == "UUPL123"


# ---------------------------------------------------------------------------
# list_playlist_items
# ---------------------------------------------------------------------------


class TestListPlaylistItems:
    def test_returns_api_response(self):
        fake_resp = {
            "items": [{"contentDetails": {"videoId": "vid1"}}],
            "nextPageToken": None,
        }
        svc = unittest.mock.MagicMock()
        svc.playlistItems().list().execute.return_value = fake_resp
        client = _make_client(svc)
        result = client.list_playlist_items("UUPL123", max_results=10)
        assert result["items"][0]["contentDetails"]["videoId"] == "vid1"

    def test_passes_page_token(self):
        svc = unittest.mock.MagicMock()
        svc.playlistItems().list().execute.return_value = {"items": []}
        client = _make_client(svc)
        client.list_playlist_items("UUPL123", max_results=5, page_token="tok123")
        svc.playlistItems().list.assert_called_with(
            part="contentDetails,snippet",
            playlistId="UUPL123",
            maxResults=5,
            pageToken="tok123",
        )

    def test_propagates_http_error(self):
        from googleapiclient.errors import HttpError

        svc = unittest.mock.MagicMock()
        resp = unittest.mock.MagicMock()
        resp.status = 500
        svc.playlistItems().list().execute.side_effect = HttpError(
            resp=resp, content=b"Server Error"
        )
        client = _make_client(svc)
        with pytest.raises(ApiError):
            client.list_playlist_items("UUPL123", max_results=10)


# ---------------------------------------------------------------------------
# get_videos
# ---------------------------------------------------------------------------


class TestGetVideos:
    def test_returns_empty_list_for_empty_input(self):
        svc = unittest.mock.MagicMock()
        client = _make_client(svc)
        assert client.get_videos([]) == []
        svc.videos.assert_not_called()

    def test_returns_items(self):
        videos = [{"id": "vid1"}, {"id": "vid2"}]
        svc = unittest.mock.MagicMock()
        svc.videos().list().execute.return_value = {"items": videos}
        client = _make_client(svc)
        result = client.get_videos(["vid1", "vid2"])
        assert len(result) == 2
        assert result[0]["id"] == "vid1"

    def test_joins_ids_with_comma(self):
        svc = unittest.mock.MagicMock()
        svc.videos().list().execute.return_value = {"items": []}
        client = _make_client(svc)
        client.get_videos(["a", "b", "c"])
        svc.videos().list.assert_called_with(
            part="id,snippet,contentDetails,statistics,status",
            id="a,b,c",
        )


# ---------------------------------------------------------------------------
# get_video
# ---------------------------------------------------------------------------


class TestGetVideo:
    def test_returns_single_video(self):
        video = {"id": "vid1", "snippet": {"title": "Hello"}}
        svc = unittest.mock.MagicMock()
        svc.videos().list().execute.return_value = {"items": [video]}
        client = _make_client(svc)
        result = client.get_video("vid1")
        assert result["id"] == "vid1"

    def test_raises_when_not_found(self):
        svc = unittest.mock.MagicMock()
        svc.videos().list().execute.return_value = {"items": []}
        client = _make_client(svc)
        with pytest.raises(ApiError) as exc_info:
            client.get_video("missing")
        assert exc_info.value.code == "RESOURCE_NOT_FOUND"
