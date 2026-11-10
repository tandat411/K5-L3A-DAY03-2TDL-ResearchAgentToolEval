from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    execute_tool_call,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from providers.base import ToolCall
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"
RUNS_DIR = ROOT / "runs"

PROVIDERS = ("openrouter", "openai", "anthropic", "gemini", "ollama")
PROVIDER_KEYS = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

st.set_page_config(
    page_title="Research Agent | Day 03 Lab",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(
    """
    <style>
    :root {
      color-scheme: dark;
      --page: #0b1020;
      --surface: #111a2c;
      --surface-raised: #172238;
      --stroke: rgba(183, 198, 225, .14);
      --muted: #9aabc6;
      --text: #edf3ff;
      --accent: #8b9cff;
      --mint: #73e0c1;
    }
    .stApp {
      background:
        radial-gradient(ellipse at 80% -8%, rgba(83, 104, 210, .20), transparent 36%),
        radial-gradient(ellipse at 8% 18%, rgba(31, 175, 164, .09), transparent 30%),
        var(--page);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    [data-testid="stHeader"] { background: rgba(11, 16, 32, .72); }
    [data-testid="stSidebar"] {
      background: rgba(12, 19, 34, .96);
      border-right: 1px solid var(--stroke);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.25rem; }
    .block-container { max-width: 1480px; padding-top: 2.2rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: var(--text); letter-spacing: -.035em; }
    h1 { font-size: clamp(2rem, 3.6vw, 3.15rem) !important; line-height: 1.04 !important; }
    p, li, label, [data-testid="stCaptionContainer"] { color: #c1cde0; }
    [data-testid="stChatMessage"] {
      background: rgba(17, 26, 44, .86);
      border: 1px solid var(--stroke);
      border-radius: 22px;
      padding: .55rem 1rem;
      margin-bottom: .8rem;
      box-shadow: 0 12px 34px rgba(0, 0, 0, .12);
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
      background: rgba(32, 47, 72, .72);
    }
    [data-testid="stChatInput"] textarea,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
      background: #101a2d;
      border-color: rgba(183, 198, 225, .20);
      border-radius: 13px;
      color: var(--text);
    }
    [data-testid="stChatInput"] textarea:focus,
    [data-testid="stTextInput"] input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(139, 156, 255, .20);
    }
    .stButton > button, [data-testid="stDownloadButton"] button {
      min-height: 44px;
      border-radius: 13px;
      border: 1px solid rgba(183, 198, 225, .20);
      background: #172238;
      color: var(--text);
      transition: all .18s ease-in-out;
    }
    .stButton > button:hover, [data-testid="stDownloadButton"] button:hover {
      border-color: rgba(139, 156, 255, .72);
      color: white;
      transform: translateY(-1px);
    }
    [data-testid="stMetric"] {
      background: rgba(17, 26, 44, .78);
      border: 1px solid var(--stroke);
      border-radius: 17px;
      padding: .9rem 1rem;
    }
    [data-testid="stMetricValue"] { color: var(--text); }
    [data-testid="stExpander"] {
      border: 1px solid var(--stroke);
      border-radius: 15px;
      background: rgba(17, 26, 44, .42);
    }
    .eyebrow {
      color: var(--mint); text-transform: uppercase; letter-spacing: .14em;
      font-size: .74rem; font-weight: 700; margin-bottom: .6rem;
    }
    .hero-copy { color: var(--muted); font-size: 1.02rem; margin-top: -.7rem; }
    .brand-mark {
      display: inline-flex; width: 38px; height: 38px; align-items: center; justify-content: center;
      border-radius: 13px; margin-right: .6rem; color: #fff;
      background: linear-gradient(135deg, #6578f2, #3ab9a7);
      box-shadow: 0 8px 24px rgba(81, 111, 233, .25);
    }
    .brand-line { display: flex; align-items: center; font-size: 1rem; font-weight: 750; color: var(--text); }
    .pill {
      display: inline-block; padding: .3rem .62rem; margin: .2rem .22rem .2rem 0;
      border-radius: 999px; border: 1px solid var(--stroke); background: rgba(23, 34, 56, .78);
      color: #d6e0f3; font-size: .76rem; line-height: 1.35;
    }
    .panel-note { color: var(--muted); font-size: .87rem; line-height: 1.55; }
    .safe-note {
      padding: .8rem .9rem; border: 1px solid rgba(115, 224, 193, .25);
      border-radius: 14px; background: rgba(40, 132, 116, .10); color: #c8f4e7;
      font-size: .88rem; line-height: 1.5;
    }
    @media (max-width: 760px) {
      .block-container { padding: 1.2rem 1rem 2rem; }
      [data-testid="stChatMessage"] { border-radius: 17px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_state() -> None:
    defaults: dict[str, Any] = {
        "messages": [],
        "history": [],
        "transcript": None,
        "transcript_path": None,
        "active_config": None,
        "pending_send": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_conversation() -> None:
    st.session_state.messages = []
    st.session_state.history = []
    st.session_state.transcript = None
    st.session_state.transcript_path = None
    st.session_state.active_config = None
    st.session_state.pending_send = None


def selected_config() -> dict[str, Any]:
    return {
        "provider": st.session_state.provider_choice,
        "model": st.session_state.model_override.strip() or None,
        "version": st.session_state.version_label.strip() or "v0",
        "history_window": st.session_state.history_window,
        "max_tool_rounds": st.session_state.max_tool_rounds,
    }


def create_transcript(config: dict[str, Any]) -> dict[str, Any]:
    provider = make_provider(config["provider"])
    selected_model = config["model"] or getattr(provider, "default_model", None)
    artifact_version = build_artifact_version(config["version"], PROMPT_PATH, TOOLS_PATH)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join((safe_slug(config["version"]), safe_slug(config["provider"]), timestamp))
    return {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": config["provider"],
        "model": selected_model,
        "system_prompt": "artifacts/system_prompt.md",
        "tools": "artifacts/tools.yaml",
        "history_window": config["history_window"],
        "max_tool_rounds": config["max_tool_rounds"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def redact_error(error: Exception) -> str:
    message = f"{type(error).__name__}: {error}"
    for env_name in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "TAVILY_API_KEY", "FIRECRAWL_API_KEY", "RAPIDAPI_KEY", "TELEGRAM_BOT_TOKEN"):
        secret = os.getenv(env_name)
        if secret:
            message = message.replace(secret, "[REDACTED]")
    return message


def persist_transcript() -> None:
    transcript = st.session_state.transcript
    path = st.session_state.transcript_path
    if transcript and path:
        write_transcript(Path(path), transcript)


def handle_user_message(user_text: str) -> None:
    config = st.session_state.active_config
    if config is None:
        config = selected_config()
        st.session_state.active_config = config

    if st.session_state.transcript is None:
        transcript = create_transcript(config)
        transcript_path = TRANSCRIPTS_DIR / f"{transcript['transcript_id']}.transcript.json"
        st.session_state.transcript = transcript
        st.session_state.transcript_path = str(transcript_path)

    turn: dict[str, Any] = {
        "turn_index": len(st.session_state.transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    st.session_state.messages.append({"role": "user", "content": user_text})

    try:
        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        declarations = load_tool_declarations(TOOLS_PATH)
        openai_tools = to_openai_tools(declarations)
        provider = make_provider(config["provider"])
        messages = [
            {"role": "system", "content": system_prompt},
            *trim_history(st.session_state.history, config["history_window"]),
            {"role": "user", "content": user_text},
        ]

        def ui_tool_executor(call: ToolCall) -> dict[str, Any]:
            if call.name == "send":
                # A model-generated confirmed=true is not user approval. Hold the
                # message until the user explicitly presses the confirmation button.
                st.session_state.pending_send = {
                    "text": str(call.args.get("text", "")),
                    "requested_at": now_iso(),
                }
                return {
                    "tool": "send",
                    "args": {**call.args, "confirmed": False},
                    "result": {
                        "status": "awaiting_confirmation",
                        "awaiting_user": True,
                        "question": "Mình đã chuẩn bị nội dung. Hãy xem và xác nhận trước khi gửi lên Telegram.",
                    },
                }
            return execute_tool_call(call)

        with st.spinner("Agent đang phân tích và gọi công cụ phù hợp…"):
            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=config["model"],
                max_tool_rounds=config["max_tool_rounds"],
                tool_executor=ui_tool_executor,
            )
        turn.update(result)
        assistant_text = result.get("assistant_text") or "Mình chưa nhận được nội dung trả lời từ provider."
        st.session_state.history.extend(
            ({"role": "user", "content": user_text}, {"role": "assistant", "content": assistant_text})
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_text,
            "tool_events": result.get("tool_events", []),
            "status": result.get("status", "answered"),
        })
    except Exception as exc:
        safe_error = redact_error(exc)
        turn.update({
            "status": "provider_error",
            "error": safe_error,
            "assistant_text": "Không thể hoàn tất yêu cầu. Kiểm tra cấu hình provider rồi thử lại.",
        })
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Không thể hoàn tất yêu cầu. Mở phần chi tiết bên dưới để xem lỗi đã được lọc thông tin nhạy cảm.",
            "error": safe_error,
            "status": "provider_error",
        })

    turn["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn)
    persist_transcript()


def tool_pills(tool_names: list[str]) -> str:
    return "".join(f'<span class="pill">{name}</span>' for name in tool_names)


def render_message(message: dict[str, Any]) -> None:
    role = message["role"]
    avatar = "🧭" if role == "assistant" else "🙂"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message.get("content", ""))
        if message.get("status") == "provider_error" and message.get("error"):
            with st.expander("Chi tiết lỗi đã lọc thông tin nhạy cảm"):
                st.code(message["error"], language="text")
        events = message.get("tool_events") or []
        if events:
            with st.expander(f"Chi tiết {len(events)} lượt gọi tool", expanded=False):
                for index, event in enumerate(events, start=1):
                    st.markdown(f"**{index}. {event.get('tool', 'tool')}**")
                    st.json(event, expanded=False)


def record_send_event(event: dict[str, Any], display_text: str) -> None:
    transcript = st.session_state.transcript
    if transcript and transcript.get("turns"):
        last_turn = transcript["turns"][-1]
        last_turn.setdefault("tool_events", []).append(event)
        if last_turn.get("rounds"):
            last_turn["rounds"][-1].setdefault("tool_results", []).append(event)
        last_turn["send_confirmation"] = {
            "confirmed_by_user": event.get("result", {}).get("status") == "sent",
            "resolved_at": now_iso(),
        }
    st.session_state.messages.append({
        "role": "assistant",
        "content": display_text,
        "tool_events": [event],
    })
    persist_transcript()


def render_send_confirmation() -> None:
    pending = st.session_state.pending_send
    if not pending:
        return
    st.markdown("### Cần bạn xác nhận")
    st.caption("Nội dung chưa được gửi. Kiểm tra chính xác nội dung bên dưới.")
    st.code(pending["text"] or "(nội dung trống)", language="text")
    left, right = st.columns(2)
    if left.button("Xác nhận và gửi Telegram", type="primary", use_container_width=True, key="confirm_telegram_send"):
        event = execute_tool_call(ToolCall(name="send", args={"text": pending["text"], "confirmed": True}))
        result = event.get("result", {})
        if isinstance(result, dict) and result.get("status") == "sent":
            record_send_event(event, "Đã gửi nội dung lên Telegram.")
            st.session_state.pending_send = None
        else:
            record_send_event(event, "Không gửi được nội dung lên Telegram. Xem chi tiết tool call để biết lý do.")
            st.session_state.pending_send = None
        st.rerun()
    if right.button("Huỷ gửi", use_container_width=True, key="cancel_telegram_send"):
        event = {
            "tool": "send",
            "args": {"text": pending["text"], "confirmed": False},
            "result": {"status": "cancelled_by_user"},
        }
        record_send_event(event, "Đã huỷ gửi; nội dung không được chuyển tới Telegram.")
        st.session_state.pending_send = None
        st.rerun()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="brand-line"><span class="brand-mark">⌕</span>Research Agent</div>', unsafe_allow_html=True)
        st.caption("DAY 03 · TOOL EVAL LAB")
        st.divider()

        st.selectbox("Provider", PROVIDERS, index=0, key="provider_choice")
        st.text_input("Model override (tuỳ chọn)", placeholder="Để trống dùng model mặc định", key="model_override")
        st.text_input("Version", value="v0", key="version_label")
        st.slider("Số lượt hội thoại giữ lại", min_value=1, max_value=10, value=5, key="history_window")
        st.slider("Số vòng gọi tool tối đa", min_value=1, max_value=8, value=4, key="max_tool_rounds")

        config_now = selected_config()
        active_config = st.session_state.active_config
        if active_config is None:
            key_name = PROVIDER_KEYS.get(config_now["provider"])
            ready = True if config_now["provider"] == "ollama" else bool(key_name and os.getenv(key_name))
            label = "Local endpoint" if config_now["provider"] == "ollama" else ("Key đã cấu hình" if ready else f"Thiếu {key_name}")
            st.markdown(f'<div class="safe-note">● {label}</div>', unsafe_allow_html=True)
        elif config_now != active_config:
            st.info("Cấu hình mới áp dụng cho cuộc trò chuyện mới.")

        st.markdown("")
        if st.button("＋  Cuộc trò chuyện mới", use_container_width=True, key="new_conversation"):
            reset_conversation()
            st.rerun()

        st.divider()
        st.markdown("**Câu hỏi gợi ý**")
        st.markdown(
            '<div class="panel-note">• Tin AI mới nhất hôm nay có gì?<br>• Tóm tắt bài viết tại [URL].<br>• Tìm 5 bài mới nhất của [tên tài khoản].<br>• So sánh nguồn web và bài đăng mạng xã hội về [chủ đề].</div>',
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown("**Kết quả đánh giá**")
        run_files = sorted(RUNS_DIR.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        if run_files:
            run_names = [path.name for path in run_files]
            st.selectbox("Chọn file run", run_names, key="selected_run_file")
        else:
            st.caption("Chưa có file run trong thư mục runs.")


def render_selected_run() -> None:
    selected_name = st.session_state.get("selected_run_file")
    if not selected_name:
        return
    run_path = RUNS_DIR / selected_name
    try:
        run_data = json.loads(run_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        st.error(f"Không đọc được file run: {exc}")
        return

    summary = run_data.get("summary", {})
    st.markdown("#### File run được chọn")
    st.caption(selected_name)
    st.markdown(
        f"**Version** `{run_data.get('version', '—')}` · "
        f"**Provider** `{run_data.get('provider', '—')}` · "
        f"**Model** `{run_data.get('model', '—')}`"
    )
    metric_cols = st.columns(4)
    metric_cols[0].metric("Case accuracy", f"{summary.get('case_accuracy', 0):.0%}")
    metric_cols[1].metric("Tool routing", f"{summary.get('tool_routing_accuracy', 0):.0%}")
    metric_cols[2].metric("Argument accuracy", f"{summary.get('argument_accuracy', 0):.0%}")
    metric_cols[3].metric("Passed cases", f"{summary.get('passed_cases', 0)}/{summary.get('total_cases', 0)}")

    failures = []
    for case in run_data.get("results", []):
        result = case.get("result", {})
        if not result.get("passed", True):
            failures.append({
                "Case": case.get("id", "—"),
                "Loại lỗi": result.get("failure_type") or result.get("case_failure_type") or "—",
                "Sai lệch": result.get("observed_mismatch") or "—",
                "Input": case.get("input", "—"),
            })
    with st.expander(f"Case FAIL ({len(failures)})", expanded=bool(failures)):
        if failures:
            st.dataframe(failures, use_container_width=True, hide_index=True)
        else:
            st.success("Không có case FAIL trong run này.")


def main() -> None:
    initialize_state()
    render_sidebar()

    current_config = selected_config()
    if st.session_state.active_config is None:
        st.session_state.active_config = current_config
    elif current_config != st.session_state.active_config and st.session_state.messages:
        st.sidebar.info("Cấu hình đang chạy được giữ cố định cho cuộc trò chuyện này.")

    chat_disabled = st.session_state.pending_send is not None
    prompt = st.chat_input(
        "Hỏi về tin tức, bài đăng, URL hoặc nghiên cứu…",
        disabled=chat_disabled,
        max_chars=4000,
        key="research_chat_input",
    )
    if prompt and prompt.strip():
        handle_user_message(prompt.strip())

    st.markdown('<div class="eyebrow">Evidence-first research</div>', unsafe_allow_html=True)
    st.title("Tìm. Đọc. Tổng hợp.")
    st.markdown(
        '<p class="hero-copy">Một research agent dùng tool thật, giữ dấu vết từng lượt gọi và lưu transcript để bạn kiểm chứng.</p>',
        unsafe_allow_html=True,
    )

    chat_column, overview_column = st.columns([1.7, 1], gap="large")
    with chat_column:
        if not st.session_state.messages:
            with st.container(border=True):
                st.markdown("#### Bắt đầu một phiên nghiên cứu")
                st.markdown("Nhập yêu cầu ở ô chat bên dưới. Khi thiếu tài khoản hoặc URL, agent có thể hỏi lại.")
                declarations = load_tool_declarations(TOOLS_PATH)
                names = [item["name"] for item in declarations]
                st.markdown(tool_pills(names), unsafe_allow_html=True)
        else:
            for message in st.session_state.messages:
                render_message(message)

        render_send_confirmation()

    with overview_column:
        render_selected_run()
        transcript = st.session_state.transcript
        turns = transcript.get("turns", []) if transcript else []
        total_tool_calls = sum(len(turn.get("tool_events", [])) for turn in turns)
        metric_turns, metric_tools = st.columns(2)
        metric_turns.metric("Lượt chat", len(turns))
        metric_tools.metric("Tool events", total_tool_calls)

        with st.container(border=True):
            st.markdown("#### Phiên hiện tại")
            cfg = st.session_state.active_config or current_config
            st.markdown(f"**Provider** · `{cfg['provider']}`")
            if transcript:
                st.markdown(f"**Model** · `{transcript.get('model') or 'provider default'}`")
                st.markdown(f"**Artifact** · `{transcript.get('artifact_version')}`")
                st.caption(f"Transcript: `{Path(st.session_state.transcript_path).name}`")
            else:
                st.markdown("**Model** · mặc định của provider")
                st.caption("Transcript sẽ được tạo sau tin nhắn đầu tiên.")

        with st.expander("Tool của agent", expanded=False):
            declarations = load_tool_declarations(TOOLS_PATH)
            for item in declarations:
                st.markdown(f"**{item['name']}** · {item.get('description', '')}")

        if turns:
            latest_events = turns[-1].get("tool_events", [])
            with st.expander("Hoạt động gần nhất", expanded=True):
                if latest_events:
                    for event in latest_events:
                        st.markdown(f"`{event.get('tool', 'tool')}`")
                else:
                    st.caption("Lượt gần nhất không gọi tool.")

        if transcript:
            payload = json.dumps(transcript, ensure_ascii=False, indent=2, default=str)
            st.download_button(
                "Tải transcript JSON",
                data=payload,
                file_name=Path(st.session_state.transcript_path).name,
                mime="application/json",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
