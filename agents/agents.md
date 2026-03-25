# Agent Notes

## Purpose

This repository contains `ytx`, a read-only, agent-friendly YouTube CLI built with Typer.

The current scope is:

- OAuth installed-app login for creator-owned channels
- local profile and token reuse
- channel metadata and recent-video inventory reads
- YouTube Analytics queries with a stable JSON envelope
- JSON and CSV export paths
- quota-aware, read-only defaults

Do not add write-side YouTube actions unless the user explicitly asks for them.

## Entry Points

- CLI root: `src/ytx/cli.py`
- Auth commands: `src/ytx/commands/auth.py`
- Channel commands: `src/ytx/commands/channel.py`
- Video commands: `src/ytx/commands/video.py`
- Analytics commands: `src/ytx/commands/analytics.py`
- Doctor commands: `src/ytx/commands/doctor.py`

## Core Architecture

- `src/ytx/config.py`
  Handles local paths, config loading, profile store, secret store, and SQLite cache wiring.
- `src/ytx/auth/`
  OAuth login flow, credential serialization, secure storage, and profile metadata.
- `src/ytx/clients/`
  Thin wrappers over the Google API clients.
- `src/ytx/services/`
  Business logic for channel reads, video reads, analytics normalization, and quota guidance.
- `src/ytx/models/`
  Pydantic response/query models used to keep CLI output stable.
- `src/ytx/formatters/`
  Human, JSON, and CSV output helpers.
- `src/ytx/utils/`
  Date parsing, metric aliasing, paging, and light utility helpers.

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

## Current Storage Layout

Expected local files under `~/.config/ytx/`:

- `config.toml`
- `profiles.json`
- `cache.db`
- `credentials/<profile>.json.enc` when keyring is unavailable

## Validation

Use:

```powershell
py -3.13 -m pytest -q
```

The repo currently tests deterministic local logic only. Live OAuth and Google API calls require real credentials and should not be added to automated tests.

## Editing Guidance

- Keep public metric aliases ergonomic. Raw Google metric names belong behind the alias layer.
- If you expand analytics support, validate metric/dimension/filter combinations before sending API requests.
- If you add new commands, wire them through the existing formatter and error-envelope helpers instead of inventing a new output shape.
- Reuse the cache namespaces already present before creating new storage patterns.
- Keep docs aligned with the implemented command surface.
