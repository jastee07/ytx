from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity: str
    start_date: str
    end_date: str
    metrics: list[str]
    dimensions: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)
    sort: list[str] = Field(default_factory=list)
    max_results: int | None = None
    video_id: str | None = None


class AnalyticsReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity: str
    start_date: str
    end_date: str
    metrics: list[str]
    dimensions: list[str]
    filters: list[str]
    rows: list[dict]
    totals: dict[str, float | int] | None = None
