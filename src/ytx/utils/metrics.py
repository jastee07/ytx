from __future__ import annotations

from collections.abc import Iterable

from ytx.errors import ValidationError

METRIC_ALIASES = {
    "views": "views",
    "watch_time": "estimatedMinutesWatched",
    "avg_view_duration": "averageViewDuration",
    "likes": "likes",
    "comments": "comments",
    "subs_gained": "subscribersGained",
    "subs_lost": "subscribersLost",
}

DIMENSION_ALIASES = {
    "day": "day",
}

FILTER_DIMENSIONS = {
    "country": "country",
    "video": "video",
}


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def resolve_metrics(metrics: Iterable[str]) -> tuple[list[str], dict[str, str]]:
    raw_metrics = list(metrics)
    resolved: list[str] = []
    reverse: dict[str, str] = {}
    for metric in raw_metrics:
        if metric not in METRIC_ALIASES:
            raise ValidationError(
                code="INVALID_METRIC",
                message=f"Unsupported metric alias: {metric}",
                details={"supported_metrics": sorted(METRIC_ALIASES)},
            )
        api_name = METRIC_ALIASES[metric]
        resolved.append(api_name)
        reverse[api_name] = metric
    return resolved, reverse


def resolve_dimensions(dimensions: Iterable[str]) -> list[str]:
    resolved: list[str] = []
    for dimension in dimensions:
        if dimension not in DIMENSION_ALIASES:
            raise ValidationError(
                code="INVALID_DIMENSION",
                message=f"Unsupported dimension alias: {dimension}",
                details={"supported_dimensions": sorted(DIMENSION_ALIASES)},
            )
        resolved.append(DIMENSION_ALIASES[dimension])
    return resolved


def resolve_filters(filters: Iterable[str], video_id: str | None = None) -> list[str]:
    resolved = list(filters)
    if video_id:
        resolved.append(f"video=={video_id}")
    normalized: list[str] = []
    for raw_filter in resolved:
        if "==" not in raw_filter:
            raise ValidationError(
                code="INVALID_DIMENSION",
                message=f"Filter must use dimension==value syntax: {raw_filter}",
            )
        key, value = raw_filter.split("==", 1)
        key = key.strip()
        value = value.strip()
        if key not in FILTER_DIMENSIONS:
            raise ValidationError(
                code="INVALID_DIMENSION",
                message=f"Unsupported filter dimension: {key}",
                details={"supported_filters": sorted(FILTER_DIMENSIONS)},
            )
        normalized.append(f"{FILTER_DIMENSIONS[key]}=={value}")
    return normalized


def validate_metric_dimension_combo(metrics: list[str], dimensions: list[str]) -> None:
    if len(dimensions) > 1:
        raise ValidationError(
            code="INVALID_METRIC_DIMENSION_COMBO",
            message="v1 only supports zero dimensions or the day dimension.",
        )
    if dimensions and dimensions != ["day"]:
        raise ValidationError(
            code="INVALID_METRIC_DIMENSION_COMBO",
            message="v1 only supports the day dimension for analytics queries.",
        )
    if not metrics:
        raise ValidationError(
            code="INVALID_METRIC",
            message="At least one metric is required.",
        )
