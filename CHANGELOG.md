# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-09

### Added
- OAuth installed-app login flow with multi-profile support
- Channel metadata retrieval (`ytx channel get`)
- Video inventory listing via uploads-playlist traversal (`ytx channel videos`, `ytx video list`)
- Per-video metadata lookup (`ytx video get`)
- Channel-level analytics with configurable date ranges (`ytx channel stats`)
- Per-video analytics with flexible metrics and dimensions (`ytx video analytics`)
- Generic YouTube Analytics API query interface (`ytx analytics query`)
- YouTube Reporting API support for bulk pre-defined CSV reports (`ytx reporting`)
- Stable JSON envelope output with deterministic error codes and exit codes
- Agent affordances: `YTX_OUTPUT` and `YTX_PROFILE` environment variables
- Machine-readable parameter discovery via `ytx schema show --json`
- SQLite TTL-based response cache with namespace support
- Encrypted credential storage using OS keyring with local Fernet fallback
- Diagnostic commands for scopes, quota, token, and cache inspection (`ytx doctor`)
- `--version` flag on the CLI
- CI pipeline with Ruff linting and pytest with 80% coverage threshold
- Pre-commit hooks for code formatting and linting
