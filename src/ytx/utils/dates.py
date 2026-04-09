from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import re

from ytx.errors import ValidationError

_RANGE_RE = re.compile(r"^(?P<days>\d+)d$")


def today_utc() -> date:
    return datetime.now(UTC).date()


def iso_now() -> str:
    """Return current UTC time as an ISO-8601 string with a Z suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def parse_date_range(range_value: str | None, start_date: str | None, end_date: str | None) -> tuple[str, str]:
    if range_value and (start_date or end_date):
        raise ValidationError(
            code="INVALID_DATE_RANGE",
            message="Use either --range or --start-date/--end-date, not both.",
        )

    if range_value:
        match = _RANGE_RE.match(range_value)
        if not match:
            raise ValidationError(
                code="INVALID_DATE_RANGE",
                message="Range must look like 7d, 28d, 90d, or 365d.",
            )
        days = int(match.group("days"))
        if days <= 0:
            raise ValidationError(
                code="INVALID_DATE_RANGE",
                message="Range must be greater than zero days.",
            )
        end = today_utc()
        start = end - timedelta(days=days - 1)
        return start.isoformat(), end.isoformat()

    if bool(start_date) ^ bool(end_date):
        raise ValidationError(
            code="INVALID_DATE_RANGE",
            message="Both --start-date and --end-date are required together.",
        )

    if start_date and end_date:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        if start > end:
            raise ValidationError(
                code="INVALID_DATE_RANGE",
                message="Start date must be on or before end date.",
            )
        return start.isoformat(), end.isoformat()

    end = today_utc()
    start = end - timedelta(days=27)
    return start.isoformat(), end.isoformat()
