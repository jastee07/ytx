from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from ytx.clients.youtube_analytics import YouTubeAnalyticsClient
from ytx.models.analytics import AnalyticsQuery, AnalyticsReport
from ytx.utils.metrics import resolve_dimensions, resolve_filters, resolve_metrics, validate_metric_dimension_combo


class AnalyticsService:
    def __init__(self, client: YouTubeAnalyticsClient, cache) -> None:
        self.client = client
        self.cache = cache

    def query(self, query: AnalyticsQuery) -> AnalyticsReport:
        api_metrics, reverse_metrics = resolve_metrics(query.metrics)
        api_dimensions = resolve_dimensions(query.dimensions)
        api_filters = resolve_filters(query.filters, video_id=query.video_id if query.entity == "video" else None)
        validate_metric_dimension_combo(query.metrics, query.dimensions)
        normalized = {
            "entity": query.entity,
            "start_date": query.start_date,
            "end_date": query.end_date,
            "metrics": query.metrics,
            "dimensions": query.dimensions,
            "filters": api_filters,
            "sort": query.sort,
            "max_results": query.max_results,
            "video_id": query.video_id,
        }
        cache_key = sha256(json.dumps(normalized, sort_keys=True).encode("utf-8")).hexdigest()
        cached = self.cache.get("analytics_query", cache_key)
        if cached:
            return AnalyticsReport.model_validate(cached)

        response = self.client.query(
            ids="channel==MINE",
            start_date=query.start_date,
            end_date=query.end_date,
            metrics=api_metrics,
            dimensions=api_dimensions,
            filters=api_filters,
            sort=query.sort,
            max_results=query.max_results,
        )
        headers = [header["name"] for header in response.get("columnHeaders", [])]
        rows = response.get("rows", [])
        normalized_rows = [self._normalize_row(headers, row, reverse_metrics) for row in rows]
        totals = _compute_totals(normalized_rows, query.metrics) if normalized_rows else None
        report = AnalyticsReport(
            entity=query.entity,
            start_date=query.start_date,
            end_date=query.end_date,
            metrics=query.metrics,
            dimensions=query.dimensions,
            filters=query.filters,
            rows=normalized_rows,
            totals=totals,
        )
        self.cache.set("analytics_query", cache_key, report.model_dump(), ttl_seconds=15 * 60)
        return report

    def _normalize_row(self, headers: list[str], row: list[Any], reverse_metrics: dict[str, str]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for header, value in zip(headers, row):
            output_key = reverse_metrics.get(header, header)
            normalized[output_key] = value
        return normalized


def _compute_totals(rows: list[dict[str, Any]], metrics: list[str]) -> dict[str, float | int]:
    totals: dict[str, float | int] = {}
    for metric in metrics:
        running = 0.0
        integer = True
        for row in rows:
            value = row.get(metric)
            if value is None:
                continue
            if isinstance(value, int):
                running += value
            elif isinstance(value, float):
                integer = False
                running += value
            else:
                try:
                    parsed = float(value)
                    integer = integer and parsed.is_integer()
                    running += parsed
                except (TypeError, ValueError):
                    continue
        totals[metric] = int(running) if integer else running
    return totals
