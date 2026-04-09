from __future__ import annotations

import json
import unittest.mock
from datetime import datetime, UTC

import pytest
from typer.testing import CliRunner

from conftest import FakeDataClient
from ytx.commands.doctor import app

runner = CliRunner()


class FakeCredentials:
    def __init__(self, valid=True):
        self.valid = valid
        self.token = "fake-token"
        self.refresh_token = "fake-refresh"
        self.expiry = datetime(2026, 12, 31, tzinfo=UTC)
        self.scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


@pytest.fixture
def patch_ctx(app_ctx):
    with unittest.mock.patch("ytx.commands.doctor.AppContext", return_value=app_ctx):
        yield app_ctx


@pytest.fixture
def patch_creds(patch_ctx):
    creds = FakeCredentials()
    with (
        unittest.mock.patch("ytx.commands.doctor.load_credentials", return_value=creds),
        unittest.mock.patch("ytx.commands.doctor.refresh_credentials"),
        unittest.mock.patch("ytx.commands.common.load_credentials", return_value=creds),
        unittest.mock.patch("ytx.commands.common.refresh_credentials"),
        unittest.mock.patch("ytx.commands.common.persist_credentials"),
        unittest.mock.patch(
            "ytx.commands.common.YouTubeDataClient", return_value=FakeDataClient()
        ),
    ):
        yield creds


class TestDoctorScopes:
    def test_json_output_returns_scopes(self, patch_ctx):
        result = runner.invoke(app, ["scopes", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        scopes = [item["scope"] for item in data["data"]["items"]]
        assert len(scopes) > 0

    def test_unknown_profile_exits_2(self, patch_ctx):
        result = runner.invoke(app, ["scopes", "--profile", "ghost", "--json"])
        assert result.exit_code == 2
        data = json.loads(result.output)
        assert data["ok"] is False


class TestDoctorQuota:
    def test_json_output_returns_items_and_notes(self, patch_ctx):
        result = runner.invoke(app, ["quota", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output, strict=False)
        assert data["ok"] is True
        assert "items" in data["data"]
        assert "notes" in data["data"]
        assert isinstance(data["data"]["items"], list)
        assert len(data["data"]["items"]) > 0

    def test_search_list_is_most_expensive(self, patch_ctx):
        result = runner.invoke(app, ["quota", "--json"])
        data = json.loads(result.output, strict=False)["data"]
        costs = {item["method"]: item["estimated_cost"] for item in data["items"]}
        assert costs["search.list"] == 100


class TestDoctorCacheShow:
    def test_empty_cache_returns_zero_total(self, patch_ctx):
        result = runner.invoke(app, ["cache", "show", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["total"] == 0
        assert data["data"]["items"] == []

    def test_populated_cache_returns_entries(self, patch_ctx):
        patch_ctx.cache.set("test_ns", "key1", {"value": 1}, ttl_seconds=60)
        result = runner.invoke(app, ["cache", "show", "--json"])
        data = json.loads(result.output)
        assert data["data"]["total"] == 1


class TestDoctorCacheClear:
    def test_clear_all(self, patch_ctx):
        patch_ctx.cache.set("ns1", "k1", {"v": 1}, ttl_seconds=60)
        patch_ctx.cache.set("ns2", "k2", {"v": 2}, ttl_seconds=60)
        result = runner.invoke(app, ["cache", "clear", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["deleted"] == 2
        assert data["data"]["namespace"] == "all"

    def test_clear_by_namespace(self, patch_ctx):
        patch_ctx.cache.set("ns1", "k1", {"v": 1}, ttl_seconds=60)
        patch_ctx.cache.set("ns2", "k2", {"v": 2}, ttl_seconds=60)
        result = runner.invoke(app, ["cache", "clear", "--namespace", "ns1", "--json"])
        data = json.loads(result.output)
        assert data["data"]["deleted"] == 1
        assert data["data"]["namespace"] == "ns1"


class TestDoctorToken:
    def test_json_output_returns_token_metadata(self, patch_ctx, patch_creds):
        result = runner.invoke(app, ["token", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["has_refresh_token"] is True
        assert data["data"]["token_expiry"] is not None

    def test_missing_credentials_exits_2(self, patch_ctx):
        from ytx.errors import AuthError

        with unittest.mock.patch(
            "ytx.commands.doctor.load_credentials",
            side_effect=AuthError(code="AUTH_REQUIRED", message="No credentials"),
        ):
            result = runner.invoke(app, ["token", "--json"])
            assert result.exit_code == 2


class TestDoctorMain:
    def test_json_output_returns_checks(self, patch_ctx, patch_creds):
        # config_toml needs to exist for the check
        patch_ctx.paths.config_toml.write_text("[app]\n")
        result = runner.invoke(app, ["doctor", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output, strict=False)
        assert data["ok"] is True
        checks = data["data"]["items"]
        check_names = [c["check"] for c in checks]
        assert "config_toml" in check_names
        assert "profile" in check_names
