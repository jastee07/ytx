"""Tests for the ytx reporting commands (commands/reporting.py)."""

from __future__ import annotations

import json
import unittest.mock

import pytest
from typer.testing import CliRunner

from conftest import FakeProfileStore, FakeReportingClient, YT_ANALYTICS, make_profile
from ytx.commands.reporting import app

runner = CliRunner()

YT_REPORTING_SCOPE = YT_ANALYTICS  # READ_REPORTING maps to yt-analytics.readonly


@pytest.fixture
def patch_ctx(app_ctx):
    with unittest.mock.patch("ytx.commands.reporting.AppContext", return_value=app_ctx):
        yield app_ctx


@pytest.fixture
def fake_reporting(patch_ctx):
    client = FakeReportingClient()
    with unittest.mock.patch(
        "ytx.commands.reporting.load_reporting_client", return_value=client
    ):
        yield client


# ---------------------------------------------------------------------------
# list-report-types
# ---------------------------------------------------------------------------


class TestListReportTypes:
    def test_json_output_structure(self, fake_reporting):
        result = runner.invoke(app, ["list-report-types", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["api"] == "youtube_reporting"
        assert isinstance(data["data"]["items"], list)
        assert data["data"]["items"][0]["id"] == "rtype1"

    def test_human_output_exits_0(self, fake_reporting):
        result = runner.invoke(app, ["list-report-types"])
        assert result.exit_code == 0

    def test_missing_scope_exits_4(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[])}
        )
        result = runner.invoke(app, ["list-report-types", "--json"])
        assert result.exit_code == 4
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"


# ---------------------------------------------------------------------------
# list-jobs
# ---------------------------------------------------------------------------


class TestListJobs:
    def test_json_output_structure(self, fake_reporting):
        result = runner.invoke(app, ["list-jobs", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["items"][0]["id"] == "job1"

    def test_missing_scope_exits_4(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[])}
        )
        result = runner.invoke(app, ["list-jobs", "--json"])
        assert result.exit_code == 4
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"


# ---------------------------------------------------------------------------
# create-job
# ---------------------------------------------------------------------------


class TestCreateJob:
    def test_json_output_contains_new_job(self, fake_reporting):
        result = runner.invoke(
            app,
            ["create-job", "--report-type-id", "rtype1", "--name", "New job", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["id"] == "job2"
        assert data["data"]["name"] == "New job"

    def test_missing_scope_exits_4(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[])}
        )
        result = runner.invoke(
            app, ["create-job", "--report-type-id", "rtype1", "--name", "x", "--json"]
        )
        assert result.exit_code == 4
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"


# ---------------------------------------------------------------------------
# delete-job
# ---------------------------------------------------------------------------


class TestDeleteJob:
    def test_json_output_on_success(self, fake_reporting):
        result = runner.invoke(app, ["delete-job", "--job-id", "job1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["deleted"] is True
        assert data["data"]["job_id"] == "job1"

    def test_human_output_exits_0(self, fake_reporting):
        result = runner.invoke(app, ["delete-job", "--job-id", "job1"])
        assert result.exit_code == 0

    def test_missing_scope_exits_1(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[])}
        )
        result = runner.invoke(app, ["delete-job", "--job-id", "job1", "--json"])
        assert result.exit_code == 1
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"


# ---------------------------------------------------------------------------
# list-reports
# ---------------------------------------------------------------------------


class TestListReports:
    def test_json_output_lists_reports(self, fake_reporting):
        result = runner.invoke(app, ["list-reports", "--job-id", "job1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["items"][0]["id"] == "report1"

    def test_unknown_job_returns_empty(self, fake_reporting):
        result = runner.invoke(
            app, ["list-reports", "--job-id", "no-such-job", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["items"] == []

    def test_missing_scope_exits_4(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[])}
        )
        result = runner.invoke(app, ["list-reports", "--job-id", "job1", "--json"])
        assert result.exit_code == 4
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"


# ---------------------------------------------------------------------------
# download
# ---------------------------------------------------------------------------


class TestDownload:
    def test_json_output_parses_csv_rows(self, fake_reporting):
        result = runner.invoke(
            app, ["download", "--job-id", "job1", "--report-id", "report1", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["data"]["job_id"] == "job1"
        assert data["data"]["report_id"] == "report1"
        rows = data["data"]["items"]
        assert isinstance(rows, list)
        assert rows[0]["date"] == "2026-03-01"
        assert rows[0]["views"] == "100"

    def test_report_not_found_exits_5(self, fake_reporting):
        result = runner.invoke(
            app,
            ["download", "--job-id", "job1", "--report-id", "no-such-report", "--json"],
        )
        assert result.exit_code == 5
        data = json.loads(result.output)
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_write_to_output_file(self, fake_reporting, tmp_path):
        out = tmp_path / "report.csv"
        result = runner.invoke(
            app,
            [
                "download",
                "--job-id",
                "job1",
                "--report-id",
                "report1",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0
        assert out.exists()
        assert b"views" in out.read_bytes()

    def test_missing_scope_exits_4(self, patch_ctx):
        patch_ctx.profile_store = FakeProfileStore(
            profiles={"default": make_profile(scopes=[])}
        )
        result = runner.invoke(
            app, ["download", "--job-id", "job1", "--report-id", "report1", "--json"]
        )
        assert result.exit_code == 4
        assert json.loads(result.output)["error"]["code"] == "INSUFFICIENT_SCOPE"
