from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ytx.auth.profiles import ProfileStore
from ytx.auth.store import KeyringBackedStore, LocalSecretStore
from ytx.cache.sqlite_cache import SQLiteCache
from ytx.policies.scopes import DEFAULT_SCOPES, YT_ANALYTICS_MONETARY_SCOPE


@dataclass
class AppPaths:
    root: Path
    config_toml: Path
    profiles_json: Path
    cache_db: Path
    credentials_dir: Path


@dataclass
class Settings:
    default_profile: str = "default"
    client_secret_path: str | None = None
    enable_analytics: bool = True
    enable_monetary: bool = False
    local_oauth_port: int = 0

    @property
    def scopes(self) -> list[str]:
        scopes = list(DEFAULT_SCOPES if self.enable_analytics else DEFAULT_SCOPES[:1])
        if self.enable_monetary:
            scopes.append(YT_ANALYTICS_MONETARY_SCOPE)
        return scopes


class AppContext:
    def __init__(self) -> None:
        self.paths = build_paths()
        self.settings = load_settings(self.paths)
        self.profile_store = ProfileStore(self.paths.profiles_json)
        self.secret_store = KeyringBackedStore("ytx", LocalSecretStore(self.paths.root))
        self.cache = SQLiteCache(self.paths.cache_db)

    def resolve_profile_name(self, profile: str | None) -> str:
        if profile:
            return profile
        return self.profile_store.default_profile() or self.settings.default_profile


def build_paths() -> AppPaths:
    root = Path.home() / ".config" / "ytx"
    root.mkdir(parents=True, exist_ok=True)
    return AppPaths(
        root=root,
        config_toml=root / "config.toml",
        profiles_json=root / "profiles.json",
        cache_db=root / "cache.db",
        credentials_dir=root / "credentials",
    )


def load_settings(paths: AppPaths) -> Settings:
    if not paths.config_toml.exists():
        return Settings()
    app = _parse_simple_toml(paths.config_toml.read_text(encoding="utf-8")).get("app", {})
    return Settings(
        default_profile=app.get("default_profile", "default"),
        client_secret_path=app.get("client_secret_path"),
        enable_analytics=app.get("enable_analytics", True),
        enable_monetary=app.get("enable_monetary", False),
        local_oauth_port=app.get("local_oauth_port", 0),
    )


def write_settings(paths: AppPaths, settings: Settings) -> None:
    client_secret_path = (settings.client_secret_path or "").replace("\\", "/").replace('"', '\\"')
    contents = "\n".join(
        [
            "[app]",
            f'default_profile = "{settings.default_profile}"',
            f'client_secret_path = "{client_secret_path}"',
            f"enable_analytics = {str(settings.enable_analytics).lower()}",
            f"enable_monetary = {str(settings.enable_monetary).lower()}",
            f"local_oauth_port = {settings.local_oauth_port}",
            "",
        ]
    )
    paths.config_toml.write_text(contents, encoding="utf-8")


def _parse_simple_toml(contents: str) -> dict[str, dict[str, str | bool | int]]:
    section = None
    data: dict[str, dict[str, str | bool | int]] = {}
    for raw_line in contents.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            data.setdefault(section, {})
            continue
        if "=" not in line or section is None:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if value.startswith('"') and value.endswith('"'):
            parsed: str | bool | int = value[1:-1]
        elif value.lower() in {"true", "false"}:
            parsed = value.lower() == "true"
        else:
            parsed = int(value)
        data[section][key] = parsed
    return data
