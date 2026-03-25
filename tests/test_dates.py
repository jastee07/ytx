from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ytx.errors import ValidationError
from ytx.utils import dates


def test_parse_date_range_from_named_range(monkeypatch: pytest.MonkeyPatch) -> None:
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 3, 25, tzinfo=UTC)

    monkeypatch.setattr(dates, "datetime", FixedDateTime)
    assert dates.parse_date_range("7d", None, None) == ("2026-03-19", "2026-03-25")


def test_parse_date_range_rejects_mixed_flags() -> None:
    with pytest.raises(ValidationError) as exc:
        dates.parse_date_range("28d", "2026-03-01", "2026-03-28")
    assert exc.value.code == "INVALID_DATE_RANGE"


def test_parse_date_range_rejects_reversed_dates() -> None:
    with pytest.raises(ValidationError) as exc:
        dates.parse_date_range(None, "2026-03-28", "2026-03-01")
    assert exc.value.code == "INVALID_DATE_RANGE"
