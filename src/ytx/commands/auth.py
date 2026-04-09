from __future__ import annotations

from pathlib import Path

import typer

from ytx.auth.login import credentials_to_json, run_installed_app_flow
from ytx.commands.common import console, render_key_value, render_payload, render_rows
from ytx.commands.common import get_profile_metadata, load_data_client, render_error
from ytx.config import AppContext, Settings, write_settings
from ytx.errors import AuthError, EXIT_CODES, YtxError
from ytx.services.channel_service import normalize_channel

app = typer.Typer(help="Authentication and profile management.")


@app.command("login")
def auth_login(
    profile: str | None = typer.Option(None, "--profile"),
    client_secret_path: Path | None = typer.Option(None, "--client-secret-path"),
    headless: bool = typer.Option(
        False,
        "--headless",
        help="Print auth URL and prompt for code instead of opening a browser. Use this on remote/VM environments.",
    ),
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        secret_path = client_secret_path or (
            Path(ctx.settings.client_secret_path)
            if ctx.settings.client_secret_path
            else None
        )
        if secret_path is None:
            raise AuthError(
                code="AUTH_REQUIRED",
                message="No OAuth client secret configured. Run 'ytx init' or pass --client-secret-path.",
            )
        credentials = run_installed_app_flow(
            str(secret_path),
            ctx.settings.scopes,
            port=ctx.settings.local_oauth_port,
            headless=headless,
        )
        ctx.secret_store.save_json(profile_name, credentials_to_json(credentials))
        channel = normalize_channel(
            load_data_client(ctx, profile_name).get_mine_channel()
        )
        metadata = ctx.profile_store.upsert_profile(
            profile_name,
            channel_id=channel.channel_id,
            channel_title=channel.title,
            granted_scopes=list(
                getattr(credentials, "granted_scopes", None)
                or getattr(credentials, "scopes", None)
                or ctx.settings.scopes
            ),
        )
        render_payload(
            api="youtube_data",
            profile_name=profile_name,
            data={
                "profile_name": metadata["profile_name"],
                "channel_id": metadata["channel_id"],
                "channel_title": metadata["channel_title"],
                "granted_scopes": metadata["granted_scopes"],
            },
            as_json=as_json,
            as_csv=False,
            output=output,
            human_renderer=lambda c, d: render_key_value(c, "Authenticated Profile", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)


@app.command("whoami")
def auth_whoami(
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        profile_meta = get_profile_metadata(ctx, profile_name)
        creds = ctx.secret_store.load_json(profile_name) or {}
        data = {
            "profile_name": profile_name,
            "channel_id": profile_meta.get("channel_id"),
            "channel_title": profile_meta.get("channel_title"),
            "granted_scopes": profile_meta.get("granted_scopes", []),
            "token_expiry": creds.get("expiry"),
        }
        render_payload(
            api="youtube_data",
            profile_name=profile_name,
            data=data,
            as_json=as_json,
            as_csv=False,
            output=output,
            human_renderer=lambda c, d: render_key_value(c, "Current Profile", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)


@app.command("list-profiles")
def auth_list_profiles(
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profiles = ctx.profile_store.list_profiles()
    render_payload(
        api="youtube_data",
        profile_name=ctx.profile_store.default_profile(),
        data={"items": profiles},
        as_json=as_json,
        as_csv=False,
        output=output,
        human_renderer=lambda c, d: render_rows(c, "Profiles", d),
    )


@app.command("use")
def auth_use(profile_name: str) -> None:
    ctx = AppContext()
    if ctx.profile_store.get_profile(profile_name) is None:
        console.print(
            f"[red]AUTH_REQUIRED[/red]: Profile '{profile_name}' is not configured."
        )
        raise typer.Exit(code=EXIT_CODES.get("AUTH_REQUIRED", 1))
    ctx.profile_store.set_default_profile(profile_name)
    settings = ctx.settings
    settings.default_profile = profile_name
    write_settings(ctx.paths, settings)
    console.print(f"default profile: {profile_name}")


@app.command("logout")
def auth_logout(
    profile: str | None = typer.Option(None, "--profile"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    ctx.secret_store.delete(profile_name)
    ctx.profile_store.delete_profile(profile_name)
    console.print(f"removed profile: {profile_name}")


@app.command("scopes")
def auth_scopes(
    profile: str | None = typer.Option(None, "--profile"),
    as_json: bool = typer.Option(False, "--json"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    ctx = AppContext()
    profile_name = ctx.resolve_profile_name(profile)
    try:
        profile_meta = get_profile_metadata(ctx, profile_name)
        data = {
            "items": [
                {"scope": scope} for scope in profile_meta.get("granted_scopes", [])
            ]
        }
        render_payload(
            api="youtube_data",
            profile_name=profile_name,
            data=data,
            as_json=as_json,
            as_csv=False,
            output=output,
            human_renderer=lambda c, d: render_rows(c, "Granted Scopes", d),
        )
    except YtxError as error:
        render_error(error, as_json=as_json, output=output)
        raise typer.Exit(code=error.exit_code)


def init_command(
    client_secret_path: Path = typer.Option(
        ..., prompt=True, exists=True, file_okay=True, dir_okay=False
    ),
    default_profile: str = typer.Option("default", prompt=True),
    enable_analytics: bool = typer.Option(True, prompt=True),
    enable_monetary: bool = typer.Option(False, prompt=True),
    local_oauth_port: int = typer.Option(0, "--oauth-port"),
) -> None:
    ctx = AppContext()
    settings = Settings(
        default_profile=default_profile,
        client_secret_path=str(client_secret_path),
        enable_analytics=enable_analytics,
        enable_monetary=enable_monetary,
        local_oauth_port=local_oauth_port,
    )
    write_settings(ctx.paths, settings)
    console.print(f"initialized config: {ctx.paths.config_toml}")
