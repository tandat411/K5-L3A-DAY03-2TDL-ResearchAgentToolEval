---
name: github_repos
track: bonus
kind: live_api
provider: GitHub REST API
requires_env: []
inputs: [query, sort, limit]
outputs: [items, total_count]
side_effect: false
---
# github_repos

Searches public GitHub repositories via `https://api.github.com/search/repositories`.
Use when the user explicitly asks to find GitHub repositories or open-source codebases by topic/keyword.

