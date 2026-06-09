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

## 9. Day08 — RAG Pipeline + Supervisor-Workers (`Lab_Assignment/`)

> Thư mục `Lab_Assignment/` là project Day08 (lớp trước), **tách biệt** khỏi root Lab9.  
> Cải tiến: **Supervisor → Workers** (3 workers) trên pipeline RAG Task 1–10.

**Chủ đề:** Pháp luật Việt Nam về ma tuý + tin tức nghệ sĩ liên quan ma tuý.

### 9.1 Bài cá nhân (Task 1–10) — đã có sẵn trong repo

- [x] Task 1–3 — Thu thập văn bản pháp luật + crawl báo + convert Markdown (`data/landing/`, `data/standardized/`)
- [x] Task 4 — Chunking & FAISS indexing (`data/faiss_index/`)
- [x] Task 5 — Semantic search (`src/task5_semantic_search.py`)
- [x] Task 6 — Lexical search BM25 (`src/task6_lexical_search.py`)
- [x] Task 7 — Reranking RRF (`src/task7_reranking.py`)
- [x] Task 8 — PageIndex vectorless fallback (`src/task8_pageindex_vectorless.py`)
- [x] Task 9 — Retrieval pipeline hybrid + fallback (`src/task9_retrieval_pipeline.py`)
- [x] Task 10 — Generation có citation + reorder (`src/task10_generation.py`)

### 9.2 Cải tiến nhóm — Supervisor-Workers (≥ 3 workers)

**Yêu cầu:** *Improve Agent Day08 sử dụng pattern Supervisor - Workers (ít nhất 2–3 workers)*

| Agent | Vai trò | File |
|-------|---------|------|
| **Supervisor** | Phân tích câu hỏi → keyword routing → dispatch workers song song | `Lab_Assignment/src/agents/supervisor.py` |
| **Worker 1 — Legal** | RAG retrieve `type=legal` → phân tích luật, hình phạt | `Lab_Assignment/src/agents/workers.py` |
| **Worker 2 — News** | RAG retrieve `type=news` → tóm tắt tin nghệ sĩ / báo chí | `Lab_Assignment/src/agents/workers.py` |
| **Worker 3 — Citation** | Tổng hợp output workers + citation từ context gốc | `Lab_Assignment/src/agents/workers.py` |

- [x] Implement Supervisor với keyword routing (`luật`, `nghệ sĩ`, `hình phạt`, …)
- [x] Legal + News workers chạy **song song** (`asyncio.gather`)
- [x] Citation Worker tổng hợp + dùng `reorder_for_llm()` từ Task 10
- [x] `retrieve_by_type()` lọc chunks theo `metadata.type` (`legal` | `news`)
- [x] LLM client hỗ trợ OpenAI và OpenRouter (`src/agents/llm_client.py`)

**Routing logic:**

| Keywords | Workers |
|----------|---------|
| `luật`, `hình phạt`, `nghị định`, `cai nghiện`, … | Legal Worker |
| `nghệ sĩ`, `bắt`, `tin tức`, `showbiz`, … | News Worker |
| Không match keyword | Cả Legal + News (mặc định) |

### 9.3 Gradio UI + Workflow Animation (Day08)

**Files:** `Lab_Assignment/group_project/app.py`, `workflow_viz.py`

- [x] Gradio chatbot trả lời có citation (port **7861**)
- [x] Animated workflow: User → Supervisor → Legal ∥ News → Citation → Response
- [x] Hiển thị worker summaries + số nguồn đã dùng
- [x] Fix Gradio 6 messages format `{"role", "content"}`

```bash
cd Lab_Assignment
cp .env.example .env   # OPENAI_API_KEY hoặc OPENROUTER_API_KEY

python -m src.agents.supervisor          # CLI test
python group_project/app.py            # UI → http://127.0.0.1:7861
```

### 9.4 So sánh Task 10 (monolith) vs Supervisor-Workers

| | Task 10 (cũ) | Supervisor-Workers (mới) |
|---|-------------|--------------------------|
| Retrieval | 1 pipeline chung | 2 workers chuyên biệt (legal / news) |
| LLM calls | 1 lần | 2 worker + 1 citation = 3 lần |
| Routing | Không | Supervisor keyword routing |
| Parallel | Không | Legal + News đồng thời |
| UI | Không | Gradio + workflow animation |

### 9.5 File Day08 đã tạo / chỉnh sửa

| File | Thay đổi |
|------|----------|
| `Lab_Assignment/src/agents/supervisor.py` | Supervisor orchestrator (mới) |
| `Lab_Assignment/src/agents/workers.py` | Legal, News, Citation workers (mới) |
| `Lab_Assignment/src/agents/retrieval_utils.py` | Filter retrieve by doc type (mới) |
| `Lab_Assignment/src/agents/llm_client.py` | OpenAI / OpenRouter client (mới) |
| `Lab_Assignment/group_project/app.py` | Gradio UI (mới) |
| `Lab_Assignment/group_project/workflow_viz.py` | Pipeline animation (mới) |
| `Lab_Assignment/group_project/README.md` | Kiến trúc + hướng dẫn chạy |
| `Lab_Assignment/requirements.txt` | Thêm `gradio` |
| `Lab_Assignment/.env.example` | Thêm OpenRouter / `LLM_MODEL` |

### 9.6 Evaluation pipeline (chưa hoàn thành)

- [ ] `group_project/evaluation/golden_dataset.json` — 15+ Q&A pairs
- [ ] `group_project/evaluation/eval_pipeline.py` — DeepEval / RAGAS
- [ ] `group_project/evaluation/results.md` — báo cáo metrics
- [ ] So sánh A/B (có reranking vs không / hybrid vs dense-only)

---

## 10. Tóm tắt file đã chỉnh sửa / tạo mới (Lab9 root)

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

## 11. Lệnh chạy nhanh (Quick demo)

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

# Day08 Supervisor-Workers (Lab_Assignment — port 7861)
cd Lab_Assignment && python group_project/app.py
```

---

## 12. Ghi chú khi demo

| Vấn đề | Nguyên nhân | Cách xử lý |
|--------|-------------|------------|
| OpenRouter 402 | Credits thấp / `max_tokens` quá cao | Dùng `gpt-3.5-turbo`, `OPENROUTER_MAX_TOKENS=512–1024` |
| `python: command not found` | macOS không có `python` global | Dùng `./start_all.sh` đã fix |
| `address already in use` | Chạy `start_all.sh` nhiều lần | `./stop_all.sh` hoặc chạy lại `start_all.sh` (auto-stop) |
| HTTP 405 trên browser | Mở agent API URL bằng GET | Dùng `test_client.py` hoặc Gradio UI (:7860), không mở :10100 trực tiếp |
| Gradio chat error | Gradio 6 cần messages format | Đã fix trong `gradio_app.py` và `Lab_Assignment/group_project/app.py` |
| Day08 FAISS not found | Chưa chạy Task 4 | `cd Lab_Assignment && python -m src.task4_chunking_indexing` |
| Day08 LLM error | Thiếu API key | Điền `OPENAI_API_KEY` hoặc `OPENROUTER_API_KEY` trong `Lab_Assignment/.env` |

---

*Hoàn thành: CODELAB Lab9 Phần 1–6 + Gradio UI (root) + Day08 Supervisor-Workers (`Lab_Assignment/`).*
