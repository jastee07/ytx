from __future__ import annotations

from ytx.policies.capabilities import (
    READ_ANALYTICS,
    READ_CHANNEL,
    READ_REPORTING,
    READ_VIDEO,
)

YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
YT_ANALYTICS_READONLY_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"
YT_ANALYTICS_MONETARY_SCOPE = (
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly"
)

CAPABILITY_SCOPES = {
    READ_CHANNEL: [YOUTUBE_READONLY_SCOPE],
    READ_VIDEO: [YOUTUBE_READONLY_SCOPE],
    READ_ANALYTICS: [YT_ANALYTICS_READONLY_SCOPE],
    READ_REPORTING: [YT_ANALYTICS_READONLY_SCOPE],
}

DEFAULT_SCOPES = [YOUTUBE_READONLY_SCOPE, YT_ANALYTICS_READONLY_SCOPE]
