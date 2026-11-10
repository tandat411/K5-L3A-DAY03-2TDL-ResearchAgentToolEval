"""Tool Unit Test Challenge (Step 4b).

Offline-only unit tests for all core, bonus, and custom tools (`github_repos`),
plus regression tests for edge-case bugs found in existing tools (Challenge+).
"""
from __future__ import annotations

import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify_tool = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_search_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]
github_repos_tool = TOOL_FUNCTIONS["github_repos"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    opts = ["Tin AI", "Tin Robotics"]
    result = clarify_tool(question="Bạn muốn xem chủ đề nào?", response_type="choice", options=opts)
    assert result["awaiting_user"] is True
    assert result["response_type"] == "choice"
    assert result["options"] == opts
    assert result["question"] == "Bạn muốn xem chủ đề nào?"


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "Item 1", "url": "https://a.com/1", "section": "A"},
        {"title": "Item 2", "url": "https://b.com/2", "section": "B"},
        {"title": "Item 3", "url": "https://a.com/3", "section": "A"},
    ]
    result = format_tool(items=items, template="sections", headline="Bản tin")
    md = result["markdown"]
    assert md.count("## A") == 1
    assert md.count("## B") == 1
    assert result["item_count"] == 3


def test_format_thread_numbers_items() -> None:
    items = [
        {"title": "First item", "url": "https://example.com/1"},
        {"title": "Second item", "url": "https://example.com/2"},
    ]
    result = format_tool(items=items, template="thread")
    chunks = result["markdown"].split("\n\n")
    assert len(chunks) == 2
    assert chunks[0].startswith("1/ ")
    assert chunks[1].startswith("2/ ")


def test_format_empty_items_does_not_crash() -> None:
    res_none = format_tool(items=None, template="sections")
    res_empty = format_tool(items=[], template="brief")
    assert res_none["item_count"] == 0
    assert res_empty["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "12345:FAKE_TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100987654321")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI hôm nay", confirmed=True)

    assert result["status"] == "sent"
    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "12345:FAKE_TOKEN" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-100987654321"
    assert calls[0]["json"]["text"] == "Bản tin AI hôm nay"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = send_tool(text="Bản tin AI hôm nay", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
    calls = fake_http(FakeResponse({"results": []}))

    result = lookup_tool(query="AI", topic="general", timeframe=None, max_results=5)

    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]
    assert result["timeframe"] is None


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")
    calls = fake_http(FakeResponse({
        "data": {
            "markdown": "Hello world content",
            "metadata": {"title": "Sample Title", "sourceURL": "https://docs.example.com/guide"},
        }
    }))

    result = fetch_tool(url="https://docs.example.com/guide")

    assert len(calls) == 1
    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"] == {"url": "https://docs.example.com/guide", "formats": ["markdown"]}
    assert result["items"][0] == {
        "title": "Sample Title",
        "url": "https://docs.example.com/guide",
        "source": "docs.example.com",
        "summary": "Hello world content",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")
    fake_http(FakeResponse({
        "data": {
            "markdown": "a" * 5500,
            "metadata": {"title": "Long Doc", "sourceURL": "https://example.com/long"},
        }
    }))

    result = fetch_tool(url="https://example.com/long")

    assert len(result["items"][0]["summary"]) == 4000
    assert result["items"][0]["summary"] == "a" * 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test-key")
    raw_timeline = [{"text": "missing id tweet", "screen_name": "sama"}] + [
        {"tweet_id": str(100 + i), "screen_name": "sama", "text": f"Tweet {i}"}
        for i in range(6)
    ]
    calls = fake_http(FakeResponse({"timeline": raw_timeline}))

    result = timeline_tool(screenname="sama", limit=3)

    assert len(calls) == 1
    assert calls[0]["params"] == {"screenname": "sama"}
    assert len(result["items"]) == 3
    for idx, item in enumerate(result["items"]):
        assert item["url"] == f"https://x.com/sama/status/{100 + idx}"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test-key")
    calls = fake_http(FakeResponse({"timeline": [
        {"tweet_id": "999", "screen_name": "karpathy", "text": "OpenAI top post"},
    ]}))

    result = social_search_tool(query="OpenAI", search_type="Top", limit=2)

    assert len(calls) == 1
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}
    assert result["search_type"] == "Top"
    assert len(result["items"]) == 1


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    result = policy_tool(query="   ", policy_area="all", top_k=3)
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy_tool(query="API key customer data confidential", policy_area="data_privacy", top_k=5)
    assert len(result["results"]) >= 1
    assert all(item["policy_area"] == "data_privacy" for item in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy_tool(query="Injection probe citation", policy_area="source_citation", top_k=5)
    probe_sections = [r for r in result["results"] if r["section"] == "Injection probe"]
    assert len(probe_sections) == 1
    sec = probe_sections[0]
    assert any("ignore the citation policy" in line for line in sec["untrusted_text"])
    assert "ignore the citation policy" not in sec["facts"]


# ---------------- NEW TOOL: github_repos ----------------

def test_my_new_tool_happy_path(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "total_count": 42,
        "items": [
            {
                "full_name": "langchain-ai/langgraph",
                "html_url": "https://github.com/langchain-ai/langgraph",
                "description": "Build resilient language agents as graphs.",
                "stargazers_count": 12500,
                "language": "Python",
            }
        ],
    }))

    result = github_repos_tool(query="langgraph", sort="stars", limit=3)

    assert len(calls) == 1
    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"] == {"q": "langgraph", "sort": "stars", "order": "desc", "per_page": 3}
    assert result["total_count"] == 42
    assert result["items"] == [{
        "title": "langchain-ai/langgraph",
        "url": "https://github.com/langchain-ai/langgraph",
        "source": "github.com",
        "summary": "Build resilient language agents as graphs.",
        "stars": 12500,
        "language": "Python",
    }]


