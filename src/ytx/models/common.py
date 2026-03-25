from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Literal

from pydantic import BaseModel, ConfigDict, Field


class Envelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    api: str
    profile: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    data: Dict[str, Any]


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: Literal[False] = False
    error: ErrorDetail
