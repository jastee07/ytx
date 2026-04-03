from __future__ import annotations

from pathlib import Path

import typer

from ytx.commands.common import (
    get_profile_metadata,
    load_analytics_client,
    load_data_client,
    render_error,
    render_key_value,
    render_payload,
    render_rows,
    require_capability,
)
from ytx.config import AppContext
from ytx.errors import YtxError
from ytx.models.analytics import AnalyticsQuery
from ytx.policies.capabilities import READ_ANALYTICS, READ_CHANNEL, READ_VIDEO
from ytx.services.analytics_service import AnalyticsService
from ytx.services.channel_service import ChannelService
from ytx.utils.dates import parse_date_range

app = typer.Typer(help="Authenticated channel operations.")

DEFAULT_CHANNEL_METRICS = ["views", "watch_time", "avg_view_duration", "likes", "comments", "subs_gained", "subs_lost"]


@app.command("get")
def channel_get(
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        profile_meta = get_profile_metadata(ctx, profile_name)
        require_capability(profile_meta, READ_CHANNEL)
        service = ChannelService(load_data_client(ctx, profile_name), ctx.cache)
        channel = service.get_channel(profile_name)
        render_payload(
            api="youtube_data",
            profile_name=profile_name,
            data=channel.model_dump(),
            as_json=as_json,
            as_csv=False,
            output=output,
            human_renderer=lambda c, d: render_key_value(c, "Channel", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)


@app.command("videos")
def channel_videos(
    limit: int = typer.Option(25, "--limit"),
    page_token: str | None = typer.Option(None, "--page-token"),
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    as_csv: bool = typer.Option(False, "--csv"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        profile_meta = get_profile_metadata(ctx, profile_name)
        require_capability(profile_meta, READ_VIDEO)
        service = ChannelService(load_data_client(ctx, profile_name), ctx.cache)
        videos, next_page_token = service.list_recent_videos(profile_name, limit=limit, page_token=page_token)
        render_payload(
            api="youtube_data",
            profile_name=profile_name,
            data={"items": [video.model_dump() for video in videos], "next_page_token": next_page_token},
            as_json=as_json,
            as_csv=as_csv,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Channel Videos", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)


@app.command("stats")
def channel_stats(
    range_value: str | None = typer.Option(None, "--range"),
    start_date: str | None = typer.Option(None, "--start-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    as_csv: bool = typer.Option(False, "--csv"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        profile_meta = get_profile_metadata(ctx, profile_name)
        require_capability(profile_meta, READ_ANALYTICS)
        resolved_start, resolved_end = parse_date_range(range_value, start_date, end_date)
        service = AnalyticsService(load_analytics_client(ctx, profile_name), ctx.cache)
        report = service.query(
            AnalyticsQuery(
                entity="channel",
                start_date=resolved_start,
                end_date=resolved_end,
                metrics=DEFAULT_CHANNEL_METRICS,
                dimensions=[],
                filters=[],
                sort=[],
                max_results=None,
                video_id=None,
            )
        )
        render_payload(
            api="youtube_analytics",
            profile_name=profile_name,
            data=report.model_dump(),
            as_json=as_json,
            as_csv=as_csv,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Channel Stats", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)
