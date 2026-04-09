from __future__ import annotations

import unittest.mock
from datetime import datetime, UTC
from types import SimpleNamespace

import pytest

from ytx.auth.login import credentials_to_json, run_installed_app_flow
from ytx.errors import AuthError


class TestCredentialsToJson:
    def test_serializes_all_fields(self):
        creds = SimpleNamespace(
            token="tok123",
            refresh_token="ref456",
            token_uri="https://oauth2.googleapis.com/token",
            client_id="cid",
            client_secret="csec",
            granted_scopes=["https://www.googleapis.com/auth/youtube.readonly"],
            scopes=None,
            expiry=datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC),
        )
        result = credentials_to_json(creds)
        assert result["token"] == "tok123"
        assert result["refresh_token"] == "ref456"
        assert result["token_uri"] == "https://oauth2.googleapis.com/token"
        assert result["client_id"] == "cid"
        assert result["client_secret"] == "csec"
        assert result["scopes"] == ["https://www.googleapis.com/auth/youtube.readonly"]
        assert "2026-06-15" in result["expiry"]

    def test_handles_missing_expiry(self):
        creds = SimpleNamespace(
            token="tok",
            refresh_token="ref",
            token_uri="uri",
            client_id="cid",
            client_secret="csec",
            granted_scopes=None,
            scopes=["scope1"],
            expiry=None,
        )
        result = credentials_to_json(creds)
        assert result["expiry"] is None
        assert result["scopes"] == ["scope1"]

    def test_handles_no_granted_scopes_falls_back_to_scopes(self):
        creds = SimpleNamespace(
            token="tok",
            refresh_token="ref",
            token_uri="uri",
            client_id="cid",
            client_secret="csec",
            scopes=["scope_a", "scope_b"],
            expiry=None,
        )
        # No granted_scopes attribute
        result = credentials_to_json(creds)
        assert result["scopes"] == ["scope_a", "scope_b"]

    def test_handles_no_scopes_at_all(self):
        creds = SimpleNamespace(
            token="tok",
            refresh_token="ref",
            token_uri="uri",
            client_id="cid",
            client_secret="csec",
            expiry=None,
        )
        result = credentials_to_json(creds)
        assert result["scopes"] == []


class TestRunInstalledAppFlow:
    def test_raises_auth_error_when_oauthlib_missing(self):
        with unittest.mock.patch.dict(
            "sys.modules",
            {"google_auth_oauthlib": None, "google_auth_oauthlib.flow": None},
        ):
            with pytest.raises(AuthError) as exc_info:
                run_installed_app_flow("/fake/secret.json", ["scope1"])
            assert exc_info.value.code == "AUTH_REQUIRED"

    def test_raises_auth_error_when_credentials_none(self):
        mock_flow_instance = unittest.mock.MagicMock()
        mock_flow_instance.run_local_server.return_value = None
        mock_flow_cls = unittest.mock.MagicMock()
        mock_flow_cls.from_client_secrets_file.return_value = mock_flow_instance
        with unittest.mock.patch(
            "ytx.auth.login.InstalledAppFlow", mock_flow_cls, create=True
        ):
            with unittest.mock.patch.dict(
                "sys.modules",
                {
                    "google_auth_oauthlib.flow": unittest.mock.MagicMock(
                        InstalledAppFlow=mock_flow_cls
                    )
                },
            ):
                with pytest.raises(AuthError) as exc_info:
                    run_installed_app_flow("/fake/secret.json", ["scope1"])
                assert exc_info.value.code == "AUTH_REQUIRED"

    def test_returns_credentials_on_success(self):
        fake_creds = SimpleNamespace(token="tok")
        mock_flow_instance = unittest.mock.MagicMock()
        mock_flow_instance.run_local_server.return_value = fake_creds
        mock_flow_cls = unittest.mock.MagicMock()
        mock_flow_cls.from_client_secrets_file.return_value = mock_flow_instance

        mock_module = unittest.mock.MagicMock()
        mock_module.InstalledAppFlow = mock_flow_cls
        with unittest.mock.patch.dict(
            "sys.modules",
            {
                "google_auth_oauthlib": mock_module,
                "google_auth_oauthlib.flow": mock_module,
            },
        ):
            result = run_installed_app_flow("/fake/secret.json", ["scope1"])
        assert result.token == "tok"
