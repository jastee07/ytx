from __future__ import annotations

from ytx.models.analytics import AnalyticsQuery
from ytx.services.analytics_service import AnalyticsService


class FakeAnalyticsClient:
    def __init__(self):
        self.calls = 0

    def query(self, **kwargs):
        self.calls += 1
        return {
            "columnHeaders": [
                {"name": "day"},
                {"name": "views"},
                {"name": "estimatedMinutesWatched"},
            ],
            "rows": [
                ["2026-03-20", 102, 215.4],
                ["2026-03-21", 98, 200.0],
            ],
        }


class DictCache:
    def __init__(self):
        self.data = {}

    def get(self, namespace, key):
        return self.data.get((namespace, key))

    def set(self, namespace, key, payload, ttl_seconds):
        self.data[(namespace, key)] = payload


def test_analytics_service_normalizes_metrics_and_totals() -> None:
    service = AnalyticsService(FakeAnalyticsClient(), DictCache())
    report = service.query(
        AnalyticsQuery(
            entity="channel",
            start_date="2026-03-01",
            end_date="2026-03-25",
            metrics=["views", "watch_time"],
            dimensions=["day"],
            filters=[],
            sort=[],
            max_results=None,
            video_id=None,
        )
    )
    assert report.rows == [
        {"day": "2026-03-20", "views": 102, "watch_time": 215.4},
        {"day": "2026-03-21", "views": 98, "watch_time": 200.0},
    ]
    assert report.totals == {"views": 200, "watch_time": 415.4}


def test_analytics_service_uses_cache() -> None:
    client = FakeAnalyticsClient()
    cache = DictCache()
    service = AnalyticsService(client, cache)
    query = AnalyticsQuery(
        entity="channel",
        start_date="2026-03-01",
        end_date="2026-03-25",
        metrics=["views"],
        dimensions=["day"],
        filters=[],
        sort=[],
        max_results=None,
        video_id=None,
    )
    service.query(query)
    service.query(query)
    assert client.calls == 1
