# Lab Solution — Multi-Agent System với A2A Protocol

| | |
|---|---|
| **Fullname** | Võ Thanh Hiệp |
| **ID** | 2A202600836 |
| **Project** | VinUni_Lab9_Multi-Agent_MCP-A2A |
| **Codelab** | [CODELAB.md](CODELAB.md) |

---

## 1. Chuẩn bị môi trường

- [x] Cài đặt Python 3.11+ và `uv`
- [x] Chạy `uv sync` để cài dependencies
- [x] Tạo file `.env` từ `.env.example`
- [x] Cấu hình `OPENROUTER_API_KEY` trên [OpenRouter](https://openrouter.ai)
- [x] Cấu hình model: `OPENROUTER_MODEL=openai/gpt-3.5-turbo`
- [x] Cấu hình `OPENROUTER_MAX_TOKENS=1024` (tránh lỗi 402 insufficient credits)
- [x] Cấu hình `REGISTRY_URL=http://localhost:10000`

---

## 2. Phần 1: Direct LLM Calling (Stage 1)

**File:** `stages/stage_1_direct_llm/main.py`, `common/llm.py`

- [x] **Bước 1** — Chạy demo Stage 1
  ```bash
  uv run python stages/stage_1_direct_llm/main.py
  ```
- [x] **Bước 2** — Đọc hiểu code (`get_llm()`, `SystemMessage`, `HumanMessage`)
- [x] **Bài tập 1.1** — Đổi `QUESTION` sang câu hỏi pháp lý tiếng Việt (hợp đồng lao động / sa thải trái pháp luật)
- [x] **Bài tập 1.2** — Thêm `temperature=0.3` vào `get_llm()` trong `common/llm.py`
- [x] Fix lỗi OpenRouter 402 — giới hạn `max_tokens` trong `common/llm.py`

---

## 3. Phần 2: LLM + RAG & Tools (Stage 2)

**File:** `stages/stage_2_rag_tools/main.py`

- [x] **Bước 1** — Chạy demo Stage 2
  ```bash
  uv run python stages/stage_2_rag_tools/main.py
  ```
- [x] **Bước 2** — Phân tích code (`@tool`, `LEGAL_KNOWLEDGE`, `.bind_tools()`)
- [x] **Bài tập 2.1** — Thêm entry `labor_law` vào `LEGAL_KNOWLEDGE` (Bộ luật Lao động VN 2019)
- [x] **Bài tập 2.2** — Tạo tool `check_statute_of_limitations` và thêm vào `TOOLS`
- [x] Cập nhật `QUESTION` để test RAG + tool mới (câu hỏi lao động + thời hiệu khởi kiện)

---

## 4. Phần 3: Single Agent với ReAct (Stage 3)

**File:** `stages/stage_3_single_agent/main.py`

- [x] **Bước 1** — Chạy demo Stage 3
  ```bash
  uv run python stages/stage_3_single_agent/main.py
  ```
- [x] **Bước 2** — Quan sát output ReAct (Think → Act → Observe)
- [x] **Bước 3** — Đọc code (`create_react_agent`, so sánh với Stage 2)
- [x] **Bài tập 3.1** — Thêm tool `search_case_law` và test với câu hỏi breach of contract
- [x] **Bài tập 3.2** — Bật debug agent reasoning (`debug=True` trong `create_react_agent`; thay cho `verbose=True` trong Gradio/LangGraph mới)

---

## 5. Phần 4: Multi-Agent In-Process (Stage 4)

**File:** `stages/stage_4_milti_agent/main.py`

- [x] **Bước 1** — Chạy demo Stage 4
  ```bash
  uv run python stages/stage_4_milti_agent/main.py
  ```
- [x] **Bước 2** — Phân tích kiến trúc (`LegalState`, agents, `Send()`, `graph.add_node/edge`)
- [x] **Bước 3** — Hiểu graph topology (analyze_law → routing → parallel → aggregate)
- [x] **Bài tập 4.1** — Thêm `privacy_agent` (GDPR / privacy law) và kết nối vào `aggregate`
- [x] **Bài tập 4.2** — Conditional routing bằng keyword (`tax`, `privacy`, `gdpr`, …) qua `Send()` API

---

## 6. Phần 5: Distributed A2A System (Stage 5)

**Files:** `start_all.sh`, `stop_all.sh`, `test_client.py`, `customer_agent/`, `law_agent/`, `tax_agent/`, `compliance_agent/`, `registry/`

- [x] **Bước 1** — Khởi động hệ thống
  ```bash
  ./start_all.sh
  ```
- [x] **Bước 2** — Test end-to-end
  ```bash
  uv run python test_client.py
  ```
- [x] **Bước 3** — Quan sát logs các service (ports 10000–10103) và `trace_id`
- [x] **Bài tập 5.1** — Trace request flow qua `trace_id` trong logs (Customer → Law → Tax/Compliance)
- [x] **Bài tập 5.2** — Hiểu xử lý khi Tax Agent down (graceful degradation: `[Tax analysis unavailable: ...]`)
- [x] **Bài tập 5.3** — Rút gọn system prompt trong `tax_agent/graph.py` (< 150 từ)
- [x] Fix `start_all.sh` — dùng `uv run python` / `.venv/bin/python` thay vì `python` không tồn tại
- [x] Fix `start_all.sh` — auto-stop ports cũ + `stop_all.sh` (tránh lỗi `address already in use`)
- [x] Refactor `common/customer_client.py` — shared A2A client cho `test_client.py` và Gradio UI
- [x] Thêm đo latency vào `test_client.py`

**Kết quả test thành công:** Customer Agent v1.0.0 → response đầy đủ, latency ~15–17s.

---

## 7. Phần 6: Tổng kết & Mở rộng

- [x] So sánh 5 stages (Direct LLM → Tools → ReAct → Multi-Agent → Distributed A2A)
- [x] Trả lời câu hỏi ôn tập (single vs multi-agent, A2A vs REST, delegation depth, Registry)
- [x] **Bài tập cộng điểm — Latency**
  - Đo được: **~14.77s – 17.17s** end-to-end
  - Đã áp dụng: `gpt-3.5-turbo`, giảm `max_tokens`, rút gọn Tax Agent prompt
  - Đề xuất thêm: keyword routing ở Law Agent, bỏ Customer ReAct layer, `max_tokens=512`

---

## 8. Mở rộng (ngoài codelab) — Gradio Web UI

**Files:** `gradio_app.py`, `common/workflow_viz.py`

- [x] Tạo Gradio chat UI kết nối Customer Agent (port 7860)
- [x] Thêm **animated workflow diagram** (User → Customer → Registry → Law → Tax/Compliance parallel → Response)
- [x] Fix bug Gradio 6 — chat history dùng messages format `{"role", "content"}`
- [x] Chạy demo UI thành công
  ```bash
  # Terminal 1
  ./start_all.sh

  # Terminal 2
  uv run python gradio_app.py
  # Mở http://127.0.0.1:7860
  ```

---

## 9. Tóm tắt file đã chỉnh sửa / tạo mới

| File | Thay đổi |
|------|----------|
| `common/llm.py` | `temperature=0.3`, `max_tokens` cap |
| `stages/stage_1_direct_llm/main.py` | Câu hỏi tiếng Việt |
| `stages/stage_2_rag_tools/main.py` | `labor_law`, `check_statute_of_limitations` |
| `stages/stage_3_single_agent/main.py` | `search_case_law`, `debug=True` |
| `stages/stage_4_milti_agent/main.py` | `privacy_agent`, keyword routing |
| `tax_agent/graph.py` | Prompt ngắn gọn |
| `start_all.sh` / `stop_all.sh` | Fix Python path, port cleanup |
| `common/customer_client.py` | Shared A2A client (mới) |
| `test_client.py` | Dùng shared client + latency |
| `gradio_app.py` | Web UI (mới) |
| `common/workflow_viz.py` | Workflow animation (mới) |
| `pyproject.toml` | Thêm dependency `gradio` |
| `.env.example` | Thêm `OPENROUTER_MAX_TOKENS` |

---

## 10. Lệnh chạy nhanh (Quick demo)

```bash
# Stage 1–4 (standalone, không cần server)
uv run python stages/stage_1_direct_llm/main.py
uv run python stages/stage_2_rag_tools/main.py
uv run python stages/stage_3_single_agent/main.py
uv run python stages/stage_4_milti_agent/main.py

# Stage 5 (distributed A2A)
./start_all.sh
uv run python test_client.py

# Gradio UI
uv run python gradio_app.py

# Dừng services
./stop_all.sh
```

---

## 11. Ghi chú khi demo

| Vấn đề | Nguyên nhân | Cách xử lý |
|--------|-------------|------------|
| OpenRouter 402 | Credits thấp / `max_tokens` quá cao | Dùng `gpt-3.5-turbo`, `OPENROUTER_MAX_TOKENS=512–1024` |
| `python: command not found` | macOS không có `python` global | Dùng `./start_all.sh` đã fix |
| `address already in use` | Chạy `start_all.sh` nhiều lần | `./stop_all.sh` hoặc chạy lại `start_all.sh` (auto-stop) |
| HTTP 405 trên browser | Mở agent API URL bằng GET | Dùng `test_client.py` hoặc Gradio UI (:7860), không mở :10100 trực tiếp |
| Gradio chat error | Gradio 6 cần messages format | Đã fix trong `gradio_app.py` |

---

*Hoàn thành toàn bộ CODELAB Phần 1–6 + Gradio UI. Chờ hướng dẫn tiếp theo.*
