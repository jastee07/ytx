from __future__ import annotations

import json
import unittest.mock

import pytest
from typer.testing import CliRunner

from ytx.commands.schema import app
from ytx.utils.metrics import DIMENSION_ALIASES, METRIC_ALIASES

runner = CliRunner()


@pytest.fixture
def patch_ctx(app_ctx):
    with unittest.mock.patch("ytx.commands.schema.AppContext", return_value=app_ctx):
        yield app_ctx


class TestSchemaShowJson:
    def test_json_output_has_all_top_level_keys(self, patch_ctx):
        result = runner.invoke(app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output, strict=False)
        assert data["ok"] is True
        payload = data["data"]
        for key in (
            "metrics",
            "dimensions",
            "filters",
            "date_range",
            "entities",
            "exit_codes",
            "env_vars",
            "commands",
        ):
            assert key in payload, f"Missing key: {key}"

    def test_commands_contracts_present(self, patch_ctx):
        result = runner.invoke(app, ["--json"])
        data = json.loads(result.output, strict=False)["data"]
        assert "channel.videos" in data["commands"]
        assert "--limit" in data["commands"]["channel.videos"]["options"]
        assert "reporting.list-jobs" in data["commands"]

    def test_all_metric_aliases_present(self, patch_ctx):
        result = runner.invoke(app, ["--json"])
        data = json.loads(result.output, strict=False)["data"]
        for alias in METRIC_ALIASES:
            assert alias in data["metrics"], f"Missing metric alias: {alias}"

    def test_all_dimension_aliases_present(self, patch_ctx):
        result = runner.invoke(app, ["--json"])
        data = json.loads(result.output, strict=False)["data"]
        for alias in DIMENSION_ALIASES:
            assert alias in data["dimensions"], f"Missing dimension alias: {alias}"

    def test_metric_entries_have_api_name(self, patch_ctx):
        result = runner.invoke(app, ["--json"])
        data = json.loads(result.output, strict=False)["data"]
        for alias, info in data["metrics"].items():
            assert "api_name" in info, f"Metric {alias} missing api_name"

    def test_exit_codes_present(self, patch_ctx):
        result = runner.invoke(app, ["--json"])
        data = json.loads(result.output, strict=False)["data"]
        assert "AUTH_REQUIRED" in data["exit_codes"]
        assert "QUOTA_EXCEEDED" in data["exit_codes"]
        assert data["exit_codes"]["AUTH_REQUIRED"]["exit_code"] == 2

    def test_env_vars_present(self, patch_ctx):
        result = runner.invoke(app, ["--json"])
        data = json.loads(result.output, strict=False)["data"]
        assert "YTX_OUTPUT" in data["env_vars"]
        assert "YTX_PROFILE" in data["env_vars"]

    def test_entities_list(self, patch_ctx):
        result = runner.invoke(app, ["--json"])
        data = json.loads(result.output, strict=False)["data"]
        assert "channel" in data["entities"]
        assert "video" in data["entities"]

    def test_filters_have_syntax(self, patch_ctx):
        result = runner.invoke(app, ["--json"])
        data = json.loads(result.output, strict=False)["data"]
        for alias, info in data["filters"].items():
            assert "syntax" in info, f"Filter {alias} missing syntax"


class TestSchemaShowHuman:
    def test_human_output_contains_section_headers(self, patch_ctx):
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Metrics" in result.output
        assert "Dimensions" in result.output
        assert "Filters" in result.output
        assert "Exit codes" in result.output
        assert "Env vars" in result.output
        assert "Commands" in result.output
