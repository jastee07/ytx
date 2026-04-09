from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from ytx.errors import AuthError


class LocalSecretStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.credential_dir = self.root / "credentials"
        self.credential_dir.mkdir(parents=True, exist_ok=True)
        self.key_path = self.root / ".local.key"

    def _fernet(self) -> Fernet:
        if not self.key_path.exists():
            self.key_path.write_bytes(Fernet.generate_key())
        key = self.key_path.read_bytes()
        return Fernet(key)

    def save_json(self, name: str, payload: dict[str, Any]) -> None:
        encrypted = self._fernet().encrypt(json.dumps(payload).encode("utf-8"))
        (self.credential_dir / f"{name}.json.enc").write_bytes(encrypted)

    def load_json(self, name: str) -> dict[str, Any] | None:
        path = self.credential_dir / f"{name}.json.enc"
        if not path.exists():
            return None
        try:
            raw = self._fernet().decrypt(path.read_bytes())
        except InvalidToken as exc:
            raise AuthError(
                code="TOKEN_REFRESH_FAILED",
                message="Stored credentials could not be decrypted.",
            ) from exc
        return json.loads(raw.decode("utf-8"))

    def delete(self, name: str) -> None:
        path = self.credential_dir / f"{name}.json.enc"
        if path.exists():
            path.unlink()


class KeyringBackedStore:
    def __init__(self, service_name: str, fallback: LocalSecretStore) -> None:
        self.service_name = service_name
        self.fallback = fallback

    def _keyring(self):
        try:
            import keyring
        except ImportError:
            return None
        return keyring

    def save_json(self, name: str, payload: dict[str, Any]) -> None:
        serialized = json.dumps(payload)
        keyring = self._keyring()
        if keyring is None:
            self.fallback.save_json(name, payload)
            return
        keyring.set_password(self.service_name, name, serialized)

    def load_json(self, name: str) -> dict[str, Any] | None:
        keyring = self._keyring()
        if keyring is None:
            return self.fallback.load_json(name)
        raw = keyring.get_password(self.service_name, name)
        if raw is None:
            return self.fallback.load_json(name)
        return json.loads(raw)

    def delete(self, name: str) -> None:
        keyring = self._keyring()
        if keyring is not None:
            try:
                keyring.delete_password(self.service_name, name)
            except Exception:
                pass
        self.fallback.delete(name)
