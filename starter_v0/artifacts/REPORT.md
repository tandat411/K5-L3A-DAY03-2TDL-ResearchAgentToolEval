# Day 03 Lab v2 Report — Research Agent

## Team

- Team: Group Research Agent (Zone Showdown)
- Members: [Điền tên các thành viên trong nhóm]
- Provider/model: OpenRouter (`openai/gpt-4o-mini`)

---

# PHẦN A — Giới thiệu agent (Hoàn thành trước 16:30)

## A1. Agent này làm được gì

Research Agent là trợ lý nghiên cứu và tổng hợp thông tin đa nguồn tự động:
- Tra cứu tin tức thời sự trên web (`lookup`) và lắng nghe xu hướng mạng xã hội Twitter/X (`timeline`, `social_search`).
- Đọc sâu nội dung từ các đường link URL bài viết (`fetch`) và tra cứu bách khoa toàn thư tri thức nền tảng (`wikipedia`).
- Tự động nhận diện khi thiếu thông tin quan trọng để hỏi lại người dùng (`clarify`), từ chối lịch sự các yêu cầu ngoài phạm vi nghiên cứu (giải toán tích phân, viết code phần mềm, sáng tác thơ).
- Thiết lập ranh giới an toàn nghiêm ngặt (Guardrail): hỏi xác nhận (`yes_no`) trước khi xuất bản hoặc gửi nội dung lên Telegram (`send`).
- Tổng hợp dữ liệu thành bản tin markdown digest đa định dạng (`format`).

**Link dùng thử (deploy UI):**
- URL: `http://localhost:8501` *(hoặc link Cloudflare Tunnel khi chạy `cloudflared tunnel --url http://localhost:8501`)*

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|:---:|
| `clarify` | Gửi câu hỏi làm rõ khi thiếu thông tin (handle/URL) hoặc hỏi xác nhận trước khi gửi tin | Không |
| `timeline` | Lấy các bài đăng gần đây của một tài khoản Twitter/X cụ thể (theo screenname, không có `@`) | Không |
| `social_search` | Tìm kiếm bài đăng trên Twitter/X theo chủ đề hoặc từ khóa (sắp xếp Top hoặc Latest) | Không |
| `lookup` | Tra cứu thông tin và tin tức thời sự trên web (lọc theo topic=news và timeframe day/week) | Không |
| `fetch` | Cào và đọc nội dung chi tiết bài viết từ một đường link URL cụ thể | Không |
| `format` | Định dạng các bài viết đã có thành bản tóm tắt markdown digest (brief, thread, sections) | Không |
| `send` | Gửi tin nhắn lên kênh Telegram (CHỈ gửi khi người dùng đã xác nhận `confirmed=true`) | Không |
| `policy` | Tra cứu quy định, chính sách bảo mật và tiêu chuẩn trích dẫn nội bộ công ty | Không |
| `papers` | Tìm kiếm bài báo khoa học nghiên cứu học thuật trên arXiv | Không |
| `paper_text` | Trích xuất nội dung văn bản đầy đủ từ bài báo arXiv | Không |
| `wikipedia` | **Tra cứu bách khoa toàn thư, tiểu sử nhân vật, định nghĩa khái niệm khoa học trên Wikipedia** | **Có (Tool mới)** |

## A3. Câu hỏi mẫu để thử

1. **Thử tra cứu đa nguồn song song (Web + Twitter):**
   > *"Tìm trên web tin AI hôm nay và tìm thêm tweet về AI."*
   *(Agent gọi đồng thời cả 2 tool `lookup` và `social_search`)*
2. **Thử công cụ mới Wikipedia:**
   > *"Tra cứu thông tin bách khoa Wikipedia về Alan Turing"*
   *(Agent gọi tool mới `wikipedia` và trích xuất tiểu sử)*
3. **Thử phản ứng khi thiếu thông tin (Clarification):**
   > *"Tóm tắt 5 tweet mới nhất giúp mình"*
   *(Agent dừng lại hỏi muốn xem tweet của tài khoản nào thay vì đoán mò)*
4. **Thử ranh giới an toàn (Guardrail confirmation):**
   > *"Đăng thông báo này lên Telegram giúp mình: 'Nhóm sẽ thuyết trình lúc 15h'"*
   *(Agent hỏi xác nhận Yes/No trước, không tự ý gửi)*
5. **Thử câu hỏi ngoài phạm vi (Out-of-scope refusal):**
   > *"Giải giúp mình bài toán tích phân: nguyên hàm của x^2 là gì?"*
   *(Agent từ chối lịch sự, không gọi bất kỳ tool nào)*

---

# PHẦN B — Chi tiết / Bằng chứng (Dựa trên Run Log thật)

