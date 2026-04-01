from __future__ import annotations

from typing import Any

from ytx.errors import ApiError, map_google_http_error


class YouTubeAnalyticsClient:
    def __init__(self, credentials: Any) -> None:
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise ApiError(code="API_ERROR", message="google-api-python-client is required for YouTube Analytics access.") from exc
        self._service = build("youtubeAnalytics", "v2", credentials=credentials, cache_discovery=False)

    def query(
        self,
        *,
        ids: str,
        start_date: str,
        end_date: str,
        metrics: list[str],
        dimensions: list[str],
        filters: list[str],
        sort: list[str],
        max_results: int | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "ids": ids,
            "startDate": start_date,
            "endDate": end_date,
            "metrics": ",".join(metrics),
        }
        if dimensions:
            params["dimensions"] = ",".join(dimensions)
        if filters:
            params["filters"] = ";".join(filters)
        if sort:
            params["sort"] = ",".join(sort)
        if max_results:
            params["maxResults"] = max_results
        try:
            return self._service.reports().query(**params).execute()
        except Exception as exc:
            raise map_google_http_error(exc) from exc
