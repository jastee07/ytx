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


def map_google_http_error(exc: Exception) -> ApiError:
    """Convert a googleapiclient.errors.HttpError into an ApiError with a stable code."""
    status = None
    reason = str(exc)
    try:
        # HttpError exposes .resp.status and .error_details / .reason
        status = int(exc.resp.status)  # type: ignore[attr-defined]
        reason = exc.reason or reason  # type: ignore[attr-defined]
    except Exception:
        pass

    if status == 401:
        return ApiError(code="AUTH_REQUIRED", message=f"Authentication required: {reason}")
    if status == 403:
        lower = reason.lower()
        if "quota" in lower or "rateLimitExceeded" in reason or "userRateLimitExceeded" in reason:
            return ApiError(code="QUOTA_EXCEEDED", message=f"Quota exceeded: {reason}")
        if "forbidden" in lower or "insufficientPermissions" in reason:
            return ApiError(code="INSUFFICIENT_SCOPE", message=f"Insufficient permissions: {reason}")
        return ApiError(code="QUOTA_EXCEEDED", message=f"Forbidden: {reason}")
    if status == 404:
        return ApiError(code="RESOURCE_NOT_FOUND", message=f"Resource not found: {reason}")
    if status == 429:
        return ApiError(code="RATE_LIMITED", message=f"Rate limited: {reason}")
    return ApiError(code="API_ERROR", message=f"YouTube API error (HTTP {status}): {reason}")
