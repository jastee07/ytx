from __future__ import annotations

import csv
import json
from io import StringIO

from rich.console import Console

from ytx.formatters.csv_out import emit_csv
from ytx.formatters.json_out import emit_json


def _capture_console() -> tuple[Console, StringIO]:
    buf = StringIO()
    console = Console(file=buf, no_color=True, width=80)
    return console, buf


class TestEmitJson:
    def test_newlines_and_brackets_in_description(self):
        console, buf = _capture_console()
        payload = {
            "title": "Test Video",
            "description": "Line 1\nLine 2\n[Music]\nLine 3",
        }
        emit_json(console, payload)
        parsed = json.loads(buf.getvalue())
        assert parsed["description"] == "Line 1\nLine 2\n[Music]\nLine 3"

    def test_long_description_no_wrapping(self):
        console, buf = _capture_console()
        long_desc = "A" * 200
        payload = {"description": long_desc}
        emit_json(console, payload)
        parsed = json.loads(buf.getvalue())
        assert parsed["description"] == long_desc


class TestEmitCsv:
    def test_brackets_preserved(self):
        console, buf = _capture_console()
        rows = [{"title": "Video", "tag": "[Intro]"}]
        emit_csv(console, rows)
        output = buf.getvalue()
        reader = csv.DictReader(StringIO(output))
        row = next(reader)
        assert row["tag"] == "[Intro]"
