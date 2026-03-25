from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChannelProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_id: str
    title: str
    custom_url: Optional[str] = None
    published_at: Optional[str] = None
    country: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
