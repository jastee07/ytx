# Agent Notes

## Purpose

This repository contains `ytx`, a read-only, agent-friendly YouTube CLI built with Typer.

The current scope is:

- OAuth installed-app login for creator-owned channels
- local profile and token reuse
- channel metadata and recent-video inventory reads
- YouTube Analytics queries with a stable JSON envelope
- YouTube Reporting API (bulk pre-defined reports)
- JSON and CSV export paths
- quota-aware, read-only defaults

Do not add write-side YouTube actions unless the user explicitly asks for them.

## Entry Points

- CLI root: `src/ytx/cli.py`
- Auth commands: `src/ytx/commands/auth.py`
- Channel commands: `src/ytx/commands/channel.py`
- Video commands: `src/ytx/commands/video.py`
- Analytics commands: `src/ytx/commands/analytics.py`
- Reporting commands: `src/ytx/commands/reporting.py`
- Doctor commands: `src/ytx/commands/doctor.py`

## Core Architecture

- `src/ytx/config.py`
  Handles local paths (via `platformdirs`), config loading, profile store, secret store, and SQLite cache wiring.
- `src/ytx/auth/`
  OAuth login flow, credential serialization, secure storage, and profile metadata.
  `refresh_credentials()` raises `AuthError(code="TOKEN_REFRESH_FAILED")` on revoked tokens or network failures — never a raw exception.
- `src/ytx/clients/`
  Thin wrappers over the Google API clients. All clients use `httplib2.Http(timeout=30)` and pass `num_retries=3` to `.execute()` for automatic backoff on transient errors.
- `src/ytx/services/`
  Business logic for channel reads, video reads, analytics normalization, and quota guidance.
- `src/ytx/models/`
  Pydantic response/query models used to keep CLI output stable.
- `src/ytx/formatters/`
  Human, JSON, and CSV output helpers.
- `src/ytx/utils/`
  Date parsing, metric aliasing, paging, and light utility helpers.
- `src/ytx/cache/sqlite_cache.py`
  TTL-based SQLite cache. Supports `list_all()` and `clear(namespace=)` for inspection and invalidation.

## Agent Affordances

### Environment variables
| Variable | Values | Purpose |
|----------|--------|---------|
| `YTX_OUTPUT` | `json`, `csv` | Force output format for all commands — agents should set `YTX_OUTPUT=json` so every response is machine-readable without passing `--json` per call |
| `YTX_PROFILE` | `<profile_name>` | Default profile — avoids passing `--profile` on every call |

### Exit codes
Agents can branch on exit codes without parsing JSON:
| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | — |
| 1 | Generic / unexpected error | Inspect JSON error envelope |
| 2 | `AUTH_REQUIRED` / `TOKEN_REFRESH_FAILED` | Requires human re-authentication |
| 3 | `QUOTA_EXCEEDED` / `RATE_LIMITED` | Back off and retry (retryable) |
| 4 | `INSUFFICIENT_SCOPE` | Re-login with broader scopes |
| 5 | `RESOURCE_NOT_FOUND` | Fix the ID and retry |
| 6 | Validation error | Fix query parameters and retry immediately |

### Parameter discovery
Call `ytx schema show --json` once at startup to obtain all valid metric aliases,
dimension aliases, filter syntax, date range formats, exit code table, and env vars.
The output is stable across patch releases.

### Error envelope
All errors emit a JSON envelope (when `--json` or `YTX_OUTPUT=json`):
```json
{
  "ok": false,
  "generated_at": "2024-01-15T10:30:00Z",
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "...",
    "details": {}
  }
}
```
Branch on `error.code` (not `error.message`) for stable agent logic.

## Product Rules

- Prefer `channels.list`, uploads-playlist traversal, and `videos.list`.
- Avoid `search.list` unless the user explicitly wants a path that requires it.
- Keep the CLI read-only by default.
- Preserve snake_case JSON keys.
- Keep the top-level envelope stable:
  - `ok`
  - `api`
  - `profile`
  - `generated_at`
  - `data`
- Return deterministic error codes for agent-facing failures.

## Current Command Surface

| Command | Description |
|---------|-------------|
| `ytx init` | Initialise config with OAuth client secret path |
| `ytx auth login/whoami/list-profiles/use/logout/scopes` | OAuth and profile management |
| `ytx channel get/videos/stats` | Channel metadata and analytics |
| `ytx video list/get/analytics` | Video inventory and per-video analytics |
| `ytx analytics query` | Generic Analytics API queries |
| `ytx reporting list-report-types/list-jobs/create-job/list-reports/download` | Reporting API (bulk CSV reports) |
| `ytx doctor [scopes\|quota\|token]` | Diagnostics and quota guidance |
| `ytx doctor cache show` | List all SQLite cache entries |
| `ytx doctor cache clear [--namespace <ns>]` | Delete cache entries |
| `ytx schema show` | Emit all valid metrics, dimensions, filters, exit codes, and env vars |

## Current Storage Layout

Config directory is resolved via `platformdirs.user_config_dir("ytx")`:

- Linux: `~/.config/ytx/`
- macOS: `~/Library/Application Support/ytx/`
- Windows: `%APPDATA%\ytx\`

Files within the config directory:

- `config.toml`
- `profiles.json`
- `cache.db`
- `credentials/<profile>.json.enc` when keyring is unavailable

## Validation

```bash
python -m pytest -q
```

Runtime target: Python 3.12+.

The repo tests deterministic local logic only. Live OAuth and Google API calls require real credentials and should not be added to automated tests.

## Editing Guidance

- Keep public metric aliases ergonomic. Raw Google metric names belong behind the alias layer.
- If you expand analytics support, validate metric/dimension/filter combinations before sending API requests.
- If you add new commands, wire them through the existing formatter and error-envelope helpers instead of inventing a new output shape.
- Reuse the cache namespaces already present before creating new storage patterns.
- Keep docs aligned with the implemented command surface.
- All API client calls must pass `num_retries=3` to `.execute()` to be consistent with the rest of the codebase.
