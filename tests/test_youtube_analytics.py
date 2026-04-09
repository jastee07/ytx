"""Unit tests for ytx/clients/youtube_analytics.py."""
from __future__ import annotations

import unittest.mock

import pytest

from ytx.clients.youtube_analytics import YouTubeAnalyticsClient
from ytx.errors import ApiError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(service_mock):
    client = object.__new__(YouTubeAnalyticsClient)
    client._service = service_mock
    return client


FAKE_RESPONSE = {
    "kind": "youtubeAnalytics#resultTable",
    "columnHeaders": [
        {"name": "day", "columnType": "DIMENSION"},
        {"name": "views", "columnType": "METRIC"},
    ],
    "rows": [["2026-03-01", 100], ["2026-03-02", 200]],
}


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------


class TestQuery:
    def _svc_with_response(self, response=None):
        svc = unittest.mock.MagicMock()
        svc.reports().query().execute.return_value = response or FAKE_RESPONSE
        return svc

    def test_returns_api_response(self):
        svc = self._svc_with_response()
        client = _make_client(svc)
        result = client.query(
            ids="channel==MINE",
            start_date="2026-03-01",
            end_date="2026-03-02",
            metrics=["views"],
            dimensions=["day"],
            filters=[],
            sort=[],
            max_results=None,
        )
        assert result["rows"][0] == ["2026-03-01", 100]

    def test_builds_correct_params(self):
        svc = self._svc_with_response()
        client = _make_client(svc)
        client.query(
            ids="channel==MINE",
            start_date="2026-03-01",
            end_date="2026-03-31",
            metrics=["views", "likes"],
            dimensions=["day"],
            filters=["video==vid1"],
            sort=["-views"],
            max_results=10,
        )
        svc.reports().query.assert_called_with(
            ids="channel==MINE",
            startDate="2026-03-01",
            endDate="2026-03-31",
            metrics="views,likes",
            dimensions="day",
            filters="video==vid1",
            sort="-views",
            maxResults=10,
        )

    def test_omits_optional_params_when_empty(self):
        svc = self._svc_with_response()
        client = _make_client(svc)
        client.query(
            ids="channel==MINE",
            start_date="2026-03-01",
            end_date="2026-03-31",
            metrics=["views"],
            dimensions=[],
            filters=[],
            sort=[],
            max_results=None,
        )
        call_kwargs = svc.reports().query.call_args[1]
        assert "dimensions" not in call_kwargs
        assert "filters" not in call_kwargs
        assert "sort" not in call_kwargs
        assert "maxResults" not in call_kwargs

    def test_joins_multiple_metrics_with_comma(self):
        svc = self._svc_with_response()
        client = _make_client(svc)
        client.query(
            ids="channel==MINE",
            start_date="2026-03-01",
            end_date="2026-03-31",
            metrics=["views", "likes", "comments"],
            dimensions=[],
            filters=[],
            sort=[],
            max_results=None,
        )
        call_kwargs = svc.reports().query.call_args[1]
        assert call_kwargs["metrics"] == "views,likes,comments"

    def test_joins_multiple_filters_with_semicolon(self):
        svc = self._svc_with_response()
        client = _make_client(svc)
        client.query(
            ids="channel==MINE",
            start_date="2026-03-01",
            end_date="2026-03-31",
            metrics=["views"],
            dimensions=[],
            filters=["video==vid1", "country==US"],
            sort=[],
            max_results=None,
        )
        call_kwargs = svc.reports().query.call_args[1]
        assert call_kwargs["filters"] == "video==vid1;country==US"

    def test_propagates_http_error(self):
        from googleapiclient.errors import HttpError
        svc = unittest.mock.MagicMock()
        resp = unittest.mock.MagicMock()
        resp.status = 403
        svc.reports().query().execute.side_effect = HttpError(resp=resp, content=b"Forbidden")
        client = _make_client(svc)
        with pytest.raises(ApiError):
            client.query(
                ids="channel==MINE",
                start_date="2026-03-01",
                end_date="2026-03-31",
                metrics=["views"],
                dimensions=[],
                filters=[],
                sort=[],
                max_results=None,
            )
