from __future__ import annotations

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity: str
    start_date: str
    end_date: str
    metrics: List[str]
    dimensions: List[str] = Field(default_factory=list)
    filters: List[str] = Field(default_factory=list)
    sort: List[str] = Field(default_factory=list)
    max_results: Optional[int] = None
    video_id: Optional[str] = None


class AnalyticsReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity: str
    start_date: str
    end_date: str
    metrics: List[str]
    dimensions: List[str]
    filters: List[str]
    rows: list[dict]
    totals: Optional[Dict[str, Union[float, int]]] = None
