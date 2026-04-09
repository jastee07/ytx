from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ytx.utils.dates import iso_now


class Envelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    api: str
    profile: str
    generated_at: str = Field(default_factory=iso_now)
    data: dict[str, Any]


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: Literal[False] = False
    generated_at: str = Field(default_factory=iso_now)
    error: ErrorDetail
