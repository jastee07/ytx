from __future__ import annotations


def clamp_page_size(limit: int, max_page_size: int = 50) -> int:
    if limit <= 0:
        return 1
    return min(limit, max_page_size)
