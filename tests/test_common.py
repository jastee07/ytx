from __future__ import annotations

import unittest.mock

import pytest

from ytx.commands.common import (
    build_envelope,
    build_error,
    extract_csv_rows,
    render_error,
    render_payload,
)
from ytx.errors import ValidationError, YtxError


class TestBuildEnvelope:
    def test_creates_correct_envelope(self):
        env = build_envelope(
            api="youtube_data", profile_name="default", data={"items": []}
        )
        assert env.ok is True
        assert env.api == "youtube_data"
        assert env.profile == "default"
        assert env.data == {"items": []}
        assert env.generated_at  # non-empty


class TestBuildError:
    def test_creates_error_envelope(self):
        error = YtxError(
            code="QUOTA_EXCEEDED",
            message="Too many requests",
            details={"retry_after": 60},
        )
        env = build_error(error)
        assert env.ok is False
        assert env.error.code == "QUOTA_EXCEEDED"
        assert env.error.message == "Too many requests"
        assert env.error.details == {"retry_after": 60}


class TestExtractCsvRows:
    def test_extracts_items_key(self):
        rows = extract_csv_rows({"items": [{"a": 1}, {"a": 2}]})
        assert rows == [{"a": 1}, {"a": 2}]

    def test_extracts_rows_key(self):
        rows = extract_csv_rows({"rows": [{"b": 3}]})
        assert rows == [{"b": 3}]

    def test_wraps_plain_dict(self):
        rows = extract_csv_rows({"key": "value"})
        assert rows == [{"key": "value"}]


class TestRenderPayload:
    def test_ytx_output_json_env_forces_json(self, monkeypatch):
        monkeypatch.setenv("YTX_OUTPUT", "json")
        output_lines = []

        def human_renderer(c, d):
            output_lines.append("human")

        # Just verify it doesn't call human_renderer when YTX_OUTPUT=json
        with unittest.mock.patch("ytx.commands.common.emit_json") as mock_json:
            render_payload(
                api="test",
                profile_name="default",
                data={"items": []},
                as_json=False,
                as_csv=False,
                output=None,
                human_renderer=human_renderer,
            )
            mock_json.assert_called_once()
        assert output_lines == []

    def test_ytx_output_csv_env_forces_csv(self, monkeypatch):
        monkeypatch.setenv("YTX_OUTPUT", "csv")
        with unittest.mock.patch("ytx.commands.common.emit_csv") as mock_csv:
            render_payload(
                api="test",
                profile_name="default",
                data={"items": [{"a": 1}]},
                as_json=False,
                as_csv=False,
                output=None,
                human_renderer=lambda c, d: None,
            )
            mock_csv.assert_called_once()

    def test_json_and_csv_both_true_raises(self, monkeypatch):
        monkeypatch.delenv("YTX_OUTPUT", raising=False)
        with pytest.raises(ValidationError):
            render_payload(
                api="test",
                profile_name="default",
                data={},
                as_json=True,
                as_csv=True,
                output=None,
                human_renderer=lambda c, d: None,
            )

    def test_human_renderer_called_when_no_format_flag(self, monkeypatch):
        monkeypatch.delenv("YTX_OUTPUT", raising=False)
        called = []

        def human_renderer(c, d):
            called.append(True)

        render_payload(
            api="test",
            profile_name="default",
            data={"items": []},
            as_json=False,
            as_csv=False,
            output=None,
            human_renderer=human_renderer,
        )
        assert called == [True]


class TestRenderError:
    def test_json_error_output(self):
        error = YtxError(code="RESOURCE_NOT_FOUND", message="Video not found")
        with unittest.mock.patch("ytx.commands.common.emit_json") as mock_json:
            render_error(error, as_json=True)
            mock_json.assert_called_once()

    def test_human_error_output(self, capsys):
        error = YtxError(
            code="RESOURCE_NOT_FOUND", message="Video not found", details={"id": "abc"}
        )
        render_error(error, as_json=False)
        # Rich prints to its own console, so we just verify no exception raised
