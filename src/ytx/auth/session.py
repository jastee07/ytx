from __future__ import annotations

from datetime import datetime
from typing import Any

from ytx.auth.store import KeyringBackedStore
from ytx.errors import AuthError


def load_credentials(secret_store: KeyringBackedStore, profile_name: str):
    try:
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise AuthError(code="AUTH_REQUIRED", message="google-auth is required to load credentials.") from exc

    payload = secret_store.load_json(profile_name)
    if payload is None:
        raise AuthError(
            code="AUTH_REQUIRED",
            message=f"No stored credentials found for profile '{profile_name}'.",
        )
    data = {
        "token": payload.get("token"),
        "refresh_token": payload.get("refresh_token"),
        "token_uri": payload.get("token_uri"),
        "client_id": payload.get("client_id"),
        "client_secret": payload.get("client_secret"),
        "scopes": payload.get("scopes", []),
    }
    credentials = Credentials(**data)
    expiry = payload.get("expiry")
    if expiry:
        credentials.expiry = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
    return credentials


def refresh_credentials(credentials: Any) -> None:
    if credentials.valid:
        return
    if not credentials.refresh_token:
        raise AuthError(code="TOKEN_REFRESH_FAILED", message="Credentials do not contain a refresh token.")
    try:
        from google.auth.transport.requests import Request
    except ImportError as exc:
        raise AuthError(code="TOKEN_REFRESH_FAILED", message="google-auth transport support is required.") from exc
    credentials.refresh(Request())


def persist_credentials(secret_store: KeyringBackedStore, profile_name: str, credentials: Any) -> None:
    expiry = getattr(credentials, "expiry", None)
    secret_store.save_json(
        profile_name,
        {
            "token": getattr(credentials, "token", None),
            "refresh_token": getattr(credentials, "refresh_token", None),
            "token_uri": getattr(credentials, "token_uri", None),
            "client_id": getattr(credentials, "client_id", None),
            "client_secret": getattr(credentials, "client_secret", None),
            "scopes": list(getattr(credentials, "granted_scopes", None) or getattr(credentials, "scopes", None) or []),
            "expiry": expiry.isoformat() if expiry else None,
        },
    )
