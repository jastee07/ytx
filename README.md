## ytx

![CI](https://github.com/jastee07/ytx/actions/workflows/python-app.yml/badge.svg)

`ytx` is a read-only, agent-friendly YouTube CLI built around the official YouTube Data API v3, YouTube Analytics API, and YouTube Reporting API.

### Features

- **Read-only by default** — no write operations against the YouTube API
- **Agent-friendly** — stable JSON envelope, deterministic exit codes, environment variable controls
- **Multi-profile** — manage multiple channel profiles locally
- **Cached** — SQLite TTL-based cache reduces redundant API calls
- **Quota-aware** — prefers low-cost API methods; avoids `search.list`
- **Secure** — credentials stored in OS keyring or AES-encrypted local files

### Install

```bash
pip install git+https://github.com/jastee07/ytx.git
```

Requires Python 3.12+.

### Setup

1. Create a Google Cloud project.
2. Enable the YouTube Data API v3 and YouTube Analytics API.
3. Create an OAuth desktop client and download the client secret JSON.
4. Run `ytx init` and point it at the client secret file.
5. Run `ytx auth login` to authenticate.

### Quick start

```bash
# Authenticate
ytx auth login

# Get channel metadata as JSON
ytx channel get --json
```

```json
{
  "ok": true,
  "api": "youtube_data",
  "profile": "default",
  "generated_at": "2026-04-09T12:00:00Z",
  "data": {
    "channel_id": "UC...",
    "title": "My Channel",
    "subscriber_count": 1500,
    "video_count": 42,
    "view_count": 120000
  }
}
```

```bash
# Channel analytics for the last 28 days
ytx channel stats --range 28d --json

# Per-video analytics
ytx video analytics VIDEO_ID --range 7d --metrics views,watch_time --json

# List recent videos
ytx channel videos --limit 10 --json
```

### Agent integration

Agents should set `YTX_OUTPUT=json` so every response is machine-readable, and optionally `YTX_PROFILE=<name>` to select a profile.

```bash
export YTX_OUTPUT=json
export YTX_PROFILE=default
```

Call `ytx schema show --json` once at startup to discover all valid metrics, dimensions, filters, exit codes, and environment variables.

**Exit codes** allow branching without parsing JSON:

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | — |
| 1 | Generic error | Inspect JSON error envelope |
| 2 | Auth required | Human re-authentication needed |
| 3 | Quota / rate limit | Back off and retry |
| 4 | Insufficient scope | Re-login with broader scopes |
| 5 | Resource not found | Fix the ID and retry |
| 6 | Validation error | Fix query parameters |

### Commands

| Command | Description |
|---------|-------------|
| `ytx init` | Initialize config with OAuth client secret path |
| `ytx auth login` | Authenticate via OAuth |
| `ytx auth whoami` | Show current profile |
| `ytx auth list-profiles` | List all profiles |
| `ytx auth use <name>` | Switch default profile |
| `ytx auth logout` | Remove profile and credentials |
| `ytx auth scopes` | Show granted OAuth scopes |
| `ytx channel get` | Channel metadata |
| `ytx channel videos` | Recent video inventory |
| `ytx channel stats` | Channel-level analytics |
| `ytx video list` | List videos with optional filters |
| `ytx video get <id>` | Single video metadata |
| `ytx video analytics <id>` | Per-video analytics |
| `ytx analytics query` | Generic Analytics API query |
| `ytx reporting list-report-types` | Available bulk report types |
| `ytx reporting list-jobs` | Active reporting jobs |
| `ytx reporting create-job` | Create a new reporting job |
| `ytx reporting list-reports` | Completed reports for a job |
| `ytx reporting download` | Download a bulk CSV report |
| `ytx doctor` | Run diagnostic checks |
| `ytx doctor scopes` | Show granted scopes |
| `ytx doctor quota` | Quota cost guidance |
| `ytx doctor token` | Token expiry details |
| `ytx doctor cache show` | List cache entries |
| `ytx doctor cache clear` | Clear cache entries |
| `ytx schema show` | Emit parameter discovery schema |

### Development

```bash
pip install -e ".[dev]"
python -m pytest --cov=ytx -q
```

### License

MIT
