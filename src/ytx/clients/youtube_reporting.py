from __future__ import annotations

from typing import Any

from ytx.errors import ApiError, map_google_http_error


class YouTubeReportingClient:
    """Client for the YouTube Reporting API (bulk pre-defined reports).

    The Reporting API is oriented around predefined report types that are
    generated daily and stored as downloadable files, in contrast to the
    Analytics API which supports interactive ad-hoc queries.

    Typical usage:
      1. List available report types (list_report_types).
      2. Create a reporting job for a desired type (create_job).
      3. Poll for completed reports (list_reports).
      4. Download the CSV payload (download_report).
    """

    def __init__(self, credentials: Any) -> None:
        try:
            import httplib2
            from google_auth_httplib2 import AuthorizedHttp
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise ApiError(
                code="API_ERROR",
                message="google-api-python-client is required for YouTube Reporting access.",
            ) from exc
        http = AuthorizedHttp(credentials, http=httplib2.Http(timeout=30))
        self._service = build("youtubereporting", "v1", http=http, cache_discovery=False)

    # ------------------------------------------------------------------
    # Report types
    # ------------------------------------------------------------------

    def list_report_types(self, *, include_system_managed: bool = False) -> list[dict[str, Any]]:
        """Return all report types available to the authenticated channel."""
        try:
            response = (
                self._service.reportTypes()
                .list(includeSystemManaged=include_system_managed)
                .execute()
            )
        except Exception as exc:
            raise map_google_http_error(exc) from exc
        return response.get("reportTypes", [])

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------

    def list_jobs(self, *, include_system_managed: bool = False) -> list[dict[str, Any]]:
        """List all reporting jobs for the authenticated channel."""
        try:
            response = (
                self._service.jobs()
                .list(includeSystemManaged=include_system_managed)
                .execute()
            )
        except Exception as exc:
            raise map_google_http_error(exc) from exc
        return response.get("jobs", [])

    def create_job(self, *, report_type_id: str, name: str) -> dict[str, Any]:
        """Create a new reporting job for the given report type."""
        body = {"reportTypeId": report_type_id, "name": name}
        try:
            return self._service.jobs().create(body=body).execute()
        except Exception as exc:
            raise map_google_http_error(exc) from exc

    def delete_job(self, job_id: str) -> None:
        """Delete a reporting job by ID."""
        try:
            self._service.jobs().delete(jobId=job_id).execute()
        except Exception as exc:
            raise map_google_http_error(exc) from exc

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def list_reports(
        self,
        job_id: str,
        *,
        created_after: str | None = None,
        start_time_at_or_after: str | None = None,
    ) -> list[dict[str, Any]]:
        """List completed reports for a job.

        Args:
            job_id: The job whose reports to list.
            created_after: RFC 3339 timestamp; only return reports created after this time.
            start_time_at_or_after: RFC 3339 timestamp; filter by report start time.
        """
        params: dict[str, Any] = {"jobId": job_id}
        if created_after:
            params["createdAfter"] = created_after
        if start_time_at_or_after:
            params["startTimeAtOrAfter"] = start_time_at_or_after
        try:
            response = self._service.jobs().reports().list(**params).execute()
        except Exception as exc:
            raise map_google_http_error(exc) from exc
        return response.get("reports", [])

    def download_report(self, download_url: str) -> bytes:
        """Download the raw CSV bytes for a completed report.

        The download_url comes from a report object's ``downloadUrl`` field.
        Uses the media download helper from the discovery client.
        """
        try:
            request = self._service.media().download(resourceName="")
            request.uri = download_url
            _unused_response, content = request.execute(num_retries=3)
            return content
        except Exception as exc:
            raise map_google_http_error(exc) from exc