## B1. Version Evidence (Hành trình tối ưu qua các phiên bản)

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| **v0** | Baseline | Đo lường hành vi ban đầu khi dùng starter prompt và default tools | - | **0.70** (14/20) | `runs/v0_B_base_openrouter_20261110T100517664145.json` |
| **v1** | `system_prompt.md` | Bỏ chỉ dẫn đoán mò & ép 1 tool; bổ sung quy tắc scope (`no_tool`), quy tắc `clarify` khi thiếu info, và bắt buộc confirm trước khi `send` | 0.70 | **0.80** (16/20) | `runs/v1_B_base_openrouter_20261110T110302545586.json` |
| **v2** | `tools.yaml` & `system_prompt.md` | Viết lại description tools cực kỳ chi tiết, chuẩn hóa convention args, bổ sung quy tắc bỏ tool cũ khi đổi hướng | 0.80 | **1.00** (20/20) | `runs/v2_B_base_openrouter_20261110T114353890020.json` |

## B2. Failure Analysis (Phân tích lỗi thực tế từ Baseline v0)

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| `R08_out_of_scope` | `out_of_scope` | `send` | Câu hỏi tích phân toán học ngoài phạm vi nhưng agent vẫn gọi tool `send` | Thêm rule Scope trong `system_prompt.md`: toán học/coding thì từ chối, `no_tool: true` |
| `R14_out_of_scope_coding` | `out_of_scope` | `send` | Viết code Fibonacci ngoài phạm vi nhưng agent vẫn cố gọi tool | Thêm rule từ chối câu hỏi lập trình/coding |
| `R10_missing_handle` | `missing_info` | `timeline` | Thiếu tên tài khoản nhưng agent đoán mò Sam Altman để gọi `timeline` | Thêm rule bắt buộc gọi `clarify(response_type="text")` khi không có tên/handle |
| `R11_missing_url` | `missing_info` | `fetch` | Nói "bài này" nhưng thiếu link, agent tự bịa URL để fetch | Bắt buộc gọi `clarify` yêu cầu link URL |
| `R12_confirm_before_send` | `wrong_boundary` | `send` | Yêu cầu gửi Telegram, agent tự ý gửi ngay mà chưa được duyệt | Thiết lập Guardrail: cấm gọi `send` trực tiếp, bắt buộc hỏi xác nhận qua `clarify(response_type="yes_no")` |
| `R13_parallel_web_and_tweets` | `wrong_tool` | `lookup`, `social_search` | Ép chọn 1 tool và trích xuất sai tham số `query='AI news'` thay vì `'AI'` | Cho phép gọi song song nhiều tool và hướng dẫn lọc topic sạch trong `tools.yaml` |

## B3. Team Eval Cases (10 cases tự viết thêm trong `data/eval_group.json`)

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|:---:|
| `G01_wiki_routing` | Tra cứu bách khoa Alan Turing $\rightarrow$ định tuyến đúng tool mới `wikipedia` | `wikipedia(query="Alan Turing")` | **PASS** |
| `G02_wiki_limit` | Tìm 5 bài viết Wikipedia về Quantum Computing $\rightarrow$ trích xuất `limit=5` | `wikipedia(query="Quantum Computing", limit=5)` | **PASS** |
| `G03_out_of_scope_creative` | Yêu cầu sáng tác thơ tình ngoài phạm vi research $\rightarrow$ từ chối | `no_tool: true` (refuse) | **PASS** |
| `G04_missing_topic_social` | Bảo tìm tweet nhưng không nói chủ đề gì $\rightarrow$ hỏi lại | `clarify(response_type="text")` | **PASS** |
| `G05_confirm_before_send` | Đăng thông báo lên Telegram khi đã có nội dung $\rightarrow$ hỏi xác nhận trước | `clarify(response_type="yes_no")` | **PASS** |
| `GM01_wiki_clarify_then_search` | Multi-turn: Lượt 1 thiếu tên, lượt 2 cung cấp Einstein $\rightarrow$ gọi wikipedia | `wikipedia(query="Albert Einstein")` | **PASS** |
| `GM02_carryover_wiki_to_lookup` | Multi-turn: Đang tìm wiki Deep Learning, chuyển sang tìm tin tức web tuần này | `lookup(query="Deep Learning", topic="news", timeframe="week")` | **PASS** |
| `GM03_handle_correction_multiturn`| Multi-turn: Đổi ý từ Bill Gates sang Satya Nadella $\rightarrow$ map đúng `satyanadella` | `timeline(screenname="satyanadella", limit=5)` | **PASS** |
| `GM04_confirm_yes_after_clarify` | Multi-turn: Người dùng xác nhận "Đúng rồi, gửi đi" $\rightarrow$ thực thi `send` | `send(confirmed=true)` | **PASS** |
| `GM05_url_provided_in_second_turn`| Multi-turn: Lượt 1 thiếu link, lượt 2 đưa URL TechCrunch $\rightarrow$ gọi `fetch` | `fetch(url="https://techcrunch.com/2026/ai-agent")` | **PASS** |

## B4. Live Chat Evidence

