from __future__ import annotations

from pathlib import Path

import typer

from ytx.commands.common import console, render_payload
from ytx.config import AppContext
from ytx.errors import EXIT_CODES
from ytx.utils.metrics import DIMENSION_ALIASES, FILTER_DIMENSIONS, METRIC_ALIASES

app = typer.Typer(help="Emit machine-readable schema for agent parameter discovery.")


@app.command("show")
def schema_show(
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    """Emit all valid metrics, dimensions, filters, date formats, and error codes.

    Agents should call this once to discover valid parameter values before
    constructing analytics queries.  All values are stable across patch releases.
    """
    ctx = AppContext()
    data = {
        "metrics": {
            alias: {"description": _METRIC_DESCRIPTIONS.get(alias, ""), "api_name": api_name}
            for alias, api_name in METRIC_ALIASES.items()
        },
        "dimensions": {
            alias: {"description": _DIMENSION_DESCRIPTIONS.get(alias, ""), "api_name": api_name}
            for alias, api_name in DIMENSION_ALIASES.items()
        },
        "filters": {
            alias: {"description": _FILTER_DESCRIPTIONS.get(alias, ""), "api_name": api_name, "syntax": f"{alias}==<value>"}
            for alias, api_name in FILTER_DIMENSIONS.items()
        },
        "date_range": {
            "range_format": "<N>d  (e.g. 7d, 28d, 90d, 365d) — trailing N days ending today",
            "explicit_format": "YYYY-MM-DD via --start-date and --end-date",
            "default": "last 28 days when no date option is supplied",
        },
        "entities": ["channel", "video"],
        "exit_codes": {
            code: {"exit_code": exit_code, "retryable": exit_code in {3}}
            for code, exit_code in EXIT_CODES.items()
        },
        "env_vars": {
            "YTX_OUTPUT": {
                "values": ["json", "csv"],
                "description": "Force output format for all commands without passing --json/--csv each time.",
            },
            "YTX_PROFILE": {
                "values": ["<profile_name>"],
                "description": "Default profile to use when --profile is not supplied.",
            },
        },
    }
    render_payload(
        api="schema",
        profile_name=ctx.profile_store.default_profile(),
        data=data,
        as_json=as_json,
        as_csv=False,
        output=output,
        human_renderer=lambda c, d: _human_schema(c, d),
    )


def _human_schema(c: object, data: dict) -> None:  # type: ignore[type-arg]
    console.print("\n[bold]Metrics[/bold]")
    for alias, info in data["metrics"].items():
        console.print(f"  {alias:25s}  {info['description']}")
    console.print("\n[bold]Dimensions[/bold]")
    for alias, info in data["dimensions"].items():
        console.print(f"  {alias:25s}  {info['description']}")
    console.print("\n[bold]Filters[/bold]")
    for alias, info in data["filters"].items():
        console.print(f"  {info['syntax']:35s}  {info['description']}")
    console.print("\n[bold]Date range[/bold]")
    for key, val in data["date_range"].items():
        console.print(f"  {key}: {val}")
    console.print("\n[bold]Exit codes[/bold]")
    for code, info in data["exit_codes"].items():
        retry = " (retryable)" if info["retryable"] else ""
        console.print(f"  {info['exit_code']}  {code}{retry}")
    console.print("\n[bold]Env vars[/bold]")
    for var, info in data["env_vars"].items():
        console.print(f"  {var}: {info['description']}")


_METRIC_DESCRIPTIONS: dict[str, str] = {
    "views": "Total view count",
    "watch_time": "Estimated minutes watched",
    "avg_view_duration": "Average view duration in seconds",
    "likes": "Number of likes",
    "comments": "Number of comments",
    "subs_gained": "Subscribers gained",
    "subs_lost": "Subscribers lost",
}

_DIMENSION_DESCRIPTIONS: dict[str, str] = {
    "day": "Break results down by calendar day (YYYY-MM-DD)",
}

_FILTER_DESCRIPTIONS: dict[str, str] = {
    "country": "ISO 3166-1 alpha-2 country code (e.g. country==US)",
    "video": "YouTube video ID (e.g. video==dQw4w9WgXcQ)",
}
