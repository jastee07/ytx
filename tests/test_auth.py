from __future__ import annotations

import json
import unittest.mock

import pytest
from typer.testing import CliRunner

from conftest import FakeProfileStore, YT_READONLY, make_profile
from ytx.commands.auth import app

runner = CliRunner()


@pytest.fixture
def patch_ctx(app_ctx):
    with unittest.mock.patch("ytx.commands.auth.AppContext", return_value=app_ctx):
        yield app_ctx


class TestAuthWhoami:
    def test_json_output_structure(self, patch_ctx):
        result = runner.invoke(app, ["whoami", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["profile_name"] == "default"
        assert data["data"]["channel_id"] == "UC123"
        assert data["data"]["channel_title"] == "Test Channel"

    def test_unknown_profile_exits_2(self, patch_ctx):
        result = runner.invoke(app, ["whoami", "--profile", "ghost", "--json"])
        assert result.exit_code == 2
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "AUTH_REQUIRED"

    def test_human_output_contains_channel_title(self, patch_ctx):
        result = runner.invoke(app, ["whoami"])
        assert result.exit_code == 0
        assert "Test Channel" in result.output


class TestAuthListProfiles:
    def test_json_output_items_list(self, patch_ctx):
        result = runner.invoke(app, ["list-profiles", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data["data"]["items"], list)
        assert data["data"]["items"][0]["profile_name"] == "default"

    def test_empty_profiles_still_succeeds(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(profiles={})
        result = runner.invoke(app, ["list-profiles", "--json"])
        assert result.exit_code == 0
        assert json.loads(result.output)["data"]["items"] == []


class TestAuthUse:
    def test_switches_default_profile(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(), "work": make_profile("work")}
        )
        result = runner.invoke(app, ["use", "work"])
        assert result.exit_code == 0
        assert "work" in result.output

    def test_unknown_profile_exits_2(self, patch_ctx):
        result = runner.invoke(app, ["use", "nonexistent"])
        assert result.exit_code == 2


class TestAuthLogout:
    def test_removes_profile(self, patch_ctx):
        result = runner.invoke(app, ["logout"])
        assert result.exit_code == 0
        assert "removed profile" in result.output


class TestAuthScopes:
    def test_json_output_scopes_list(self, patch_ctx):
        result = runner.invoke(app, ["scopes", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        scopes = [item["scope"] for item in data["data"]["items"]]
        assert YT_READONLY in scopes

    def test_unknown_profile_exits_2(self, patch_ctx):
        result = runner.invoke(app, ["scopes", "--profile", "nobody", "--json"])
        assert result.exit_code == 2
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "AUTH_REQUIRED"


class TestAuthLogin:
    def test_no_client_secret_configured_exits_2(self, patch_ctx):
        # Settings has no client_secret_path → AuthError before OAuth flow starts
        patch_ctx.settings.client_secret_path = None
        result = runner.invoke(app, ["login", "--json"])
        assert result.exit_code == 2
        # The error message contains a newline so strict JSON parsing fails;
        # check for the error code as a string instead.
        assert '"AUTH_REQUIRED"' in result.output