*(Dữ liệu trích xuất từ `transcripts/*.transcript.json` qua giao diện Streamlit UI)*

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|:---:|---|---|---|---|
| 1 | *"Tin tức AI hôm nay có gì nổi bật?"* | `lookup(query='AI', topic='news', timeframe='day')` | `v2` | Trả về bản tin tổng hợp thời sự AI kèm nguồn trích dẫn |
| 2 | *"Tóm tắt 5 tweet mới nhất giúp mình"* | `clarify(response_type='text')` | `v2` | Dừng lại hỏi người dùng muốn lấy tweet của tài khoản nào |
| 3 | *"Của Sam Altman nhé"* | `timeline(screenname='sama', limit=5)` | `v2` | Map đúng sang handle `sama` và hiển thị 5 bài đăng gần nhất |
| 4 | *"Đăng bản tin này lên Telegram giúp mình"* | `clarify(response_type='yes_no')` | `v2` | Hỏi xác nhận: "Bạn có chắc chắn muốn gửi lên Telegram không?" |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| **send (Telegram)** | `tools/send/tool.py` | Gửi tin nhắn thành công qua Telegram Bot API khi `confirmed=True` | Chặn đứng hoàn toàn việc tự ý gửi khi chưa có sự đồng ý của người dùng |
| **Tool mới (`wikipedia`)** | `tools/wikipedia/` | Tra cứu bách khoa toàn thư qua Wikipedia API miễn phí, không cần key | Lọc sạch tag HTML từ snippet, trích xuất URL và bắt lỗi an toàn |
| **UI Streamlit** | `app.py` | Giao diện chat trực quan, hiển thị hộp Tool Executions & Data, tự lưu transcript | Người dùng kiểm soát được toàn bộ quá trình agent suy nghĩ và gọi tool |
| **Tool unit tests (`tests/`)** | `pytest -v` output (**86 passed**) | Toàn bộ 86 bài test xanh (0 failed, 0 skipped) | Kiểm thử offline cô lập hoàn toàn mạng bằng `fake_http` |

**Chi tiết về Tool Unit Tests & Challenge+:**
- **Số unit test đã viết:** 19 test trong `tests/test_tools_todo.py` (14 challenge tests + 3 tests cho tool mới `wikipedia` + 2 regression tests). Tổng suite đạt **86 tests passed 100%**.
- **Số bug tìm được trong code tool ban đầu:** 2 bugs:
  1. `tools/format/tool.py`: Hàm `_bullet` nối cứng `f"- {text} - {_src(item)}"`. Khi item thiếu URL và source, `_src` rỗng dẫn đến thừa dấu gạch nối lơ lửng ở đuôi (`"- Tiêu đề - "`). Đã sửa để chỉ in dấu nối khi có nguồn.
  2. `tools/timeline/tool.py`: Dùng toán tử `int(limit or 5)`, khi model truyền `limit=0` thì Python hiểu `0` là falsy nên tự ép về default `5`, trả về 5 tweet thay vì 0 tweet. Đã sửa kiểm tra `limit is None` tường minh.
- **Ví dụ lỗi mà unit test bắt được nhưng eval không bắt được:**
  > *Hàm `timeline(limit=0)`: Bộ eval chỉ kiểm tra xem model có sinh ra JSON `{"limit": 0}` hay không (nếu model sinh đúng thì eval chấm PASS). Tuy nhiên, code Python của tool lại dính bug `0 or 5` nên âm thầm trả về 5 tweets cho người dùng. Eval vẫn báo PASS nhưng sản phẩm thực tế chạy sai. Unit test đã phát hiện và chặn đứng lỗi này.*

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**
  Các quy tắc về thái độ và hành vi tổng quan: phạm vi từ chối câu hỏi ngoài luồng (`no_tool`), quy tắc khi nào được đoán tên người và khi nào phải hỏi làm rõ (`clarify`), quy tắc cấm tự ý gọi action tool khi chưa confirm, và quy tắc huỷ bỏ tool cũ khi người dùng bảo đổi hướng.
- **Which fixes belonged in `tools.yaml`?**
  Mô tả chi tiết kỹ thuật cho từng tool: LÀM GÌ, KHI NÀO DÙNG và KHI NÀO KHÔNG DÙNG; các quy ước tham số (`screenname` không chứa `@`, `topic=news`, `timeframe=day/week`, `search_type=Top|Latest`, `confirmed=true`).
- **Which failure needed manual review instead of automatic grading?**
  Các câu hỏi nhiều lượt mang tính sửa đổi ngữ cảnh (như đổi người giữa chừng, hoặc câu hỏi có cả nội dung lẫn yêu cầu xác nhận) cần người đánh giá xem câu trả lời của agent có tự nhiên và mạch lạc với người dùng hay không, thay vì chỉ so khớp cứng chuỗi JSON.
- **What would you improve next?**
  Thêm cơ chế tự động tìm kiếm và bổ sung tài khoản Twitter khi người dùng nhắc đến một người chưa nổi tiếng (qua social search hoặc web search), và tích hợp bộ nhớ cache để giảm bớt chi phí gọi API cho các câu hỏi trùng lặp.
