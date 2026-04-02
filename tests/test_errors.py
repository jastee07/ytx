"""Error-path tests: verify that API errors and auth failures surface
the correct error codes and exit codes rather than raw exceptions."""
from __future__ import annotations

import json
import unittest.mock

import pytest
from typer.testing import CliRunner

from ytx.errors import ApiError, AuthError

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class ErrorDataClient:
    """Fake data client that raises a pre-configured exception on every call."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def get_mine_channel(self):
        raise self._error

    def get_uploads_playlist_id(self):
        raise self._error

    def list_playlist_items(self, *args, **kwargs):
        raise self._error

    def get_videos(self, *args, **kwargs):
        raise self._error

    def get_video(self, *args, **kwargs):
        raise self._error


# ---------------------------------------------------------------------------
# channel get — API error codes
# ---------------------------------------------------------------------------


class TestChannelGetApiErrors:
    def _invoke(self, app_ctx, error):
        from ytx.commands.channel import app

        with unittest.mock.patch("ytx.commands.channel.AppContext", return_value=app_ctx):
            with unittest.mock.patch("ytx.commands.channel.load_data_client", return_value=ErrorDataClient(error)):
                return runner.invoke(app, ["get", "--json"])

    def test_quota_exceeded(self, app_ctx):
        result = self._invoke(app_ctx, ApiError(code="QUOTA_EXCEEDED", message="Daily quota limit reached."))
        assert result.exit_code == 1
        assert json.loads(result.output)["error"]["code"] == "QUOTA_EXCEEDED"

    def test_resource_not_found(self, app_ctx):
        result = self._invoke(app_ctx, ApiError(code="RESOURCE_NOT_FOUND", message="Channel not found."))
        assert result.exit_code == 1
        assert json.loads(result.output)["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_insufficient_scope_from_api(self, app_ctx):
        result = self._invoke(app_ctx, ApiError(code="INSUFFICIENT_SCOPE", message="Missing OAuth scope."))
        assert result.exit_code == 1
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"

    def test_rate_limited(self, app_ctx):
        result = self._invoke(app_ctx, ApiError(code="RATE_LIMITED", message="Too many requests."))
        assert result.exit_code == 1
        assert json.loads(result.output)["error"]["code"] == "RATE_LIMITED"


# ---------------------------------------------------------------------------
# video get — API error codes
# ---------------------------------------------------------------------------


class TestVideoGetApiErrors:
    def _invoke(self, app_ctx, error):
        from ytx.commands.video import app

        with unittest.mock.patch("ytx.commands.video.AppContext", return_value=app_ctx):
            with unittest.mock.patch("ytx.commands.video.load_data_client", return_value=ErrorDataClient(error)):
                return runner.invoke(app, ["get", "vid999", "--json"])

    def test_resource_not_found(self, app_ctx):
        result = self._invoke(app_ctx, ApiError(code="RESOURCE_NOT_FOUND", message="Video not found: vid999"))
        assert result.exit_code == 1
        assert json.loads(result.output)["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_rate_limited(self, app_ctx):
        result = self._invoke(app_ctx, ApiError(code="RATE_LIMITED", message="Too many requests."))
        assert result.exit_code == 1
        assert json.loads(result.output)["error"]["code"] == "RATE_LIMITED"


# ---------------------------------------------------------------------------
# Token refresh failure surfaces as TOKEN_REFRESH_FAILED
# ---------------------------------------------------------------------------


class TestTokenRefreshFailure:
    def test_refresh_failure_exits_1(self, app_ctx):
        from ytx.commands.channel import app

        err = AuthError(code="TOKEN_REFRESH_FAILED", message="Token was revoked. Run 'ytx auth login'.")
        with unittest.mock.patch("ytx.commands.channel.AppContext", return_value=app_ctx):
            with unittest.mock.patch("ytx.commands.channel.load_data_client", side_effect=err):
                result = runner.invoke(app, ["get", "--json"])
        assert result.exit_code == 1
        assert json.loads(result.output)["error"]["code"] == "TOKEN_REFRESH_FAILED"


# ---------------------------------------------------------------------------
# doctor cache show / clear
# ---------------------------------------------------------------------------


class TestDoctorCache:
    @pytest.fixture
    def patch_ctx(self, app_ctx):
        from ytx.commands.doctor import app as doctor_app

        with unittest.mock.patch("ytx.commands.doctor.AppContext", return_value=app_ctx):
            yield app_ctx, doctor_app

    def test_cache_show_empty(self, patch_ctx):
        app_ctx, doctor_app = patch_ctx
        result = runner.invoke(doctor_app, ["cache", "show", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_cache_show_lists_entries(self, patch_ctx):
        app_ctx, doctor_app = patch_ctx
        app_ctx.cache.set("channel", "UC123", {"title": "Test"}, ttl_seconds=900)
        result = runner.invoke(doctor_app, ["cache", "show", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["namespace"] == "channel"

    def test_cache_clear_all(self, patch_ctx):
        app_ctx, doctor_app = patch_ctx
        app_ctx.cache.set("channel", "UC123", {}, ttl_seconds=900)
        app_ctx.cache.set("video", "vid1", {}, ttl_seconds=900)
        result = runner.invoke(doctor_app, ["cache", "clear", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["deleted"] == 2
        assert data["data"]["namespace"] == "all"

    def test_cache_clear_by_namespace(self, patch_ctx):
        app_ctx, doctor_app = patch_ctx
        app_ctx.cache.set("channel", "UC123", {}, ttl_seconds=900)
        app_ctx.cache.set("video", "vid1", {}, ttl_seconds=900)
        result = runner.invoke(doctor_app, ["cache", "clear", "--namespace", "channel", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["deleted"] == 1
        assert data["data"]["namespace"] == "channel"
        # video entry should still be present
        assert app_ctx.cache.get("video", "vid1") is not None
