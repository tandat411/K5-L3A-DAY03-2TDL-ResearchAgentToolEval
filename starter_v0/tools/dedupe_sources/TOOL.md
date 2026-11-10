---
name: dedupe_sources
track: bonus
kind: local_formatter
requires_env: []
inputs: [items]
outputs: [items, input_count, duplicate_count]
side_effect: false
---
# dedupe_sources

Removes duplicate research results by URL, keeping the first occurrence. URL
comparison ignores letter case and trailing slashes. Items without a URL are
kept because they cannot be safely matched to another source. This tool works
only with items already collected; it does not search the web or fetch pages.
