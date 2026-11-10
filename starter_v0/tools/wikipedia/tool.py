from __future__ import annotations

import re
from typing import Any

import requests

from tools._shared import TIMEOUT, err


def search_wikipedia(query: str = "", limit: int = 3) -> dict[str, Any]:
    """Search Wikipedia for encyclopedic articles and summaries."""
    try:
        clean_query = (query or "").strip()
        if not clean_query:
            return {"tool": "wikipedia", "error": "ValueError", "message": "Query must not be empty", "items": []}

        params = {
            "action": "query",
            "list": "search",
            "srsearch": clean_query,
            "format": "json",
            "srlimit": int(limit or 3),
        }
        headers = {"User-Agent": "ResearchAgentTool/1.0 (test@research-agent.local)"}
        
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params=params,
            headers=headers,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        search_results = data.get("query", {}).get("search", [])
        items = []
        for item in search_results:
            title = item.get("title", "")
            raw_snippet = item.get("snippet", "")
            # Remove HTML tags returned in snippet
            snippet = re.sub(r"<[^>]+>", "", raw_snippet).strip()
            pageid = item.get("pageid")
            url = f"https://en.wikipedia.org/?curid={pageid}" if pageid else f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            items.append({
                "title": title,
                "url": url,
                "summary": snippet,
                "pageid": pageid,
            })

        return {
            "tool": "wikipedia",
            "query": clean_query,
            "limit": int(limit or 3),
            "item_count": len(items),
            "items": items,
        }
    except Exception as exc:
        return err("wikipedia", exc)
