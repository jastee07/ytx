"""Tests for auth/session.py — credential loading, refresh, and persistence."""

from __future__ import annotations

from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from conftest import FakeSecretStore
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
        creds.refresh.side_effect = google.auth.exceptions.RefreshError(
            "Token has been revoked."
        )
        with pytest.raises(AuthError) as exc_info:
            refresh_credentials(creds)
        assert exc_info.value.code == "TOKEN_REFRESH_FAILED"
        assert "ytx auth login" in exc_info.value.message

    def test_transport_error_surfaces_as_auth_error(self):
        import google.auth.exceptions

        from ytx.auth.session import refresh_credentials

        creds = _expired_creds()
        creds.refresh.side_effect = google.auth.exceptions.TransportError(
            "Network failure."
        )
        with pytest.raises(AuthError) as exc_info:
            refresh_credentials(creds)
        assert exc_info.value.code == "TOKEN_REFRESH_FAILED"
        assert "Network error" in exc_info.value.message


class TestLoadCredentials:
    def test_missing_credentials_raises_auth_error(self):
        from ytx.auth.session import load_credentials

        store = FakeSecretStore()
        with pytest.raises(AuthError) as exc_info:
            load_credentials(store, "nonexistent")
        assert exc_info.value.code == "AUTH_REQUIRED"

    def test_loads_valid_credentials(self):
        from ytx.auth.session import load_credentials

        store = FakeSecretStore(
            data={
                "myprofile": {
                    "token": "tok",
                    "refresh_token": "ref",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": "cid",
                    "client_secret": "csec",
                    "scopes": ["https://www.googleapis.com/auth/youtube.readonly"],
                    "expiry": "2026-12-31T00:00:00Z",
                }
            }
        )
        creds = load_credentials(store, "myprofile")
        assert creds.token == "tok"
        assert creds.refresh_token == "ref"
        assert creds.expiry is not None


class TestPersistCredentials:
    def test_roundtrip_persist_and_load(self):
        from ytx.auth.session import persist_credentials

        store = FakeSecretStore()
        creds = SimpleNamespace(
            token="tok",
            refresh_token="ref",
            token_uri="https://oauth2.googleapis.com/token",
            client_id="cid",
            client_secret="csec",
            granted_scopes=["scope1"],
            scopes=None,
            expiry=datetime(2026, 12, 31, tzinfo=UTC),
        )
        persist_credentials(store, "test", creds)
        loaded_data = store.load_json("test")
        assert loaded_data["token"] == "tok"
        assert loaded_data["refresh_token"] == "ref"
        assert loaded_data["scopes"] == ["scope1"]

    def test_persist_handles_no_expiry(self):
        from ytx.auth.session import persist_credentials

        store = FakeSecretStore()
        creds = SimpleNamespace(
            token="tok",
            refresh_token="ref",
            token_uri="uri",
            client_id="cid",
            client_secret="csec",
            granted_scopes=None,
            scopes=["s1"],
            expiry=None,
        )
        persist_credentials(store, "test", creds)
        loaded = store.load_json("test")
        assert loaded["expiry"] is None
        assert loaded["scopes"] == ["s1"]
