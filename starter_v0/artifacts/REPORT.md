# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: 2TDL
- Members: Nguyễn Trần Tú Trân (2A202603603)
- Provider/model: gemini / gemini-2.5-flash

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent đa năng chuyên sâu: tự động tra cứu tin tức web, tìm kiếm bài đăng Twitter/X, đọc sâu URL bài viết, tổng hợp báo cáo digest, tính toán thể tích/cước vận tải hàng hóa (CBM), tra cứu bài báo arXiv/chính sách và gửi tin Telegram an toàn qua guardrail xác nhận (Human-in-the-loop).

**Link dùng thử (deploy):**

> URL: https://drill-advisors-recognition-logan.trycloudflare.com

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin hoặc xin xác nhận trước hành động quan trọng | không |
| timeline | Lấy các bài đăng gần nhất trên X (Twitter) của tài khoản được chỉ định | không |
| social_search | Tìm kiếm bài đăng trên X (Twitter) theo từ khóa hoặc hashtag | không |
| lookup | Tìm kiếm tin tức và tài liệu trên web (hỗ trợ phân loại topic=news/general) | không |
| fetch | Đọc nội dung bài viết chi tiết từ đường link URL cụ thể | không |
| format | Định dạng nội dung thô thành Markdown digest tóm tắt chuyên nghiệp kèm nguồn | không |
| send | Gửi thông điệp/báo cáo lên Telegram channel (chỉ gửi khi có confirmed=true) | không |
| policy | Tra cứu quy định nội bộ và chính sách trích dẫn/chia sẻ thông tin công ty | không |
| papers | Tìm kiếm danh sách bài báo khoa học trên hệ thống arXiv | không |
| paper_text | Tải và trích xuất nội dung toàn văn bài báo khoa học theo arXiv ID | không |
| cbm_calculator | Tính mét khối (CBM), khối lượng thể tích và khối lượng tính cước vận chuyển | có |

## A3. Câu hỏi mẫu để thử

1. "Tính giúp mình thể tích kiện hàng kích thước 60x40x30 cm nặng 8kg số lượng 3 thùng."
2. "Tìm tin tức mới nhất về chip bán dẫn hôm nay và tóm tắt thành bản tin digest."
3. "Xem các bài đăng gần đây của @sama trên Twitter và tổng hợp các chủ đề nổi bật."
4. "Gửi báo cáo tin tức thị trường vừa tìm được lên kênh Telegram giúp tôi." *(Agent sẽ kích hoạt guardrail hỏi xác nhận an toàn trước khi gửi)*
5. "Tra cứu chính sách công ty về việc chia sẻ thông tin nghiên cứu ra bên ngoài." 

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi mặc định chưa tối ưu của starter prompt và tools | - | 0.7143 | runs/v0_B_base_gemini_20261110T102803355977.json |
| v1 | system_prompt.md | Bắt buộc clarify khi thiếu thông tin và xin xác nhận trước khi gửi sẽ chặn lỗi missing_info và wrong_boundary | 0.7143 | 0.8889 | runs/v1_B_base_gemini_20261110T112719079235.json |
| v2 | system_prompt.md | Ép schema response_type cho clarify và carryover multi-turn giúp chuẩn hóa tham số | 0.8889 | 1.0000 | runs/v2_B_base_gemini_20261110T120116693181.json |
| v3 | tools.yaml | Mô tả rõ ràng khi nào dùng/cấm dùng và convention args trong tools.yaml giúp ổn định 100% multiturn và đạt 0 provider error | 1.0000 | 0.8500 | runs/v3_B_base_gemini_20261110T120828064244.json |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R10_missing_handle | missing_info | timeline(screenname='sama') | Không gọi clarify hỏi tên tài khoản, tự ý đoán Sama | Xóa chỉ dẫn đoán bừa trong prompt, thêm rule bắt buộc clarify |
| R11_missing_url | missing_info | fetch(...) | Không gọi clarify hỏi link bài viết, tự bịa URL | Bổ sung rule clarify khi thiếu URL |
| R12_confirm_before_send | wrong_boundary | send(...) | Tự ý gửi tin lên Telegram khi chưa có xác nhận | Thêm guardrail bắt buộc clarify xin xác nhận (confirmed=true) trước khi gửi |
| R03_web_news_routing | wrong_tool | lookup(query='AI artificial intelligence news') | Tự chèn thêm từ thừa vào query thay vì giữ nguyên 'AI' | Thêm rule giữ nguyên từ khóa gốc |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_cbm_calculator_routing | Route vào custom tool cbm_calculator và trích đúng 5 tham số | cbm_calculator(length=50, width=40, height=30, weight=5, quantity=2) | PASS |
| G02_cbm_calculator_default_args | Tính CBM với tham số mặc định (không có weight và quantity) | cbm_calculator(length=60, width=40, height=25) | PASS |
| G03_social_search_latest | Tìm bài đăng mới nhất trên Twitter | social_search(search_type='Latest') | PASS |
| G04_out_of_scope_cooking | Câu hỏi nấu ăn ngoài phạm vi research tin tức/vận tải | no_tool: true (từ chối lịch sự) | PASS |
| G05_clarify_missing_shipping_dimensions | Hỏi tính CBM nhưng thiếu kích thước | clarify(response_type='text') | FAIL |
| GM01_clarify_then_cbm | Multi-turn: clarify hỏi kích thước rồi tính CBM với 4 kiện | cbm_calculator(length=80, width=50, height=40, quantity=4) | PASS |
| GM02_correct_dimensions | Multi-turn: sửa chiều cao từ 20 thành 40 cm | cbm_calculator(length=50, width=30, height=40) | PASS |
| GM03_research_then_cbm | Multi-turn: chuyển đổi ngữ cảnh từ tin tức sang tính thể tích kiện mẫu | cbm_calculator(length=45, width=35, height=25, weight=3) | PASS |
| GM04_confirm_send_shipping_quote | Multi-turn: xin xác nhận trước khi gửi và chỉ gửi khi user đồng ý | send(confirmed=true) | PASS |
| GM05_switch_from_cbm_to_web | Multi-turn: chuyển từ tính toán CBM sang tra cứu quy định đóng gói trên web | lookup(topic='general') | PASS |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tính giúp mình thể tích kiện hàng kích thước 60x40x30 cm nặng 8kg số lượng 3 thùng | cbm_calculator | v3 (custom tool cbm_calculator) | Tính chuẩn xác 0.216 CBM, thực tế 24kg, thể tích 43.2kg, tính cước 43.2kg |
| 2 | Tin tức mới nhất về xuất khẩu hàng thủ công mỹ nghệ hôm nay | lookup -> format | v3 (routing lookup + format) | Tổng hợp bản tin Markdown digest kèm link nguồn bài viết báo chí |
| 3 | Gửi kết quả này lên Telegram channel giúp mình | clarify(response_type='yes_no') | v3 (guardrail send confirmation) | Dừng lại xin xác nhận 'Bạn có chắc chắn muốn gửi...', không tự ý gửi tin |

