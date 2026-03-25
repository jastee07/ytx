from __future__ import annotations

from typing import Any

from ytx.errors import AuthError


def run_installed_app_flow(client_secret_path: str, scopes: list[str], port: int = 0):
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise AuthError(
            code="AUTH_REQUIRED",
            message="google-auth-oauthlib is required for login.",
        ) from exc

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes=scopes)
    credentials = flow.run_local_server(port=port)
    if not credentials:
        raise AuthError(code="AUTH_REQUIRED", message="OAuth login did not return credentials.")
    return credentials


def credentials_to_json(credentials: Any) -> dict[str, Any]:
    granted_scopes = list(getattr(credentials, "granted_scopes", None) or getattr(credentials, "scopes", None) or [])
    expiry = getattr(credentials, "expiry", None)
    return {
        "token": getattr(credentials, "token", None),
        "refresh_token": getattr(credentials, "refresh_token", None),
        "token_uri": getattr(credentials, "token_uri", None),
        "client_id": getattr(credentials, "client_id", None),
        "client_secret": getattr(credentials, "client_secret", None),
        "scopes": granted_scopes,
        "expiry": expiry.isoformat() if expiry else None,
    }
