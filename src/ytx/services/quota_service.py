from __future__ import annotations


COMMAND_COSTS = {
    "channels.list": 1,
    "playlistItems.list": 1,
    "videos.list": 1,
    "search.list": 100,
    "youtubeAnalytics.reports.query": 1,
}


def known_expensive_paths() -> list[dict[str, int | str]]:
    return [
        {"method": method, "estimated_cost": cost}
        for method, cost in sorted(COMMAND_COSTS.items(), key=lambda item: item[1], reverse=True)
    ]


def command_quota_notes() -> list[str]:
    return [
        "Avoid search.list for inventory traversal; it costs 100 quota units.",
        "Prefer channels.list + uploads playlist traversal + videos.list for recent uploads.",
        "The CLI caches channel profiles, video inventory, and analytics queries to reduce repeat calls.",
    ]
