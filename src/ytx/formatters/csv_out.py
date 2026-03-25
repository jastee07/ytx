from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any

from rich.console import Console


def emit_csv(console: Console, rows: list[dict[str, Any]], output: Path | None = None) -> None:
    if not rows:
        rendered = ""
    else:
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        rendered = buffer.getvalue()
    if output:
        output.write_text(rendered, encoding="utf-8")
        return
    console.print(rendered.rstrip())
