from __future__ import annotations

from typing import Optional

import typer

from ytx import __version__
from ytx.commands.analytics import app as analytics_app
from ytx.commands.auth import app as auth_app, init_command
from ytx.commands.channel import app as channel_app
from ytx.commands.doctor import app as doctor_app
from ytx.commands.reporting import app as reporting_app
from ytx.commands.schema import app as schema_app
from ytx.commands.video import app as video_app


def _version_callback(value: bool) -> None:
    if value:
        print(f"ytx {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Read-only, agent-friendly YouTube CLI.")


@app.callback(invoke_without_command=True)
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    pass


app.command("init")(init_command)
app.add_typer(auth_app, name="auth")
app.add_typer(channel_app, name="channel")
app.add_typer(video_app, name="video")
app.add_typer(analytics_app, name="analytics")
app.add_typer(reporting_app, name="reporting")
app.add_typer(doctor_app, name="doctor")
app.add_typer(schema_app, name="schema")


if __name__ == "__main__":
    app()
