from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from rich.console import Console

from ytx.auth.session import load_credentials, persist_credentials, refresh_credentials
from ytx.clients.youtube_analytics import YouTubeAnalyticsClient
from ytx.clients.youtube_data import YouTubeDataClient
from ytx.config import AppContext
from ytx.errors import ScopeError, ValidationError, YtxError
from ytx.formatters.csv_out import emit_csv
from ytx.formatters.json_out import emit_json
from ytx.formatters.table_out import emit_key_value_table, emit_rows_table
from ytx.models.common import Envelope, ErrorDetail, ErrorEnvelope
from ytx.policies.scopes import CAPABILITY_SCOPES

console = Console()


def build_envelope(api: str, profile_name: str, data: dict[str, Any]) -> Envelope:
    return Envelope(api=api, profile=profile_name, data=data)


def build_error(error: YtxError) -> ErrorEnvelope:
    return ErrorEnvelope(error=ErrorDetail(code=error.code, message=error.message, details=error.details))


def render_payload(
    *,
    api: str,
    profile_name: str,
    data: dict[str, Any],
    as_json: bool,
    as_csv: bool,
    output: Path | None,
    human_renderer: Callable[[Console, dict[str, Any]], None],
) -> None:
    if as_json and as_csv:
        raise ValidationError(code="API_ERROR", message="Use only one of --json or --csv.")
    envelope = build_envelope(api=api, profile_name=profile_name, data=data)
    if as_json:
        emit_json(console, envelope, output=output)
        return
    if as_csv:
        rows = extract_csv_rows(data)
        emit_csv(console, rows, output=output)
        return
    human_renderer(console, data)


def render_error(error: YtxError, as_json: bool = False, output: Path | None = None) -> None:
    if as_json:
        emit_json(console, build_error(error), output=output)
        return
    console.print(f"[red]{error.code}[/red]: {error.message}")
    if error.details:
        for key, value in error.details.items():
            console.print(f"{key}: {value}")


def extract_csv_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    if "items" in data and isinstance(data["items"], list):
        return data["items"]
    if "rows" in data and isinstance(data["rows"], list):
        return data["rows"]
    return [data]


def render_key_value(console: Console, title: str, data: dict[str, Any]) -> None:
    emit_key_value_table(console, title, data)


def render_rows(console: Console, title: str, data: dict[str, Any]) -> None:
    if "items" in data:
        emit_rows_table(console, title, data["items"])
        if data.get("next_page_token"):
            console.print(f"next_page_token: {data['next_page_token']}")
        return
    if "rows" in data:
        emit_rows_table(console, title, data["rows"])
        if data.get("totals"):
            emit_key_value_table(console, "Totals", data["totals"])
        return
    emit_rows_table(console, title, [data])


def get_profile_metadata(ctx: AppContext, profile_name: str) -> dict[str, Any]:
    profile = ctx.profile_store.get_profile(profile_name)
    if profile is None:
        raise YtxError(code="AUTH_REQUIRED", message=f"Profile '{profile_name}' is not configured.")
    return profile


def require_capability(profile: dict[str, Any], capability: str) -> None:
    required_scopes = CAPABILITY_SCOPES.get(capability, [])
    granted = set(profile.get("granted_scopes", []))
    missing = [scope for scope in required_scopes if scope not in granted]
    if missing:
        raise ScopeError(
            code="INSUFFICIENT_SCOPE",
            message=f"Command requires {capability}",
            details={"required_scopes": missing},
        )


def load_data_client(ctx: AppContext, profile_name: str) -> YouTubeDataClient:
    credentials = load_credentials(ctx.secret_store, profile_name)
    refresh_credentials(credentials)
    persist_credentials(ctx.secret_store, profile_name, credentials)
    return YouTubeDataClient(credentials)


def load_analytics_client(ctx: AppContext, profile_name: str) -> YouTubeAnalyticsClient:
    credentials = load_credentials(ctx.secret_store, profile_name)
    refresh_credentials(credentials)
    persist_credentials(ctx.secret_store, profile_name, credentials)
    return YouTubeAnalyticsClient(credentials)
