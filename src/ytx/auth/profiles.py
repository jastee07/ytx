from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


class ProfileStore:
    def __init__(self, profile_path: Path) -> None:
        self.profile_path = profile_path
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, Any]:
        if not self.profile_path.exists():
            return {"default_profile": "default", "profiles": {}}
        return json.loads(self.profile_path.read_text(encoding="utf-8"))

    def _save(self, payload: dict[str, Any]) -> None:
        self.profile_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def default_profile(self) -> str:
        return self._load().get("default_profile", "default")

    def set_default_profile(self, name: str) -> None:
        payload = self._load()
        payload["default_profile"] = name
        self._save(payload)

    def list_profiles(self) -> list[dict[str, Any]]:
        return list(self._load().get("profiles", {}).values())

    def get_profile(self, name: str) -> dict[str, Any] | None:
        return self._load().get("profiles", {}).get(name)

    def upsert_profile(
        self,
        name: str,
        channel_id: str,
        channel_title: str,
        granted_scopes: list[str],
    ) -> dict[str, Any]:
        payload = self._load()
        profiles = payload.setdefault("profiles", {})
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        current = profiles.get(name, {})
        current.update(
            {
                "profile_name": name,
                "channel_id": channel_id,
                "channel_title": channel_title,
                "granted_scopes": granted_scopes,
                "created_at": current.get("created_at", now),
                "updated_at": now,
            }
        )
        profiles[name] = current
        payload.setdefault("default_profile", name)
        self._save(payload)
        return current

    def delete_profile(self, name: str) -> None:
        payload = self._load()
        profiles = payload.get("profiles", {})
        profiles.pop(name, None)
        if payload.get("default_profile") == name:
            payload["default_profile"] = next(iter(profiles), "default")
        self._save(payload)
