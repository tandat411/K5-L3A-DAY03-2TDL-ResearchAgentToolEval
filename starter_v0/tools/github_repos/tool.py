from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
ALLOWED_SORTS = {"stars", "forks", "updated"}


def search_github_repos(query: str = "", sort: str = "stars", limit: int = 5) -> dict[str, Any]:
    try:
        cleaned_query = (query or "").strip() if isinstance(query, str) else ""
        if not cleaned_query:
            raise ValueError("query must not be empty")

        normalized_sort = str(sort or "stars").strip().lower()
        if normalized_sort not in ALLOWED_SORTS:
            normalized_sort = "stars"

        parsed_limit = int(limit) if limit is not None and str(limit).strip() != "" else 5
        if parsed_limit <= 0:
            return {
                "tool": "search_github_repos",
                "query": cleaned_query,
                "sort": normalized_sort,
                "total_count": 0,
                "items": [],
            }
        clamped_limit = min(parsed_limit, 20)

        user_agent = os.getenv("ARXIV_USER_AGENT", "AI20k-Day03-Research-Agent/1.0")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": user_agent,
        }
        response = requests.get(
            GITHUB_SEARCH_URL,
            params={"q": cleaned_query, "sort": normalized_sort, "order": "desc", "per_page": clamped_limit},
            headers=headers,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        raw_items = data.get("items") or []
        items = [{
            "title": item.get("full_name") or item.get("name") or "",
            "url": item.get("html_url") or "",
            "source": "github.com",
            "summary": item.get("description") or "",
            "stars": item.get("stargazers_count", 0),
            "language": item.get("language"),
        } for item in raw_items[:clamped_limit] if item.get("html_url") or item.get("full_name")]

        return {
            "tool": "search_github_repos",
            "query": cleaned_query,
            "sort": normalized_sort,
            "total_count": data.get("total_count", len(items)),
            "items": items,
        }
    except Exception as exc:
        return err("search_github_repos", exc)