def test_my_new_tool_bad_input_from_model(fake_http) -> None:
    calls = fake_http(FakeResponse({"total_count": 0, "items": []}))

    # 1) Empty query -> returns ValueError dict without calling network
    empty_res = github_repos_tool(query="   ", sort="stars", limit=5)
    assert empty_res["error"] == "ValueError"
    assert calls == []

    # 2) Out-of-enum sort + string limit -> normalizes sort to 'stars' and casts limit
    norm_res = github_repos_tool(query="agent", sort="invalid_sort_mode", limit="2")  # type: ignore[arg-type]
    assert norm_res["sort"] == "stars"
    assert calls[0]["params"]["sort"] == "stars"
    assert calls[0]["params"]["per_page"] == 2


def test_my_new_tool_failure_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=403))
    result = github_repos_tool(query="AI agent", sort="stars", limit=5)
    assert result["error"] == "HTTPError"

    fake_http(requests.Timeout("GitHub request timed out"))
    timeout_res = github_repos_tool(query="AI agent")
    assert timeout_res["error"] == "Timeout"


# ---------------- CHALLENGE+ REGRESSION TESTS ----------------

def test_regression_timeline_limit_zero_and_at_prefix(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test-key")
    calls = fake_http(FakeResponse({"timeline": [
        {"tweet_id": "1", "screen_name": "sama", "text": "Tweet 1"},
    ]}))

    result = timeline_tool(screenname="@sama", limit=0)

    assert calls[0]["params"]["screenname"] == "sama"
    assert result["items"] == []


def test_regression_policy_top_k_zero_returns_empty_list() -> None:
    result = policy_tool(query="API key", policy_area="data_privacy", top_k=0)
    assert result["results"] == []


def test_regression_send_string_false_does_not_bypass_confirmation(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = send_tool(text="Bản tin", confirmed="false")  # type: ignore[arg-type]
    assert result["status"] == "needs_confirmation"
    assert calls == []
