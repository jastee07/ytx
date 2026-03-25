from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class VideoSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_id: str
    title: str
    published_at: str
    description: Optional[str] = None
    channel_id: str
    privacy_status: Optional[str] = None
    duration: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
