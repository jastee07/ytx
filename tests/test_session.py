"""Tests for auth/session.py — credential refresh error handling."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ytx.errors import AuthError


def _expired_creds(has_refresh_token=True):
    creds = MagicMock()
    creds.valid = False
    creds.refresh_token = "tok" if has_refresh_token else None
    return creds


class TestRefreshCredentials:
    def test_valid_credentials_skip_refresh(self):
        from ytx.auth.session import refresh_credentials

        creds = MagicMock()
        creds.valid = True
        refresh_credentials(creds)
        creds.refresh.assert_not_called()

    def test_no_refresh_token_raises(self):
        from ytx.auth.session import refresh_credentials

        with pytest.raises(AuthError) as exc_info:
            refresh_credentials(_expired_creds(has_refresh_token=False))
        assert exc_info.value.code == "TOKEN_REFRESH_FAILED"

    def test_refresh_error_surfaces_as_auth_error(self):
        import google.auth.exceptions

        from ytx.auth.session import refresh_credentials

        creds = _expired_creds()
        creds.refresh.side_effect = google.auth.exceptions.RefreshError("Token has been revoked.")
        with pytest.raises(AuthError) as exc_info:
            refresh_credentials(creds)
        assert exc_info.value.code == "TOKEN_REFRESH_FAILED"
        assert "ytx auth login" in exc_info.value.message

    def test_transport_error_surfaces_as_auth_error(self):
        import google.auth.exceptions

        from ytx.auth.session import refresh_credentials

        creds = _expired_creds()
        creds.refresh.side_effect = google.auth.exceptions.TransportError("Network failure.")
        with pytest.raises(AuthError) as exc_info:
            refresh_credentials(creds)
        assert exc_info.value.code == "TOKEN_REFRESH_FAILED"
        assert "Network error" in exc_info.value.message
