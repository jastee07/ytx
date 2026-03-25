from __future__ import annotations

import pytest

from ytx.errors import ValidationError
from ytx.utils.metrics import resolve_dimensions, resolve_filters, resolve_metrics, validate_metric_dimension_combo


def test_resolve_metrics_maps_aliases() -> None:
    metrics, reverse = resolve_metrics(["views", "watch_time", "subs_gained"])
    assert metrics == ["views", "estimatedMinutesWatched", "subscribersGained"]
    assert reverse["estimatedMinutesWatched"] == "watch_time"


def test_resolve_metrics_rejects_unknown_metric() -> None:
    with pytest.raises(ValidationError) as exc:
        resolve_metrics(["bogus"])
    assert exc.value.code == "INVALID_METRIC"


def test_resolve_dimensions_rejects_unknown_dimension() -> None:
    with pytest.raises(ValidationError) as exc:
        resolve_dimensions(["country"])
    assert exc.value.code == "INVALID_DIMENSION"


def test_resolve_filters_appends_video_filter() -> None:
    assert resolve_filters(["country==US"], video_id="abc123") == ["country==US", "video==abc123"]


def test_validate_metric_dimension_combo_only_supports_day() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_metric_dimension_combo(["views"], ["country"])
    assert exc.value.code == "INVALID_METRIC_DIMENSION_COMBO"
