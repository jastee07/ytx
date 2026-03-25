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
from ytx.policies.capabilities import READ_ANALYTICS, READ_VIDEO
from ytx.services.analytics_service import AnalyticsService
from ytx.services.channel_service import ChannelService
from ytx.services.video_service import VideoService
from ytx.utils.dates import parse_date_range

app = typer.Typer(help="Video inventory and analytics.")


@app.command("list")
def video_list(
    limit: int = typer.Option(25, "--limit"),
    published_after: str | None = typer.Option(None, "--published-after"),
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
        videos, next_page_token = service.list_recent_videos(profile_name, limit=limit)
        items = [video.model_dump() for video in videos]
        if published_after:
            items = [item for item in items if item["published_at"][:10] > published_after]
        render_payload(
            api="youtube_data",
            profile_name=profile_name,
            data={"items": items, "next_page_token": next_page_token},
            as_json=as_json,
            as_csv=as_csv,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Videos", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=1)


@app.command("get")
def video_get(
    video_id: str,
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        profile_meta = get_profile_metadata(ctx, profile_name)
        require_capability(profile_meta, READ_VIDEO)
        service = VideoService(load_data_client(ctx, profile_name), ctx.cache)
        video = service.get_video(video_id)
        render_payload(
            api="youtube_data",
            profile_name=profile_name,
            data=video.model_dump(),
            as_json=as_json,
            as_csv=False,
            output=output,
            human_renderer=lambda c, d: render_key_value(c, "Video", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=1)


@app.command("analytics")
def video_analytics(
    video_id: str,
    range_value: str | None = typer.Option(None, "--range"),
    start_date: str | None = typer.Option(None, "--start-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    dimensions: str | None = typer.Option(None, "--dimensions"),
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
        dimension_list = [dimensions] if dimensions else []
        service = AnalyticsService(load_analytics_client(ctx, profile_name), ctx.cache)
        report = service.query(
            AnalyticsQuery(
                entity="video",
                start_date=resolved_start,
                end_date=resolved_end,
                metrics=["views", "watch_time"],
                dimensions=dimension_list,
                filters=[],
                sort=[],
                max_results=None,
                video_id=video_id,
            )
        )
        render_payload(
            api="youtube_analytics",
            profile_name=profile_name,
            data=report.model_dump(),
            as_json=as_json,
            as_csv=as_csv,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Video Analytics", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=1)
