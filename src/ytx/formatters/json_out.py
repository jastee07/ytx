from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console

from ytx.models.common import Envelope, ErrorEnvelope


def emit_json(
    console: Console,
    payload: Envelope | ErrorEnvelope | dict[str, Any],
    output: Path | None = None,
) -> None:
    if hasattr(payload, "model_dump"):
        data = payload.model_dump()
    else:
        data = payload
    rendered = json.dumps(data, indent=2, sort_keys=False)
    if output:
        output.write_text(rendered + "\n", encoding="utf-8")
        return
    console.print(rendered)
