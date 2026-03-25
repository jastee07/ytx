from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ChannelProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_id: str
    title: str
    custom_url: str | None = None
    published_at: str | None = None
    country: str | None = None
    subscriber_count: int | None = None
    video_count: int | None = None
    view_count: int | None = None
