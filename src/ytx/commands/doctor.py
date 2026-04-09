from __future__ import annotations

from pathlib import Path

import typer

from ytx.auth.session import load_credentials, refresh_credentials
from ytx.commands.common import console, get_profile_metadata, load_data_client, render_error, render_payload, render_rows
from ytx.config import AppContext
from ytx.errors import YtxError
from ytx.services.quota_service import command_quota_notes, known_expensive_paths

app = typer.Typer(help="Diagnostics and quota guidance.")
cache_app = typer.Typer(help="Inspect and clear the local response cache.")
app.add_typer(cache_app, name="cache")


@app.command()
def doctor(
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    checks = []
    try:
        checks.append({"check": "config_toml", "ok": ctx.paths.config_toml.exists(), "detail": str(ctx.paths.config_toml)})
        profile_meta = ctx.profile_store.get_profile(profile_name)
        checks.append({"check": "profile", "ok": profile_meta is not None, "detail": profile_name})
        creds = load_credentials(ctx.secret_store, profile_name)
        refresh_credentials(creds)
        checks.append({"check": "token_refresh", "ok": True, "detail": "refresh succeeded"})
        channel = load_data_client(ctx, profile_name).get_mine_channel()
        checks.append({"check": "channel_resolve", "ok": True, "detail": channel.get('id')})
        if profile_meta is not None:
            checks.append({"check": "granted_scopes", "ok": True, "detail": ",".join(profile_meta.get("granted_scopes", []))})
        render_payload(
            api="youtube_data",
            profile_name=profile_name,
            data={"items": checks},
            as_json=as_json,
            as_csv=False,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Doctor", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)


@app.command("scopes")
def doctor_scopes(
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        profile_meta = get_profile_metadata(ctx, profile_name)
        render_payload(
            api="youtube_data",
            profile_name=profile_name,
            data={"items": [{"scope": scope} for scope in profile_meta.get("granted_scopes", [])]},
            as_json=as_json,
            as_csv=False,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Scopes", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)


@app.command("quota")
def doctor_quota(
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    data = {
        "items": known_expensive_paths(),
        "notes": command_quota_notes(),
    }
    render_payload(
        api="youtube_data",
        profile_name=ctx.profile_store.default_profile(),
        data=data,
        as_json=as_json,
        as_csv=False,
        output=output,
        human_renderer=lambda c, d: (
            render_rows(c, "Quota Costs", {"items": d["items"]}),
            [console.print(note) for note in d["notes"]],
        ),
    )


@cache_app.command("show")
def doctor_cache_show(
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    """List all entries currently in the local SQLite cache."""
    ctx = AppContext()
    entries = ctx.cache.list_all()
    render_payload(
        api="cache",
        profile_name=ctx.profile_store.default_profile(),
        data={"items": entries, "total": len(entries)},
        as_json=as_json,
        as_csv=False,
        output=output,
        human_renderer=lambda c, d: render_rows(c, "Cache entries", d),
    )


@cache_app.command("clear")
def doctor_cache_clear(
    namespace: str | None = typer.Option(None, "--namespace", help="Only clear entries in this namespace."),
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    """Delete cached entries, optionally scoped to a namespace."""
    ctx = AppContext()
    deleted = ctx.cache.clear(namespace=namespace)
    render_payload(
        api="cache",
        profile_name=ctx.profile_store.default_profile(),
        data={"deleted": deleted, "namespace": namespace or "all"},
        as_json=as_json,
        as_csv=False,
        output=output,
        human_renderer=lambda c, d: render_rows(c, "Cache cleared", d),
    )


@app.command("token")
def doctor_token(
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        creds = load_credentials(ctx.secret_store, profile_name)
        render_payload(
            api="youtube_data",
            profile_name=profile_name,
            data={
                "token_expiry": creds.expiry.isoformat() if creds.expiry else None,
                "has_refresh_token": bool(creds.refresh_token),
                "scopes": list(creds.scopes or []),
            },
            as_json=as_json,
            as_csv=False,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Token", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)
