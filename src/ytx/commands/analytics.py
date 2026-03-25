from __future__ import annotations

from pathlib import Path

import typer

from ytx.commands.common import (
    get_profile_metadata,
    load_analytics_client,
    render_error,
    render_payload,
    render_rows,
    require_capability,
)
from ytx.config import AppContext
from ytx.errors import ValidationError, YtxError
from ytx.models.analytics import AnalyticsQuery
from ytx.policies.capabilities import READ_ANALYTICS
from ytx.services.analytics_service import AnalyticsService
from ytx.utils.dates import parse_date_range
from ytx.utils.metrics import split_csv

app = typer.Typer(help="Generic YouTube Analytics queries.")


@app.command("query")
def analytics_query(
    entity: str = typer.Option(..., "--entity"),
    video_id: str | None = typer.Option(None, "--video-id"),
    range_value: str | None = typer.Option(None, "--range"),
    start_date: str | None = typer.Option(None, "--start-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    metrics: str = typer.Option(..., "--metrics"),
    dimensions: str | None = typer.Option(None, "--dimensions"),
    filters: str | None = typer.Option(None, "--filters"),
    sort: str | None = typer.Option(None, "--sort"),
    max_results: int | None = typer.Option(None, "--max-results"),
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    as_csv: bool = typer.Option(False, "--csv"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        if entity not in {"channel", "video"}:
            raise ValidationError(
                code="INVALID_DIMENSION",
                message="Entity must be channel or video.",
            )
        if entity == "video" and not video_id:
            raise ValidationError(
                code="INVALID_DIMENSION",
                message="Video analytics queries require --video-id.",
            )
        profile_meta = get_profile_metadata(ctx, profile_name)
        require_capability(profile_meta, READ_ANALYTICS)
        resolved_start, resolved_end = parse_date_range(range_value, start_date, end_date)
        query = AnalyticsQuery(
            entity=entity,
            start_date=resolved_start,
            end_date=resolved_end,
            metrics=split_csv(metrics),
            dimensions=split_csv(dimensions),
            filters=split_csv(filters),
            sort=split_csv(sort),
            max_results=max_results,
            video_id=video_id,
        )
        report = AnalyticsService(load_analytics_client(ctx, profile_name), ctx.cache).query(query)
        render_payload(
            api="youtube_analytics",
            profile_name=profile_name,
            data=report.model_dump(),
            as_json=as_json,
            as_csv=as_csv,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Analytics Query", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=1)
