"""
Task 10 — Generation Có Citation.

Pipeline:
    1. Retrieve chunks (Task 9 hybrid pipeline)
    2. Reorder chunks → tránh "lost in the middle"
    3. Format context với source labels
    4. Call LLM (OpenAI gpt-4o-mini) với system prompt yêu cầu citation
    5. Return answer + sources

Các lựa chọn kỹ thuật:
    - top_k=5: đủ evidence, không quá dài → tránh lost in the middle
    - temperature=0.3: RAG cần factual accuracy, ít sáng tạo
    - top_p=0.9: diversity vừa đủ
    - Model: gpt-4o-mini (nhanh, rẻ, đủ chất lượng cho tiếng Việt)

Lost in the middle:
    LLM nhớ tốt thông tin ở ĐẦU và CUỐI, quên thông tin ở GIỮA.
    → Đặt chunks quan trọng nhất ở đầu và cuối context.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from .task9_retrieval_pipeline import retrieve


# =============================================================================
# CONFIGURATION
# =============================================================================

TOP_K = 5           # Số chunks đưa vào context (đủ evidence, không quá dài)
TOP_P = 0.9         # Nucleus sampling (diversity vừa đủ)
TEMPERATURE = 0.3   # Thấp để factual, cao hơn 0 để không quá cứng nhắc


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Bạn là trợ lý pháp luật chuyên về lĩnh vực phòng, chống ma tuý tại Việt Nam.
Trả lời câu hỏi dựa HOÀN TOÀN vào các đoạn văn bản được cung cấp trong phần Context.

Quy tắc bắt buộc:
1. Mỗi thông tin thực tế PHẢI có citation trong ngoặc vuông, ví dụ:
   [Luật Phòng chống ma tuý 2021, Điều 3] hoặc [VnExpress, article_01]
2. Nếu thông tin KHÔNG có trong context → trả lời:
   "Tôi không thể xác minh thông tin này từ các nguồn hiện có."
3. Không được bịa đặt hoặc suy luận ngoài context.
4. Trả lời bằng tiếng Việt, rõ ràng, có cấu trúc.
5. Nếu có nhiều nguồn nói về cùng một vấn đề, hãy tổng hợp và cite tất cả."""


# =============================================================================
# DOCUMENT REORDERING — tránh "lost in the middle"
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp lại chunks để LLM chú ý đều các thông tin quan trọng.

    Vấn đề "Lost in the Middle" (Liu et al. 2023):
        LLM nhớ tốt thông tin ở đầu và cuối context,
        nhưng bỏ qua thông tin ở giữa.

    Chiến lược: xen kẽ odd/even positions
        Input  (sorted by score): [A(0.9), B(0.8), C(0.7), D(0.6), E(0.5)]
        Output:                   [A(0.9), C(0.7), E(0.5), D(0.6), B(0.8)]
        → Chunk quan trọng nhất (A) ở đầu
        → Chunk quan trọng thứ 2 (B) ở cuối
        → Chunk ít quan trọng nhất (E) ở giữa

    Args:
        chunks: List sorted by score descending

    Returns:
        List reordered theo chiến lược tránh lost in the middle.
    """
    if len(chunks) <= 2:
        return chunks

    # Tách ra: chẵn index (quan trọng → đầu) và lẻ index (quan trọng → cuối)
    even_chunks = [chunks[i] for i in range(0, len(chunks), 2)]   # [0, 2, 4...]
    odd_chunks = [chunks[i] for i in range(1, len(chunks), 2)]    # [1, 3, 5...]

    # Ghép: even đầu, odd đảo ngược cuối
    return even_chunks + odd_chunks[::-1]


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string với source labels cho citation.

    Args:
        chunks: List of {'content': str, 'metadata': dict, 'score': float}

    Returns:
        Formatted context string, mỗi chunk có label để LLM cite.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("source", f"source_{i}")
        doc_type = chunk.get("metadata", {}).get("type", "unknown")
        # Bỏ phần mở rộng file để citation gọn hơn
        source_label = source.replace(".md", "").replace(".pdf", "")

        context_parts.append(
            f"[Document {i} | Nguồn: {source_label} | Loại: {doc_type}]\n"
            f"{chunk['content'].strip()}"
        )

    return "\n\n---\n\n".join(context_parts)


# =============================================================================
# GENERATION
# =============================================================================

def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation có citation.

    Args:
        query: Câu hỏi của user

    Returns:
        {
            'answer': str,           # Câu trả lời có citation
            'sources': list[dict],   # Các chunks đã dùng làm context
            'retrieval_source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # ─── Step 1: Retrieve ─────────────────────────────────────────────────────
    chunks = retrieve(query, top_k=top_k)

    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ các nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    # ─── Step 2: Reorder (tránh lost in the middle) ───────────────────────────
    reordered = reorder_for_llm(chunks)

    # ─── Step 3: Format context ───────────────────────────────────────────────
    context = format_context(reordered)

    # ─── Step 4: Build prompt ─────────────────────────────────────────────────
    user_message = f"""Context:

{context}

---

Câu hỏi: {query}"""

    # ─── Step 5: Call LLM ─────────────────────────────────────────────────────
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=TEMPERATURE,
        top_p=TOP_P,
    )

    answer = response.choices[0].message.content

    # ─── Step 6: Return ───────────────────────────────────────────────────────
    retrieval_src = chunks[0].get("source", "hybrid") if chunks else "none"
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_src,
    }


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo pháp luật Việt Nam?",
        "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma tuý?",
        "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma tuý 2021?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Nguồn: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
