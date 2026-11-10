# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: 2TDL
- Members: Nguyễn Thùy Lam - 2A202603632.
- Provider/model: OpenRouter - `openai/gpt-4o-mini`.

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent hỗ trợ tra cứu web, tìm bài đăng theo chủ đề hoặc tài khoản, đọc URL, tìm paper và chính sách nội bộ, rồi định dạng kết quả thành digest. Có thể gửi nội dung lên Telegram sau khi người dùng xác nhận.

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: Chưa có link public. Chạy local bằng Streamlit tại `http://localhost:8501`.

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | hỏi người dùng khi thiếu thông tin hoặc xin xác nhận | không |
| `timeline` | lấy bài đăng gần đây của một tài khoản | không |
| `social_search` | tìm bài đăng theo chủ đề | không |
| `lookup` | tìm thông tin trên web | không |
| `fetch` | đọc nội dung từ URL | không |
| `format` | định dạng các item đã thu thập thành digest | không |
| `send` | gửi nội dung lên Telegram sau xác nhận | không |
| `policy` | tìm trong tài liệu chính sách nội bộ | không |
| `papers` | tìm bài báo trên arXiv | không |
| `paper_text` | trích văn bản từ bài báo arXiv | không |
| `dedupe_sources` | loại kết quả có URL trùng, giữ mục đầu tiên | có |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. “Tin AI hôm nay có gì nổi bật?”
2. “Tweet mới nhất của Sam Altman là gì?”
3. “Tóm tắt bài viết này: [dán URL]”
4. “Tìm tin AI hôm nay trên web và tìm thêm tweet về AI.”
5. “Loại URL trùng trong danh sách nguồn sau: [dán danh sách item]”

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Baseline reference; identify routing, argument, missing-info, and boundary failures. | n/a (baseline) | case 0.65; route 0.75; args 0.65; multi-turn 1.00 | `runs/v0_B_base_openrouter_20261110T103139208591.json` |
| v1 | `artifacts/system_prompt.md` | Clarify missing accounts/URLs instead of guessing; test whether R10/R11 routing improves. | case 0.65 | case 0.85; route 0.95; args 0.85; multi-turn 1.00 | `runs/v1_B_base_openrouter_20261110T111827486807.json` |
| v2 | `artifacts/system_prompt.md` | Clarify only ambiguous identities while preserving known public-account mappings and URL safety. | case 0.75 | case 0.90; route 0.95; args 0.90; multi-turn 1.00 | `runs/v2_B_base_openrouter_20261110T124503159038.json` |
| v3 | `artifacts/system_prompt.md`; `artifacts/tools.yaml`; `tools/__init__.py`; `data/eval_group.json` | Thêm quy tắc rõ cho xác nhận gửi và `lookup(topic=news, timeframe=...)`; đăng ký `dedupe_sources`. Kỳ vọng cải thiện hai lỗi còn lại của v2. | case 0.90; route 0.95; args 0.90; multi-turn 1.00 | case 0.90 (18/20); route 0.95; args 0.90; multi-turn 0.8333 | `runs/v3_B_base_openrouter_20261110T144154242486.json` |
## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| `R03_web_news_routing` (v0) | `wrong_arg_value` | `lookup(query="AI news")` | Query gộp chữ “news”; thiếu `topic="news"`. PASS ở v3. | Quy tắc tách chủ đề khỏi `query`, đặt `topic=news`. |
| `R08_out_of_scope` (v0) | `out_of_scope` | `send(...)` | Gọi tool gửi cho yêu cầu toán ngoài phạm vi. PASS ở v3. | Thêm quy tắc không gọi tool cho yêu cầu ngoài phạm vi. |
| `R10_missing_handle` (v0) | `missing_info` | `timeline(screenname="sama")` | Đoán tài khoản khi user chưa nêu người nào. PASS ở v3. | Hỏi lại khi thiếu tài khoản; chỉ dùng mapping đã biết khi user nêu tên. |
| `R11_missing_url` (v0) | `missing_info` | `fetch(url="https://example.com")` | Tự tạo URL. PASS ở v3. | Không bịa URL; hỏi user cung cấp link. |
| `R12_confirm_before_send` (v3) | `wrong_boundary` | `clarify(response_type="text")` | Đã hỏi lại nhưng xin nội dung bản tin, chưa hỏi xác nhận bằng `yes_no` như eval yêu cầu. | Hỏi xác nhận `yes_no` trước; nếu thiếu nội dung, cần làm rõ thứ tự lấy nội dung và xin duyệt. |
| `R13_parallel_web_and_tweets` (v0) | `wrong_arg_value` | `lookup(query="AI news")`; `social_search(query="AI")` | Thiếu `topic=news` và query web không gọn. PASS ở v3. | Quy tắc news/current events và giữ query là chủ đề. |
| `R14_out_of_scope_coding` (v0) | `out_of_scope` | `send(...)` | Gọi tool gửi cho yêu cầu viết code ngoài phạm vi. PASS ở v3. | Thêm quy tắc không gọi tool cho yêu cầu ngoài phạm vi. |
| `M06_switch_tool` (v3) | `wrong_tool` | `lookup(query="OpenAI", topic="news")` và `social_search(query="OpenAI")` | Sau khi user yêu cầu bỏ Twitter, agent vẫn gọi `social_search` thêm. Đây là một trong hai FAIL của v3. | Ưu tiên chỉ dẫn mới nhất trong hội thoại; khi user đổi nguồn, không tiếp tục gọi tool nguồn cũ. |

