from __future__ import annotations

import json
import unittest.mock

import pytest
from typer.testing import CliRunner

from conftest import (
    FakeAnalyticsClient,
    FakeDataClient,
    FakeProfileStore,
    YT_READONLY,
    make_profile,
)
from ytx.commands.channel import app

runner = CliRunner()


@pytest.fixture
def patch_ctx(app_ctx):
    with unittest.mock.patch("ytx.commands.channel.AppContext", return_value=app_ctx):
        yield app_ctx


@pytest.fixture
def fake_data(patch_ctx):
    client = FakeDataClient()
    with unittest.mock.patch(
        "ytx.commands.channel.load_data_client", return_value=client
    ):
        yield client


@pytest.fixture
def fake_analytics(patch_ctx):
    client = FakeAnalyticsClient()
    with unittest.mock.patch(
        "ytx.commands.channel.load_analytics_client", return_value=client
    ):
        yield client


class TestChannelGet:
    def test_json_output_structure(self, fake_data):
        result = runner.invoke(app, ["get", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["api"] == "youtube_data"
        assert data["data"]["channel_id"] == "UC123"
        assert data["data"]["title"] == "Test Channel"

    def test_human_output_shows_channel_title(self, fake_data):
        result = runner.invoke(app, ["get"])
        assert result.exit_code == 0
        assert "Test Channel" in result.output

    def test_no_profile_exits_2(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(profiles={})
        result = runner.invoke(app, ["get", "--json"])
        assert result.exit_code == 2
        assert json.loads(result.output)["error"]["code"] == "AUTH_REQUIRED"

    def test_missing_scope_exits_4(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[])}
        )
        result = runner.invoke(app, ["get", "--json"])
        assert result.exit_code == 4
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"


class TestChannelVideos:
    def test_json_output_items_list(self, fake_data):
        result = runner.invoke(app, ["videos", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert isinstance(data["data"]["items"], list)
        assert data["data"]["items"][0]["video_id"] == "vid1"

    def test_csv_output_exits_0(self, fake_data):
        result = runner.invoke(app, ["videos", "--csv"])
        assert result.exit_code == 0

    def test_all_flag_exits_0(self, fake_data):
        result = runner.invoke(app, ["videos", "--all", "--max-pages", "2", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data["data"]["items"], list)

    def test_missing_scope_exits_4(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[])}
        )
        result = runner.invoke(app, ["videos", "--json"])
        assert result.exit_code == 4
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"


class TestChannelStats:
    def test_json_output_structure(self, fake_analytics):
        result = runner.invoke(app, ["stats", "--range", "7d", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["api"] == "youtube_analytics"
        assert "rows" in data["data"]
        assert "totals" in data["data"]

    def test_missing_analytics_scope_exits_4(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[YT_READONLY])}
        )
        result = runner.invoke(app, ["stats", "--range", "7d", "--json"])
        assert result.exit_code == 4
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"
