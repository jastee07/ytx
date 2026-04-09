from __future__ import annotations

import json
import unittest.mock

import pytest

from ytx.auth.store import KeyringBackedStore, LocalSecretStore
from ytx.errors import AuthError


class TestLocalSecretStore:
    def test_save_and_load_roundtrip(self, tmp_path):
        store = LocalSecretStore(tmp_path)
        payload = {"token": "abc123", "refresh_token": "def456"}
        store.save_json("myprofile", payload)
        loaded = store.load_json("myprofile")
        assert loaded == payload

    def test_load_missing_returns_none(self, tmp_path):
        store = LocalSecretStore(tmp_path)
        assert store.load_json("nonexistent") is None

    def test_delete_removes_file(self, tmp_path):
        store = LocalSecretStore(tmp_path)
        store.save_json("todelete", {"token": "x"})
        assert store.load_json("todelete") is not None
        store.delete("todelete")
        assert store.load_json("todelete") is None

    def test_delete_nonexistent_is_noop(self, tmp_path):
        store = LocalSecretStore(tmp_path)
        store.delete("nonexistent")  # should not raise

    def test_corrupted_data_raises_auth_error(self, tmp_path):
        store = LocalSecretStore(tmp_path)
        # Write garbage bytes to the encrypted file
        cred_dir = tmp_path / "credentials"
        cred_dir.mkdir(parents=True, exist_ok=True)
        (cred_dir / "bad.json.enc").write_bytes(b"not-valid-fernet-data")
        with pytest.raises(AuthError) as exc_info:
            store.load_json("bad")
        assert exc_info.value.code == "TOKEN_REFRESH_FAILED"

    def test_creates_directories(self, tmp_path):
        root = tmp_path / "deep" / "nested"
        LocalSecretStore(root)
        assert root.exists()
        assert (root / "credentials").exists()

    def test_fernet_key_generated_once(self, tmp_path):
        store = LocalSecretStore(tmp_path)
        store.save_json("first", {"a": 1})
        key1 = store.key_path.read_bytes()
        store.save_json("second", {"b": 2})
        key2 = store.key_path.read_bytes()
        assert key1 == key2


class TestKeyringBackedStore:
    def test_falls_back_to_local_when_keyring_unavailable(self, tmp_path):
        local = LocalSecretStore(tmp_path)
        store = KeyringBackedStore("ytx", local)
        # Mock _keyring to return None (keyring not available)
        with unittest.mock.patch.object(store, "_keyring", return_value=None):
            store.save_json("profile1", {"token": "abc"})
            loaded = store.load_json("profile1")
        assert loaded == {"token": "abc"}

    def test_uses_keyring_when_available(self, tmp_path):
        local = LocalSecretStore(tmp_path)
        store = KeyringBackedStore("ytx", local)
        mock_keyring = unittest.mock.MagicMock()
        mock_keyring.get_password.return_value = json.dumps({"token": "from-keyring"})
        with unittest.mock.patch.object(store, "_keyring", return_value=mock_keyring):
            store.save_json("profile1", {"token": "saved"})
            mock_keyring.set_password.assert_called_once_with(
                "ytx", "profile1", json.dumps({"token": "saved"})
            )
            loaded = store.load_json("profile1")
        assert loaded == {"token": "from-keyring"}

    def test_load_falls_back_when_keyring_returns_none(self, tmp_path):
        local = LocalSecretStore(tmp_path)
        local.save_json("fallback", {"token": "local-token"})
        store = KeyringBackedStore("ytx", local)
        mock_keyring = unittest.mock.MagicMock()
        mock_keyring.get_password.return_value = None
        with unittest.mock.patch.object(store, "_keyring", return_value=mock_keyring):
            loaded = store.load_json("fallback")
        assert loaded == {"token": "local-token"}

    def test_delete_cleans_both_keyring_and_local(self, tmp_path):
        local = LocalSecretStore(tmp_path)
        local.save_json("todelete", {"token": "x"})
        store = KeyringBackedStore("ytx", local)
        mock_keyring = unittest.mock.MagicMock()
        with unittest.mock.patch.object(store, "_keyring", return_value=mock_keyring):
            store.delete("todelete")
        mock_keyring.delete_password.assert_called_once_with("ytx", "todelete")
        assert local.load_json("todelete") is None

    def test_delete_handles_keyring_error_gracefully(self, tmp_path):
        local = LocalSecretStore(tmp_path)
        local.save_json("todelete", {"token": "x"})
        store = KeyringBackedStore("ytx", local)
        mock_keyring = unittest.mock.MagicMock()
        mock_keyring.delete_password.side_effect = Exception("keyring error")
        with unittest.mock.patch.object(store, "_keyring", return_value=mock_keyring):
            store.delete("todelete")  # should not raise
        assert local.load_json("todelete") is None
