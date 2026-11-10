from __future__ import annotations

from typing import Any


def dedupe_sources(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Remove items with duplicate URLs, keeping the first occurrence."""
    if items is None:
        items = []

    if not isinstance(items, list):
        return {
            "tool": "dedupe_sources",
            "error": "TypeError",
            "message": "items must be a list",
        }

    unique_items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for item in items:
        if not isinstance(item, dict):
            continue

        url = str(item.get("url") or "").strip()
        normalized_url = url.rstrip("/").lower()

        # Keep entries without a URL; we cannot safely tell whether they duplicate.
        if not normalized_url or normalized_url not in seen_urls:
            unique_items.append(item)
            if normalized_url:
                seen_urls.add(normalized_url)

    return {
        "tool": "dedupe_sources",
        "items": unique_items,
        "input_count": len(items),
        "duplicate_count": len(items) - len(unique_items),
    }