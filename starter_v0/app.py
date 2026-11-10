import os
import sys
from pathlib import Path

# Add current directory to path
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from datetime import datetime
import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop, write_transcript, safe_slug, now_iso

load_lab_env(ROOT)
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="Research Agent - AI Assistant",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 Research Agent UI")
st.caption("Interactive Research Agent with Evidence-Driven Tool Execution & Live Logging")

# Sidebar configurations
with st.sidebar:
    st.header("⚙️ Cấu hình Agent")
    provider_name = st.selectbox(
        "Provider",
        options=["openrouter", "openai", "anthropic", "gemini", "ollama"],
        index=0,
    )
    
    version_tag = st.text_input("Artifact Version", value="v0")
    
    default_models = {
        "openrouter": "openai/gpt-4o-mini",
        "openai": "gpt-4o-mini",
        "gemini": "gemini-2.0-flash",
        "anthropic": "claude-3-5-sonnet-20241022",
        "ollama": "qwen2.5:7b",
    }
    model_name = st.text_input("Model (để trống nếu dùng mặc định)", value=default_models.get(provider_name, ""))
    model_name = model_name.strip() or None

    st.divider()
    st.subheader("🛠️ Tools khả dụng")
    tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    for t in tool_declarations:
        with st.expander(f"🔹 `{t['name']}`"):
            st.write(t.get("description", ""))
            st.json(t.get("parameters", {}), expanded=False)

    st.divider()
    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.transcript = {
            "session_id": f"chat_{safe_slug(version_tag)}_{datetime.now().strftime('%Y%m%dT%H%M%S')}",
            "started_at": now_iso(),
            "version": version_tag,
            "provider": provider_name,
            "model": model_name,
            "turns": [],
        }
        st.rerun()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "transcript" not in st.session_state:
    st.session_state.transcript = {
        "session_id": f"chat_{safe_slug(version_tag)}_{datetime.now().strftime('%Y%m%dT%H%M%S')}",
        "started_at": now_iso(),
        "version": version_tag,
        "provider": provider_name,
        "model": model_name,
        "turns": [],
    }

# Display existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "tool_events" in msg and msg["tool_events"]:
            with st.expander("🔧 Tool Executions & Data", expanded=False):
                for ev in msg["tool_events"]:
                    st.markdown(f"**Tool:** `{ev.get('tool')}`")
                    st.markdown(f"**Args:** `{json.dumps(ev.get('args', {}), ensure_ascii=False)}`")
                    st.json(ev.get("result", {}), expanded=False)
        st.markdown(msg["content"])

# User input
user_query = st.chat_input("Nhập câu hỏi hoặc yêu cầu nghiên cứu...")

if user_query:
    # Append and display user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Prepare provider & prompt
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    openai_tools = to_openai_tools(tool_declarations)
    
    try:
        provider = make_provider(provider_name)
    except Exception as e:
        st.error(f"Lỗi khởi tạo provider `{provider_name}`: {e}")
        st.stop()

    # Build context messages (trim history to last 5 turns)
    history_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]
    # Keep last 10 messages (5 pairs)
    trimmed_history = history_messages[-10:]
    working_messages = [{"role": "system", "content": system_prompt}, *trimmed_history]

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("Agent đang suy nghĩ và thực thi tools..."):
            loop_result = run_model_tool_loop(
                provider=provider,
                messages=working_messages,
                tools=openai_tools,
                model=model_name,
                max_tool_rounds=5,
            )

        tool_events = loop_result.get("tool_events", [])
        if tool_events:
            with st.expander("🔧 Tool Executions & Data", expanded=True):
                for ev in tool_events:
                    st.markdown(f"**Tool:** `{ev.get('tool')}`")
                    st.markdown(f"**Args:** `{json.dumps(ev.get('args', {}), ensure_ascii=False)}`")
                    st.json(ev.get("result", {}), expanded=False)

        final_text = loop_result.get("assistant_text", "")
        st.markdown(final_text)

        # Append to UI history
        st.session_state.messages.append({
            "role": "assistant",
            "content": final_text,
            "tool_events": tool_events,
        })

        # Append to transcript and save
        st.session_state.transcript["turns"].append({
            "turn": len(st.session_state.transcript["turns"]) + 1,
            "user": user_query,
            "assistant": final_text,
            "tool_events": tool_events,
            "status": loop_result.get("status"),
        })
        transcript_path = TRANSCRIPTS_DIR / f"{st.session_state.transcript['session_id']}.transcript.json"
        write_transcript(transcript_path, st.session_state.transcript)
        st.caption(f"💾 Transcript đã ghi: `{transcript_path.name}`")
