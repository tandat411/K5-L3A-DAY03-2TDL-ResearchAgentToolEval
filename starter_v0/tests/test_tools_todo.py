"""TODO(student): Tool Unit Test Challenge.

All stub tests implemented. Offline only: mock HTTP with fake_http.
Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    res = TOOL_FUNCTIONS["clarify"](question="Lựa chọn phương án?", response_type="choice", options=["A", "B"])
    assert res["options"] == ["A", "B"]
    assert res["awaiting_user"] is True
    assert res["response_type"] == "choice"


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "Tin 1", "url": "https://example.com/1", "summary": "Tóm tắt 1", "section": "Tech"},
        {"title": "Tin 2", "url": "https://example.com/2", "summary": "Tóm tắt 2", "section": "Business"},
        {"title": "Tin 3", "url": "https://example.com/3", "summary": "Tóm tắt 3", "section": "Tech"},
    ]
    res = TOOL_FUNCTIONS["format"](items=items, template="sections")
    markdown = res["markdown"]
    assert "## Tech" in markdown
    assert "## Business" in markdown
    assert markdown.count("## Tech") == 1
    assert markdown.count("## Business") == 1


def test_format_thread_numbers_items() -> None:
    items = [
        {"title": "Tin 1", "url": "https://example.com/1", "summary": "Tóm tắt 1"},
        {"title": "Tin 2", "url": "https://example.com/2", "summary": "Tóm tắt 2"},
    ]
    res = TOOL_FUNCTIONS["format"](items=items, template="thread")
    lines = [l.strip() for l in res["markdown"].splitlines() if l.strip()]
    assert any(l.startswith("1/") for l in lines)
    assert any(l.startswith("2/") for l in lines)


def test_format_empty_items_does_not_crash() -> None:
    res_none = TOOL_FUNCTIONS["format"](items=None, template="bullets")
    res_empty = TOOL_FUNCTIONS["format"](items=[], template="bullets")
    assert res_none["item_count"] == 0
    assert res_empty["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123456789")
    calls = fake_http(FakeResponse({"ok": True, "result": {"message_id": 99}}))

    res = TOOL_FUNCTIONS["send"](text="Bản tin công nghệ", confirmed=True)
    assert res["status"] == "sent"
    assert len(calls) == 1
    assert "123456:fake-token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-100123456789"
    assert calls[0]["json"]["text"] == "Bản tin công nghệ"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    res = TOOL_FUNCTIONS["send"](text="Bản tin", confirmed=True)
    assert res["error"] == "RuntimeError"
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    TOOL_FUNCTIONS["lookup"](query="AI news", timeframe=None)
    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")
    fake_http(FakeResponse({
        "data": {
            "markdown": "# Tiêu đề bài viết\nNội dung bài viết",
            "metadata": {"title": "Tiêu đề", "sourceURL": "https://example.com/article"}
        }
    }))

    res = TOOL_FUNCTIONS["fetch"](url="https://example.com/article")
    assert len(res["items"]) == 1
    item = res["items"][0]
    assert item["title"] == "Tiêu đề"
    assert item["url"] == "https://example.com/article"
    assert item["source"] == "example.com"
    assert "Nội dung bài viết" in item["summary"]


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")
    long_markdown = "A" * 5000
    fake_http(FakeResponse({
        "data": {
            "markdown": long_markdown,
            "metadata": {"title": "Long Article", "sourceURL": "https://example.com/long"}
        }
    }))

    res = TOOL_FUNCTIONS["fetch"](url="https://example.com/long")
    summary = res["items"][0]["summary"]
    assert len(summary) <= 4005


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapid-key")
    raw_tweets = [
        {"tweet_id": "111", "text": "Tweet 1", "screen_name": "elonmusk"},
        {"text": "Tweet no id"},
        {"tweet_id": "222", "text": "Tweet 2", "screen_name": "elonmusk"},
        {"tweet_id": "333", "text": "Tweet 3", "screen_name": "elonmusk"},
        {"tweet_id": "444", "text": "Tweet 4", "screen_name": "elonmusk"},
    ]
    fake_http(FakeResponse({"timeline": raw_tweets}))

    res = TOOL_FUNCTIONS["timeline"](screenname="elonmusk", limit=2)
    assert len(res["items"]) == 2
    assert res["items"][0]["url"] == "https://x.com/elonmusk/status/111"
    assert res["items"][1]["url"] == "https://x.com/elonmusk/status/222"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapid-key")
    calls = fake_http(FakeResponse({"results": []}))

    TOOL_FUNCTIONS["social_search"](query="OpenAI", search_type="Top", limit=3)
    assert len(calls) == 1
    assert calls[0]["params"]["query"] == "OpenAI"
    assert calls[0]["params"]["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    res = TOOL_FUNCTIONS["policy"](query="")
    assert res["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    res = TOOL_FUNCTIONS["policy"](query="privacy", policy_area="data_privacy")
    for r in res["results"]:
        assert r.get("policy_area") == "data_privacy"


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    res = TOOL_FUNCTIONS["policy"](query="citation", policy_area="source_citation")
    assert isinstance(res.get("results"), list)


# ---------------- YOUR NEW TOOL(S) (cbm_calculator) ----------------

def test_my_new_tool_happy_path() -> None:
    res = TOOL_FUNCTIONS["cbm_calculator"](length_cm=50, width_cm=40, height_cm=30, weight_kg=5, quantity=2)
    assert res["status"] == "success"
    assert res["total_cbm"] == 0.12
    assert res["quantity"] == 2
    assert res["actual_weight_kg"] == 10.0
    assert res["volumetric_weight_kg"] == 24.0
    assert res["chargeable_weight_kg"] == 24.0
    assert "0.1200 CBM" in res["summary"]


def test_my_new_tool_bad_input_from_model() -> None:
    # Model sends numbers as string representations
    res = TOOL_FUNCTIONS["cbm_calculator"](length_cm="60", width_cm="40", height_cm="20", weight_kg="10", quantity="1")
    assert res["status"] == "success"
    assert res["total_cbm"] == 0.048

    # Negative dimension
    res_neg = TOOL_FUNCTIONS["cbm_calculator"](length_cm=-10, width_cm=20, height_cm=30)
    assert res_neg["status"] == "error"
    assert "lớn hơn 0" in res_neg["message"]


def test_my_new_tool_failure_returns_error_dict() -> None:
    # Invalid non-numeric input
    res = TOOL_FUNCTIONS["cbm_calculator"](length_cm="invalid_abc", width_cm=20, height_cm=30)
    assert isinstance(res, dict)
    assert res["status"] == "error"
    assert "hợp lệ" in res["message"]
