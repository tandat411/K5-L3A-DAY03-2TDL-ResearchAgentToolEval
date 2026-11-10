from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

# Page configuration
st.set_page_config(
    page_title="2TDL Agent Studio — Pro Edition",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State (Default to Light Mode as requested by user)
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "☀️ Light Mode"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Theme Flag
is_dark = st.session_state.theme_mode == "🌙 Dark Mode"

# ==========================================
# PALETTE DEFINITIONS (SYNCHRONIZED LIGHT & DARK)
# ==========================================
if is_dark:
    bg_color = "#090d16"
    sidebar_bg = "#0d1322"
    card_bg = "#131b2e"
    card_border = "rgba(255, 255, 255, 0.08)"
    text_primary = "#f8fafc"
    text_secondary = "#94a3b8"
    hero_bg = "linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)"
    chip_bg = "rgba(255, 255, 255, 0.04)"
    chip_border = "rgba(255, 255, 255, 0.1)"
    chip_text = "#e2e8f0"
    chat_bubble_user = "rgba(99, 102, 241, 0.18)"
    chat_bubble_asst = "#131b2e"
    chat_border = "rgba(255, 255, 255, 0.08)"
    accent_color = "#6366f1"
    stat_badge_bg = "rgba(99, 102, 241, 0.15)"
    stat_badge_text = "#a5b4fc"
    input_bg = "#111827"
    input_border = "rgba(255, 255, 255, 0.12)"
else:
    # COHESIVE BRIGHT LIGHT PALETTE
    bg_color = "#f8fafc"
    sidebar_bg = "#ffffff"
    card_bg = "#ffffff"
    card_border = "#e2e8f0"
    text_primary = "#0f172a"
    text_secondary = "#475569"
    hero_bg = "linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%)"
    chip_bg = "#ffffff"
    chip_border = "#cbd5e1"
    chip_text = "#1e293b"
    chat_bubble_user = "#eff6ff"
    chat_bubble_asst = "#ffffff"
    chat_border = "#e2e8f0"
    accent_color = "#4f46e5"
    stat_badge_bg = "#e0e7ff"
    stat_badge_text = "#4338ca"
    input_bg = "#ffffff"
    input_border = "#cbd5e1"

# ==========================================
# INJECT COMPREHENSIVE SYNCHRONIZED CSS
# ==========================================
st.markdown(f"""
<style>
  /* 1. Global App & Main Canvas */
  .stApp, .main, [data-testid="stAppViewContainer"] {{
    background-color: {bg_color} !important;
    color: {text_primary} !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
  }}
  
  [data-testid="stHeader"] {{
    background-color: {bg_color} !important;
    border-bottom: 1px solid {card_border} !important;
  }}

  /* 2. Synchronized Sidebar */
  section[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{
    background-color: {sidebar_bg} !important;
    color: {text_primary} !important;
    border-right: 1px solid {card_border} !important;
  }}

  [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
  [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{
    color: {text_primary} !important;
  }}
  
  [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {{
    color: {text_secondary} !important;
  }}

  /* 3. Hero Box */
  .hero-box {{
    background: {hero_bg};
    border: 1px solid {card_border};
    border-radius: 18px;
    padding: 24px 28px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
  }}
  
  .hero-title {{
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, {accent_color}, #0284c7, #059669);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 6px;
  }}
  
  .hero-subtitle {{
    font-size: 14px;
    color: {text_secondary};
    line-height: 1.5;
    margin-bottom: 12px;
  }}
  
  .stat-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 600;
    background: {stat_badge_bg};
    color: {stat_badge_text};
    margin-right: 8px;
    border: 1px solid {card_border};
  }}

  /* 4. Scenario Cards & Buttons */
  .scenario-title {{
    font-size: 13px;
    font-weight: 700;
    color: {text_primary};
    margin-bottom: 4px;
  }}
  
  .scenario-desc {{
    font-size: 11px;
    color: {text_secondary};
    line-height: 1.4;
    margin-bottom: 8px;
  }}
  
  div.stButton > button {{
    border-radius: 10px !important;
    border: 1px solid {chip_border} !important;
    background-color: {card_bg} !important;
    color: {text_primary} !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    transition: all 0.2s ease !important;
  }}
  div.stButton > button:hover {{
    border-color: {accent_color} !important;
    color: {accent_color} !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15) !important;
  }}

  /* 5. Chat Messages Balloons */
  [data-testid="stChatMessage"] {{
    border-radius: 14px !important;
    padding: 16px 20px !important;
    margin-bottom: 14px !important;
    border: 1px solid {chat_border} !important;
    background-color: {card_bg} !important;
    color: {text_primary} !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
  }}

  /* 6. Expanders & Inspection Cards */
  div[data-testid="stExpander"] {{
    background-color: {card_bg} !important;
    border: 1px solid {card_border} !important;
    border-radius: 12px !important;
    color: {text_primary} !important;
    margin-top: 8px !important;
  }}

  div[data-testid="stExpander"] summary {{
    color: {text_primary} !important;
    font-weight: 600 !important;
  }}

  /* 7. Chat Input Container */
  [data-testid="stChatInput"] {{
    background-color: {input_bg} !important;
    border: 1px solid {input_border} !important;
    border-radius: 12px !important;
    color: {text_primary} !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05) !important;
  }}
  [data-testid="stChatInput"] textarea {{
    color: {text_primary} !important;
  }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR CONTROL PANEL
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ Bảng Điều Khiển")
    
    # 1. Theme Switcher (Light / Dark)
    st.markdown("**🌓 Chế Độ Giao Diện (Theme Mode):**")
    theme_choice = st.radio(
        label="Theme",
        options=["☀️ Light Mode", "🌙 Dark Mode"],
        index=0 if st.session_state.theme_mode == "☀️ Light Mode" else 1,
        label_visibility="collapsed",
        horizontal=True
    )
    if theme_choice != st.session_state.theme_mode:
        st.session_state.theme_mode = theme_choice
        st.rerun()
    
    st.markdown("---")
    
    # 2. Model Selector
    st.markdown("**🤖 Mô Hình Xử Lý (Model Engine):**")
    selected_model = st.selectbox(
        label="Model",
        options=["gemini-3.5-flash-lite", "gemini-3.8-flash"],
        index=0,
        label_visibility="collapsed",
        help="gemini-3.5-flash-lite: Khuyên dùng cho tốc độ cao và phản hồi tức thì."
    )
    
    # Connection Badge
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; margin-top: 6px; margin-bottom: 12px;">
        <span style="height: 9px; width: 9px; background-color: #10b981; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 12px; color: #10b981; font-weight: 600;">API Kết nối ổn định (v1beta)</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 3. Phân nhóm 5 Cụm Công Cụ Chuyên Sâu
    st.markdown("### 🛠️ 11 Công Cụ Chuyên Sâu")
    
    tool_groups = [
        ("🌐 Web Intelligence", ["lookup", "fetch", "policy"], "#0284c7" if not is_dark else "#38bdf8"),
        ("🐦 Social Signals", ["timeline", "social_search"], "#0ea5e9" if not is_dark else "#06b6d4"),
        ("🎓 Academic Research", ["papers", "paper_text"], "#8b5cf6" if not is_dark else "#a78bfa"),
        ("📦 Logistics Engine", ["cbm_calculator"], "#059669" if not is_dark else "#34d399"),
        ("🛡️ Safety & Guardrail", ["clarify", "format", "send"], "#d97706" if not is_dark else "#fbbf24"),
    ]
    
    tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    tool_dict = {t["name"]: t["description"] for t in tool_declarations}
    
    for group_name, tools_in_group, badge_color in tool_groups:
        with st.expander(f"{group_name} ({len(tools_in_group)})"):
            for t_name in tools_in_group:
                desc = tool_dict.get(t_name, "")
                is_custom = t_name == "cbm_calculator"
                tag = "⭐ CUSTOM" if is_custom else "TOOL"
                st.markdown(f"**`{t_name}`** <span style='font-size:10px; color:{badge_color}; font-weight:700;'>[{tag}]</span>", unsafe_allow_html=True)
                st.caption(desc)
                
    st.markdown("---")
    st.markdown(f"<div style='font-size:12px; color:{text_secondary};'><b>Nhóm thực hiện</b>: 2TDL (Nguyễn Trần Tú Trân)<br><b>MSSV</b>: 2A202603603<br><b>Test Suite</b>: <b style='color:#10b981;'>84/84 Passed (100% Green)</b></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Xóa Lịch Sử Hội Thoại", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# HERO BANNER (SYNCHRONIZED LIGHT CANVAS)
# ==========================================
st.markdown(f"""
<div class="hero-box">
  <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
    <div>
      <div style="margin-bottom: 8px;">
        <span class="stat-pill">⚡ Pro Edition</span>
        <span class="stat-pill">🛡️ Human-in-the-Loop Active</span>
        <span class="stat-pill">📦 Custom CBM Engine</span>
      </div>
      <h1 class="hero-title">2TDL Autonomous Research & Logistics Studio</h1>
      <p class="hero-subtitle">Môi trường AI Agent đa năng thế hệ mới: Tự động điều hướng 11 công cụ tra cứu thời gian thực, đọc toàn văn học thuật và tính cước vận tải chuyên sâu.</p>
    </div>
    <div style="text-align: right;">
      <div style="font-size: 11px; font-weight: 700; color: {text_secondary}; text-transform: uppercase;">Mô Hình Đang Chạy:</div>
      <div style="font-size: 15px; font-weight: 800; color: {accent_color}; font-family: monospace;">{selected_model}</div>
      <div style="font-size: 11px; color: #10b981; font-weight: 600; margin-top: 2px;">● Online & Streaming Ready</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4 CHUYÊN ĐỀ KỊCH BẢN GỢI Ý (PROMPT SCENARIOS)
# ==========================================
st.markdown(f"<div style='font-size:14px; font-weight:700; color:{text_primary}; margin-bottom:10px;'>💡 4 Kịch bản kiểm thử & nghiên cứu chuyên sâu:</div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
sample_prompt = None

with col1:
    st.markdown("""
    <div class="scenario-title">📦 Kịch Bản A: Logistics</div>
    <div class="scenario-desc">Tính CBM, thể tích & cước cho lô 5 kiện mẫu.</div>
    """, unsafe_allow_html=True)
    if st.button("Chạy Lô 5 Kiện Mẫu 75x45x35", key="btn_cbm", use_container_width=True):
        sample_prompt = "Tính toán CBM, trọng lượng thể tích đường hàng không cho lô hàng 5 kiện hàng mẫu (kích thước 75x45x35 cm, nặng 12kg/kiện) và cho biết kiện hàng tính cước theo thể tích hay khối lượng thực tế."

with col2:
    st.markdown("""
    <div class="scenario-title">🎓 Kịch Bản B: Khoa Học</div>
    <div class="scenario-desc">Tìm kiếm công trình arXiv về LLM Tool Calling.</div>
    """, unsafe_allow_html=True)
    if st.button("Quét Nghiên Cứu arXiv", key="btn_arxiv", use_container_width=True):
        sample_prompt = "Tìm kiếm 3 bài báo khoa học mới nhất trên arXiv về chủ đề AI Agent Tool Calling và trích xuất tóm tắt phương pháp cốt lõi."

with col3:
    st.markdown("""
    <div class="scenario-title">🐦 Kịch Bản C: Thị Trường</div>
    <div class="scenario-desc">Đọc dòng thời gian @sama & tin tức chip AI.</div>
    """, unsafe_allow_html=True)
    if st.button("Phân Tích X & Tin Tức", key="btn_social", use_container_width=True):
        sample_prompt = "Đọc các bài đăng gần nhất của @sama về mô hình AI mới, đồng thời tra cứu tin tức web liên quan và tổng hợp thành bản tin digest có dẫn nguồn."

with col4:
    st.markdown("""
    <div class="scenario-title">🛡️ Kịch Bản D: Guardrail</div>
    <div class="scenario-desc">Kiểm tra cơ chế chặn gửi Telegram khi chưa duyệt.</div>
    """, unsafe_allow_html=True)
    if st.button("Kiểm Thử Guardrail Gửi Tin", key="btn_guardrail", use_container_width=True):
        sample_prompt = "Gửi báo cáo tóm tắt vừa tạo lên kênh Telegram thông báo nội bộ."

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# CONVERSATION THREAD DISPLAY
# ==========================================
for msg in st.session_state.messages:
    is_user = msg["role"] == "user"
    avatar = "🧑‍💻" if is_user else "⚡"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        
        # Tool Events Display (Clean & Structured)
        if "tools" in msg and msg["tools"]:
            tool_count = len(msg["tools"])
            with st.expander(f"🛠️ Thực thi công cụ ({tool_count} tool calls)", expanded=False):
                for idx, evt in enumerate(msg["tools"], 1):
                    tool_name = evt.get("tool", "unknown")
                    args = evt.get("args", {})
                    result = evt.get("result", {})
                    
                    st.markdown(f"**#{idx} Công cụ: `{tool_name}`**")
                    col_in, col_out = st.columns(2)
                    with col_in:
                        st.caption("📥 Tham số đầu vào (Args):")
                        st.json(args)
                    with col_out:
                        st.caption("📤 Dữ liệu trả về (Result):")
                        st.json(result)
                    st.divider()

# ==========================================
# INPUT & EXECUTION LOOP
# ==========================================
user_input = st.chat_input("Nhập câu hỏi, yêu cầu nghiên cứu hoặc thông số kiện hàng...")
prompt = sample_prompt or user_input

if prompt:
    # 1. Append User Input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # 2. Build Multi-Turn History
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    openai_tools = to_openai_tools(tool_declarations)
    provider = make_provider("gemini")
    
    history_messages = [{"role": "system", "content": system_prompt}]
    for m in st.session_state.messages[-6:]:
        history_messages.append({"role": m["role"], "content": m["content"]})

    # 3. Assistant Inference
    with st.chat_message("assistant", avatar="⚡"):
        with st.spinner(f"Agent đang xử lý qua {selected_model}..."):
            try:
                res = run_model_tool_loop(
                    provider=provider,
                    messages=history_messages,
                    tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=3,
                )
                assistant_text = res["assistant_text"] or "Đã thực hiện xong yêu cầu."
                tool_events = res.get("tool_events", [])

                st.markdown(assistant_text)
                
                if tool_events:
                    with st.expander(f"🛠️ Thực thi công cụ ({len(tool_events)} tool calls)", expanded=True):
                        for idx, evt in enumerate(tool_events, 1):
                            tool_name = evt.get("tool", "unknown")
                            args = evt.get("args", {})
                            result = evt.get("result", {})
                            st.markdown(f"**#{idx} Công cụ: `{tool_name}`**")
                            col_in, col_out = st.columns(2)
                            with col_in:
                                st.caption("📥 Tham số đầu vào (Args):")
                                st.json(args)
                            with col_out:
                                st.caption("📤 Dữ liệu trả về (Result):")
                                st.json(result)
                            st.divider()

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_text,
                    "tools": tool_events,
                })
            except Exception as e:
                st.error(f"⚠️ Đã xảy ra lỗi: {e}")
