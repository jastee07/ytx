## ytx

`ytx` is a read-only, agent-friendly YouTube CLI built around the official YouTube Data API v3 and YouTube Analytics API.

### Current commands

- `ytx init`
- `ytx auth login`
- `ytx auth whoami`
- `ytx auth list-profiles`
- `ytx auth use`
- `ytx auth logout`
- `ytx auth scopes`
- `ytx channel get`
- `ytx channel videos`
- `ytx channel stats`
- `ytx video list`
- `ytx video get`
- `ytx video analytics`
- `ytx analytics query`
- `ytx doctor`

### Setup

1. Create a Google Cloud project.
2. Enable the YouTube Data API v3 and YouTube Analytics API.
3. Create an OAuth desktop client.
4. Install the package and run `ytx init`.
5. Run `ytx auth login`.

### Development

Install with:

```bash
pip install -e .[dev]
```

Run tests with:

```bash
PYTHONPATH=src pytest -q
```
# ytx
An agent friendly CLI tool for YouTube API's
