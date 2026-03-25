from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table


def emit_key_value_table(console: Console, title: str, values: dict[str, Any]) -> None:
    table = Table(title=title)
    table.add_column("Field")
    table.add_column("Value")
    for key, value in values.items():
        table.add_row(key, "" if value is None else str(value))
    console.print(table)


def emit_rows_table(console: Console, title: str, rows: list[dict[str, Any]]) -> None:
    table = Table(title=title)
    if not rows:
        console.print("No results.")
        return
    for key in rows[0].keys():
        table.add_column(str(key))
    for row in rows:
        table.add_row(*["" if value is None else str(value) for value in row.values()])
    console.print(table)
