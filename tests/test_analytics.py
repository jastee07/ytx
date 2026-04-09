from __future__ import annotations

import json
import unittest.mock

import pytest
from typer.testing import CliRunner

from conftest import FakeAnalyticsClient, FakeProfileStore, YT_READONLY, make_profile
from ytx.commands.analytics import app

runner = CliRunner()


@pytest.fixture
def patch_ctx(app_ctx):
    with unittest.mock.patch("ytx.commands.analytics.AppContext", return_value=app_ctx):
        yield app_ctx


@pytest.fixture
def fake_analytics(patch_ctx):
    client = FakeAnalyticsClient()
    with unittest.mock.patch(
        "ytx.commands.analytics.load_analytics_client", return_value=client
    ):
        yield client


# analytics.py has a single command so the subcommand name is not passed to the runner.
_BASE = ["--entity", "channel", "--range", "28d", "--metrics", "views"]


class TestAnalyticsQuery:
    def test_channel_query_json(self, fake_analytics):
        result = runner.invoke(app, [*_BASE, "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["api"] == "youtube_analytics"
        assert "rows" in data["data"]
        assert "totals" in data["data"]

    def test_video_query_requires_video_id(self, fake_analytics):
        result = runner.invoke(
            app, ["--entity", "video", "--range", "7d", "--metrics", "views", "--json"]
        )
        assert result.exit_code == 6
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "INVALID_DIMENSION"
        assert "video-id" in data["error"]["message"].lower()

    def test_video_query_with_video_id_succeeds(self, fake_analytics):
        result = runner.invoke(
            app,
            [
                "--entity",
                "video",
                "--video-id",
                "vid1",
                "--range",
                "7d",
                "--metrics",
                "views",
                "--json",
            ],
        )
        assert result.exit_code == 0
        assert json.loads(result.output)["ok"] is True

    def test_invalid_entity_exits_6(self, fake_analytics):
        result = runner.invoke(
            app,
            ["--entity", "playlist", "--range", "7d", "--metrics", "views", "--json"],
        )
        assert result.exit_code == 6
        data = json.loads(result.output)
        assert data["error"]["code"] == "INVALID_DIMENSION"

    def test_missing_analytics_scope_exits_4(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[YT_READONLY])}
        )
        result = runner.invoke(app, [*_BASE, "--json"])
        assert result.exit_code == 4
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"

    def test_no_profile_exits_2(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(profiles={})
        result = runner.invoke(app, [*_BASE, "--json"])
        assert result.exit_code == 2
        assert json.loads(result.output)["error"]["code"] == "AUTH_REQUIRED"

    def test_csv_output_exits_0(self, fake_analytics):
        result = runner.invoke(
            app, ["--entity", "channel", "--range", "7d", "--metrics", "views", "--csv"]
        )
        assert result.exit_code == 0
