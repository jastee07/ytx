from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VideoSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_id: str
    title: str
    published_at: str
    description: str | None = None
    channel_id: str
    privacy_status: str | None = None
    duration: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
