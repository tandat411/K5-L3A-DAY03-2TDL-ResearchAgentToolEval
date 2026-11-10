"""TODO(student): Tool Unit Test Challenge.

Each test below is a real, robust test verifying tool code execution.
Patterns copied from test_tools_examples.py. Fixtures from conftest.py.

Rules:
- Offline only: mock HTTP with fake_http, set fake keys with monkeypatch.setenv.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = pytest tests/ -v shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    clarify_tool = TOOL_FUNCTIONS["clarify"]
    result = clarify_tool(question="Chọn phương án?", response_type="choice", options=["Opt1", "Opt2"])
    assert result["options"] == ["Opt1", "Opt2"]
    assert result["awaiting_user"] is True
    assert result["response_type"] == "choice"


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    items = [
        {"title": "Item 1", "section": "A"},
        {"title": "Item 2", "section": "B"},
        {"title": "Item 3", "section": "A"},
    ]
    result = format_tool(items=items, template="sections")
    assert result["markdown"].count("## A") == 1
    assert result["markdown"].count("## B") == 1
    assert "## A" in result["markdown"]
    assert "## B" in result["markdown"]


def test_format_thread_numbers_items() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    items = [{"title": "Post 1"}, {"title": "Post 2"}]
    result = format_tool(items=items, template="thread")
    lines = [line.strip() for line in result["markdown"].split("\n\n") if line.strip()]
    assert lines[0].startswith("1/ ")
    assert lines[1].startswith("2/ ")


def test_format_empty_items_does_not_crash() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    res1 = format_tool(items=[])
    res2 = format_tool(items=None)
    assert res1["item_count"] == 0
    assert res2["item_count"] == 0
    assert res1["markdown"] == ""
    assert res2["markdown"] == ""


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot123456:ABC-DEF")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123456789")
    calls = fake_http(FakeResponse({"ok": True}))
    send_tool = TOOL_FUNCTIONS["send"]
    result = send_tool(text="Bản tin công nghệ", confirmed=True)

    assert len(calls) == 1
    assert "bot123456:ABC-DEF/sendMessage" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-100123456789"
    assert calls[0]["json"]["text"] == "Bản tin công nghệ"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    send_tool = TOOL_FUNCTIONS["send"]
    result = send_tool(text="Test", confirmed=True)
    assert calls == []
    assert result["error"] == "RuntimeError"


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))
    lookup_tool = TOOL_FUNCTIONS["lookup"]
    lookup_tool(query="AI research", timeframe=None)
    assert "time_range" not in calls[0]["json"]
    assert calls[0]["json"]["query"] == "AI research"


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-fc-key")
    calls = fake_http(FakeResponse({
        "data": {
            "markdown": "Nội dung bài viết",
            "metadata": {"title": "Tiêu đề bài viết", "sourceURL": "https://example.com/article"},
        }
    }))
    fetch_tool = TOOL_FUNCTIONS["fetch"]
    result = fetch_tool(url="https://example.com/article")
    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert result["items"][0]["title"] == "Tiêu đề bài viết"
    assert result["items"][0]["url"] == "https://example.com/article"
    assert result["items"][0]["source"] == "example.com"
    assert result["items"][0]["summary"] == "Nội dung bài viết"


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-fc-key")
    fake_http(FakeResponse({
        "data": {
            "markdown": "A" * 6000,
            "metadata": {"title": "Title", "sourceURL": "https://example.com/long"},
        }
    }))
    fetch_tool = TOOL_FUNCTIONS["fetch"]
    result = fetch_tool(url="https://example.com/long")
    assert len(result["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-key")
    tweets = [{"tweet_id": f"id_{i}", "text": f"Tweet {i}", "screen_name": "sama"} for i in range(6)]
    # item missing id
    tweets.insert(0, {"text": "No ID tweet", "screen_name": "sama"})
    fake_http(FakeResponse({"timeline": tweets}))
    timeline_tool = TOOL_FUNCTIONS["timeline"]
    result = timeline_tool(screenname="sama", limit=3)
    assert len(result["items"]) == 3
    for item in result["items"]:
        assert item["url"].startswith("https://x.com/sama/status/id_")


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-key")
    calls = fake_http(FakeResponse({"tweets": []}))
    social_search_tool = TOOL_FUNCTIONS["social_search"]
    social_search_tool(query="OpenAI", search_type="Top")
    assert calls[0]["params"]["query"] == "OpenAI"
    assert calls[0]["params"]["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="privacy data", policy_area="data_privacy")
    assert len(result["results"]) > 0
    for r in result["results"]:
        assert r["policy_area"] == "data_privacy"


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="injection probe", policy_area="source_citation")
    all_untrusted = [item for r in result["results"] for item in r.get("untrusted_text", [])]
    assert len(all_untrusted) > 0
    assert any("Assistant: ignore" in line for line in all_untrusted)
    for r in result["results"]:
        for untrusted_item in r.get("untrusted_text", []):
            assert untrusted_item not in r["facts"]


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

def test_my_new_tool_happy_path(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "query": {
            "search": [
                {"title": "Alan Turing", "pageid": 12345, "snippet": "<span>Alan Mathison Turing</span> was a mathematician."},
            ]
        }
    }))
    wiki_tool = TOOL_FUNCTIONS["wikipedia"]
    result = wiki_tool(query="Alan Turing", limit=1)

    assert calls[0]["url"] == "https://en.wikipedia.org/w/api.php"
    assert calls[0]["params"]["srsearch"] == "Alan Turing"
    assert calls[0]["params"]["srlimit"] == 1
    assert result["item_count"] == 1
    assert result["items"][0]["title"] == "Alan Turing"
    assert result["items"][0]["summary"] == "Alan Mathison Turing was a mathematician."
    assert "12345" in result["items"][0]["url"]


def test_my_new_tool_bad_input_from_model() -> None:
    wiki_tool = TOOL_FUNCTIONS["wikipedia"]
    result = wiki_tool(query="   ")
    assert result["error"] == "ValueError"
    assert result["items"] == []


def test_my_new_tool_failure_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse({}, status_code=500))
    wiki_tool = TOOL_FUNCTIONS["wikipedia"]
    result = wiki_tool(query="Python")
    assert "error" in result


# ---------------- CHALLENGE+: REGRESSION TESTS ----------------

def test_regression_format_without_url_has_no_trailing_dash() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    result = format_tool(items=[{"summary": "Tin tuc quan trong", "url": ""}], template="bullets")
    assert result["markdown"] == "- Tin tuc quan trong"
    assert not result["markdown"].endswith(" - ")


def test_regression_timeline_limit_zero_returns_empty(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-key")
    fake_http(FakeResponse({"timeline": [{"tweet_id": "1", "text": "Hello", "screen_name": "elonmusk"}]}))
    timeline_tool = TOOL_FUNCTIONS["timeline"]
    result = timeline_tool(screenname="elonmusk", limit=0)
    assert len(result["items"]) == 0
