from __future__ import annotations

import csv
import io
from pathlib import Path

import typer

from ytx.commands.common import (
    get_profile_metadata,
    load_reporting_client,
    render_error,
    render_payload,
    render_rows,
    require_capability,
)
from ytx.config import AppContext
from ytx.errors import YtxError
from ytx.policies.capabilities import READ_REPORTING

app = typer.Typer(help="YouTube Reporting API — bulk pre-defined reports.")


@app.command("list-report-types")
def reporting_list_report_types(
    include_system_managed: bool = typer.Option(False, "--include-system-managed"),
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    as_csv: bool = typer.Option(False, "--csv"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    """List report types available to the authenticated channel."""
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        profile_meta = get_profile_metadata(ctx, profile_name)
        require_capability(profile_meta, READ_REPORTING)
        client = load_reporting_client(ctx, profile_name)
        report_types = client.list_report_types(
            include_system_managed=include_system_managed
        )
        render_payload(
            api="youtube_reporting",
            profile_name=profile_name,
            data={"items": report_types},
            as_json=as_json,
            as_csv=as_csv,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Report Types", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)


@app.command("list-jobs")
def reporting_list_jobs(
    include_system_managed: bool = typer.Option(False, "--include-system-managed"),
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    as_csv: bool = typer.Option(False, "--csv"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    """List reporting jobs configured for the authenticated channel."""
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        profile_meta = get_profile_metadata(ctx, profile_name)
        require_capability(profile_meta, READ_REPORTING)
        client = load_reporting_client(ctx, profile_name)
        jobs = client.list_jobs(include_system_managed=include_system_managed)
        render_payload(
            api="youtube_reporting",
            profile_name=profile_name,
            data={"items": jobs},
            as_json=as_json,
            as_csv=as_csv,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Reporting Jobs", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)


@app.command("list-reports")
def reporting_list_reports(
    job_id: str = typer.Option(..., "--job-id"),
    created_after: str | None = typer.Option(
        None, "--created-after", help="RFC 3339 timestamp"
    ),
    start_time_at_or_after: str | None = typer.Option(
        None, "--start-time-at-or-after", help="RFC 3339 timestamp"
    ),
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    as_csv: bool = typer.Option(False, "--csv"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    """List completed reports for a reporting job."""
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        profile_meta = get_profile_metadata(ctx, profile_name)
        require_capability(profile_meta, READ_REPORTING)
        client = load_reporting_client(ctx, profile_name)
        reports = client.list_reports(
            job_id,
            created_after=created_after,
            start_time_at_or_after=start_time_at_or_after,
        )
        render_payload(
            api="youtube_reporting",
            profile_name=profile_name,
            data={"items": reports},
            as_json=as_json,
            as_csv=as_csv,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Reports", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)


@app.command("download")
def reporting_download(
    job_id: str = typer.Option(..., "--job-id"),
    report_id: str = typer.Option(..., "--report-id"),
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    """Download a completed report and emit its rows.

    Fetches the report identified by --job-id / --report-id, downloads
    the CSV bytes, parses them, and emits via the standard envelope.
    Use --output to write the raw CSV to a file instead.
    """
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        profile_meta = get_profile_metadata(ctx, profile_name)
        require_capability(profile_meta, READ_REPORTING)
        client = load_reporting_client(ctx, profile_name)
        reports = client.list_reports(job_id)
        target = next((r for r in reports if r.get("id") == report_id), None)
        if target is None:
            from ytx.errors import ApiError

            raise ApiError(
                code="RESOURCE_NOT_FOUND",
                message=f"Report '{report_id}' not found under job '{job_id}'.",
            )
        download_url = target.get("downloadUrl", "")
        raw_bytes = client.download_report(download_url)

        if output:
            output.write_bytes(raw_bytes)
            from ytx.commands.common import console

            console.print(f"Written to {output}")
            return

        text = raw_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        render_payload(
            api="youtube_reporting",
            profile_name=profile_name,
            data={"job_id": job_id, "report_id": report_id, "items": rows},
            as_json=as_json,
            as_csv=False,
            output=None,
            human_renderer=lambda c, d: render_rows(
                c, "Report Data", {"items": d["items"]}
            ),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)
