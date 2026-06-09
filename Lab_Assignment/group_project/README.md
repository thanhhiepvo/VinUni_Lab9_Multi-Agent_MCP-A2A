# Bài Tập Nhóm — RAG Chatbot (Supervisor-Workers)

**Cải tiến Day08:** Multi-agent pattern **Supervisor → Workers** (3 workers)

| Thành viên | MSSV | Nhiệm vụ |
|-----------|------|----------|
| Võ Thanh Hiệp | 2A202600836 | Supervisor-Workers architecture + Gradio UI |

---

## Kiến Trúc Hệ Thống

```
User Question
      │
      ▼
┌─────────────┐
│  Supervisor  │  Phân tích câu hỏi → chọn workers (keyword routing)
└──────┬──────┘
       │  parallel dispatch
   ┌───┴───┐
   ▼       ▼
┌──────┐ ┌──────┐
│Legal │ │ News │   Worker 1: retrieve type=legal + phân tích luật
│Worker│ │Worker│   Worker 2: retrieve type=news + tóm tắt tin tức
└──┬───┘ └──┬───┘
   └───┬────┘
       ▼
┌─────────────┐
│  Citation   │   Worker 3: tổng hợp + citation từ context gốc
│   Worker    │
└──────┬──────┘
       ▼
   Final Answer (có trích dẫn)
```

### Workers (3)

| Worker | File | Chức năng |
|--------|------|-----------|
| **Legal Worker** | `src/agents/workers.py` | RAG retrieve `type=legal` → phân tích điều luật, hình phạt |
| **News Worker** | `src/agents/workers.py` | RAG retrieve `type=news` → tóm tắt vụ nghệ sĩ / báo chí |
| **Citation Worker** | `src/agents/workers.py` | Tổng hợp output 2 workers + `task10` reorder → câu trả lời có citation |

### Supervisor

| Component | File | Chức năng |
|-----------|------|-----------|
| **Supervisor** | `src/agents/supervisor.py` | Keyword routing → `asyncio.gather` workers song song → gọi Citation Worker |

### Tích hợp pipeline Day08

- Task 9 `retrieve()` — hybrid search (semantic + BM25 + RRF + PageIndex fallback)
- Task 10 `reorder_for_llm()`, `format_context()` — tránh lost-in-the-middle
- Workers lọc kết quả theo `metadata.type` (`legal` | `news`)

---

## Hướng Dẫn Chạy

```bash
cd Lab_Assignment

# Cài dependencies (nếu chưa)
pip install -r requirements.txt

# Cấu hình API key
cp .env.example .env
# Điền OPENAI_API_KEY hoặc OPENROUTER_API_KEY

# Đảm bảo FAISS index đã build (Task 4)
python -m src.task4_chunking_indexing

# Chạy Supervisor-Workers CLI test
python -m src.agents.supervisor

# Chạy Gradio UI (port 7861)
python group_project/app.py
```

Mở **http://127.0.0.1:7861** — UI có **animated workflow diagram**.

---

## Cấu Trúc File Mới

```
Lab_Assignment/
├── src/agents/
│   ├── __init__.py
│   ├── supervisor.py      ← Supervisor orchestrator
│   ├── workers.py         ← Legal, News, Citation workers
│   ├── retrieval_utils.py ← Filter retrieve by doc type
│   └── llm_client.py      ← OpenAI / OpenRouter client
└── group_project/
    ├── app.py             ← Gradio chatbot + workflow animation
    ├── workflow_viz.py    ← HTML/CSS pipeline diagram
    └── README.md
```

---

## RAG Evaluation Pipeline

(Xem phần evaluation bên dưới — golden dataset + DeepEval)

- [ ] File `group_project/evaluation/golden_dataset.json` — 15+ cặp Q&A
- [ ] File `group_project/evaluation/eval_pipeline.py` — script chạy evaluation
- [ ] File `group_project/evaluation/results.md` — bảng điểm + phân tích
- [ ] So sánh A/B ít nhất 2 configs

---

## So Sánh: Task 10 (cũ) vs Supervisor-Workers (mới)

| | Task 10 (monolith) | Supervisor-Workers |
|---|-------------------|-------------------|
| Retrieval | 1 pipeline chung | 2 workers chuyên biệt (legal / news) |
| Phân tích | 1 LLM call | 2 worker LLM + 1 citation LLM |
| Routing | Không có | Supervisor keyword routing |
| Parallel | Không | Legal + News song song |
| UI | Không | Gradio + workflow animation |