File transcript bằng chứng: transcripts/v3_gemini_20261110T121356890306.transcript.json

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `artifacts/tools.yaml`, `artifacts/system_prompt.md`, `tests/test_tools_todo.py` | Guardrail xác nhận: Chặn gửi trực tiếp, chỉ cho phép gửi khi user xác nhận (confirmed=True). | Tránh spam, phát tán nhầm tin tức chưa duyệt ra kênh thông tin công khai. |
| arXiv/company policy | `tools/policy/tool.py`, `tools/papers/tool.py`, `tools/paper_text/tool.py` | Tra cứu chuẩn xác chính sách bảo mật nội bộ và bài báo khoa học arXiv. | Luôn tra cứu chính sách bản quyền trước khi trích xuất dữ liệu nhạy cảm. |
| UI | `starter_v0/app.py` | Giao diện Web Streamlit + Cloudflare Tunnel live, hỗ trợ 11 tools, prompt buttons và tool inspection box. | Chạy sandbox headless bảo mật, tương tác real-time. |
| Tool unit tests (`tests/`) | `tests/test_tools_todo.py` | Đạt 100% PASS (84/84 passed, 0 failed, 0 skipped), bao gồm 3 unit tests cho cbm_calculator. | Bắt sớm lỗi schema mismatch và format validation trước khi eval. |

Tool unit tests: Đã viết 84 test cases. Phát hiện bug trong mock của timeline (thiếu trường screen_name dẫn đến không sinh được URL status hoàn chỉnh). Unit test bắt được lỗi này ngay trong khi eval thường chỉ kiểm tra tool name mà bỏ qua URL logic.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
  + Xóa toàn bộ anti-pattern xấu của starter (như tự ý đoán username, bịa link URL, tự tiện gửi tin).
  + Định nghĩa quy tắc routing nhiều bước: khi nào gọi clarify, khi nào tìm kiếm lookup vs social_search, khi nào format digest và khi nào kích hoạt send.
  + Ép chuẩn hóa schema response_type cho clarify và hướng dẫn duy trì ngữ cảnh multi-turn carryover.

- Which fixes belonged in `tools.yaml`?
  + Viết lại chi tiết mô tả của từng tool: phân định ranh giới rõ ràng khi nào nên dùng và khi nào cấm dùng.
  + Chuẩn hóa conventions đối số: screen_name không chứa ký tự @, topic='news' cho tin tức báo chí, confirmed=true là bắt buộc với send.
  + Khai báo schema đầy đủ cho custom tool cbm_calculator.

- Which failure needed manual review instead of automatic grading?
  + Case `G05_clarify_missing_shipping_dimensions`: Khi user yêu cầu tính CBM nhưng thiếu số đo, model trả lời văn bản yêu cầu người dùng nhập kích thước thay vì gọi tool clarify(). Trải nghiệm thực tế hoàn toàn tốt nhưng auto-eval regex đánh fail.
  + Các câu hỏi từ chối ngoài phạm vi (out-of-scope) như nấu ăn cần con người kiểm tra giọng điệu lịch sự, hòa nhã.

- What would you improve next?
  + Tích hợp streaming response và visual progress bar hiển thị từng tool execution trên UI Streamlit.
  + Bổ sung caching tầng kết quả (SQLite/Redis) cho lookup và papers để tối ưu chi phí token và tốc độ phản hồi.
  + Mở rộng cbm_calculator hỗ trợ nhiều đơn vị đo (inch, feet, lbs) và tra cứu biểu phí logistics quốc tế. 

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