## B3. Team Eval Cases

Hiện `data/eval_group.json` có một case mới; chưa đủ 10 case theo checklist README. Chưa thấy file run cho suite `group`, nên kết quả bên dưới đang chờ chạy.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| `G01_dedupe_duplicate_source_urls` | Gọi tool khử trùng khi có URL lặp và truyền danh sách item | `dedupe_sources(items=[...])` | Chưa chạy group eval |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | “Hãy tóm tắt giúp tôi bài viết này” | Không gọi tool; hỏi URL | v0, `v0_openrouter_20261110T142033369170.transcript.json` | Hỏi bổ sung URL thay vì tự tạo link. |
| 2 | “Thôi hãy cho tôi biết thời tiết hôm nay” | Không gọi tool; hỏi vị trí | v0, cùng transcript | Hỏi vị trí trước khi tra cứu. |
| 3 | “Hà Nội” | `lookup` | v0, cùng transcript | Trả lời với nguồn web; transcript có nội dung tool call. |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `tools/send/tool.py`; `app.py` | Có luồng xác nhận trong UI và khai báo tool; v3 vẫn FAIL case xác nhận theo contract eval. Chưa có bằng chứng gửi thật. | Không gửi trước xác nhận rõ ràng; cần sửa cách hỏi xác nhận trong R12. |
| arXiv/company policy | `tools/papers/`, `tools/paper_text/`, `tools/policy/` | Các tool có implementation trong project; chưa có run riêng được ghi nhận ở lượt làm này. | Chưa có bằng chứng kiểm thử/live riêng trong report. |
| UI | `app.py` | Có giao diện Streamlit chat, transcript và chọn file run để xem metric/case FAIL. | Chỉ ghi nhận chạy local; chưa có link public. |
| Tool unit tests (`tests/`) | Chưa có output mới | Chưa thêm 3 unit test bắt buộc cho `dedupe_sources`; chưa ghi nhận pytest sau thay đổi. | Chưa xác minh happy path, input sai và nhánh lỗi bằng unit test. |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Các quy tắc điều hướng, không bịa URL, xử lý ngoài phạm vi, xác nhận gửi và chuyển nguồn theo chỉ dẫn mới nhất thuộc `system_prompt.md`.
- Quy ước `topic=news`, timeframe và điều kiện gọi `send`/`dedupe_sources` cần thể hiện rõ trong `tools.yaml` để model thấy ngay tại tool call.
- `M06_switch_tool` là lỗi hội thoại nhiều lượt: cần xem ngữ cảnh và thứ tự gọi tool; metric tự động chỉ báo tool thừa, còn nguyên nhân là agent không bỏ nguồn Twitter sau yêu cầu đổi nguồn.
- Tiếp theo: sửa R12 để dùng `yes_no`, sửa M06 để dừng gọi tool nguồn cũ, thêm unit test cho `dedupe_sources`, bổ sung đủ eval case nhóm rồi chạy suite `group`.

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
