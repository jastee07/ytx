from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class YtxError(Exception):
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


class AuthError(YtxError):
    pass


class ScopeError(YtxError):
    pass


class ApiError(YtxError):
    pass


class ValidationError(YtxError):
    pass


class QuotaRiskWarning(YtxError):
    pass
