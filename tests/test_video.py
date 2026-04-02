from __future__ import annotations

import json
import unittest.mock

import pytest
from typer.testing import CliRunner

from conftest import FakeAnalyticsClient, FakeDataClient, FakeProfileStore, YT_READONLY, make_profile
from ytx.commands.video import app

runner = CliRunner()


@pytest.fixture
def patch_ctx(app_ctx):
    with unittest.mock.patch("ytx.commands.video.AppContext", return_value=app_ctx):
        yield app_ctx


@pytest.fixture
def fake_data(patch_ctx):
    client = FakeDataClient()
    with unittest.mock.patch("ytx.commands.video.load_data_client", return_value=client):
        yield client


@pytest.fixture
def fake_analytics(patch_ctx):
    client = FakeAnalyticsClient()
    with unittest.mock.patch("ytx.commands.video.load_analytics_client", return_value=client):
        yield client


class TestVideoList:
    def test_json_output_items_list(self, fake_data):
        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert len(data["data"]["items"]) == 2

    def test_published_after_filters_results(self, fake_data):
        # vid1 published 2026-03-01, vid2 published 2026-02-15
        # --published-after 2026-02-20 should return only vid1
        result = runner.invoke(app, ["list", "--published-after", "2026-02-20", "--json"])
        assert result.exit_code == 0
        items = json.loads(result.output)["data"]["items"]
        assert len(items) == 1
        assert items[0]["video_id"] == "vid1"

    def test_missing_scope_exits_1(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[])}
        )
        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 1
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"


class TestVideoGet:
    def test_json_output_known_id(self, fake_data):
        result = runner.invoke(app, ["get", "vid1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["video_id"] == "vid1"
        assert data["data"]["title"] == "Video One"

    def test_not_found_exits_1(self, fake_data):
        result = runner.invoke(app, ["get", "missing_id", "--json"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_human_output_shows_title(self, fake_data):
        result = runner.invoke(app, ["get", "vid1"])
        assert result.exit_code == 0
        assert "Video One" in result.output


class TestVideoAnalytics:
    def test_json_output_structure(self, fake_analytics):
        result = runner.invoke(app, ["analytics", "vid1", "--range", "28d", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["api"] == "youtube_analytics"
        assert "rows" in data["data"]

    def test_missing_analytics_scope_exits_1(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[YT_READONLY])}
        )
        result = runner.invoke(app, ["analytics", "vid1", "--range", "7d", "--json"])
        assert result.exit_code == 1
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"
