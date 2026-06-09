"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search (Task 5) + BM25 lexical search (Task 6)
+ RRF reranking (Task 7) + PageIndex fallback (Task 8).

Pipeline:
    Query
      ├→ Semantic Search (FAISS)  → dense_results
      ├→ Lexical Search  (BM25)   → sparse_results
      │
      ├→ Merge bằng RRF           → merged_results  (source='hybrid')
      │
      └→ If best_score < threshold:
            └→ PageIndex Vectorless → fallback       (source='pageindex')

Lý do dùng RRF để merge:
    - Semantic và BM25 có thang điểm khác nhau hoàn toàn
      (cosine 0-1 vs BM25 0-∞), không thể cộng trực tiếp
    - RRF chỉ dùng rank position → không phụ thuộc thang điểm
    - Hiệu quả đã được chứng minh (Elasticsearch Hybrid Search dùng RRF)
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


# =============================================================================
# CONFIGURATION
# =============================================================================

SCORE_THRESHOLD = 0.30   # Nếu best RRF score < threshold → fallback PageIndex
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_pageindex_fallback: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với hybrid search + fallback logic.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả cuối cùng
        score_threshold: Ngưỡng RRF score tối thiểu; dưới ngưỡng → fallback
        use_pageindex_fallback: Có dùng PageIndex fallback hay không

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': str    # 'hybrid' | 'pageindex'
        }
        Sorted by score descending.
    """
    # ─── Step 1: Song song semantic + lexical ─────────────────────────────────
    fetch_k = top_k * 3  # Lấy nhiều hơn top_k để RRF có đủ candidates

    dense_results = semantic_search(query, top_k=fetch_k)
    sparse_results = lexical_search(query, top_k=fetch_k)

    # ─── Step 2: Merge bằng RRF ───────────────────────────────────────────────
    # RRF gộp 2 ranked lists → score không phụ thuộc thang điểm
    merged = rerank_rrf([dense_results, sparse_results], top_k=top_k * 2)

    # Đánh dấu nguồn là 'hybrid'
    for item in merged:
        item["source"] = "hybrid"

    # ─── Step 3: Lấy top_k ────────────────────────────────────────────────────
    final_results = merged[:top_k]

    # ─── Step 4: Fallback sang PageIndex nếu cần ──────────────────────────────
    if use_pageindex_fallback:
        best_score = final_results[0]["score"] if final_results else 0.0
        if best_score < score_threshold:
            try:
                fallback = pageindex_search(query, top_k=top_k)
                if fallback:
                    return fallback
            except Exception as e:
                # PageIndex không available → giữ kết quả hybrid
                print(f"  ⚠ PageIndex fallback failed: {e}")

    return final_results


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý",
        "Nghệ sĩ nào bị bắt vì sử dụng ma tuý",
        "Luật phòng chống ma tuý 2021 quy định gì về cai nghiện",
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            src = r["metadata"].get("source", "?")
            print(f"  {i}. [score={r['score']:.5f}] [{r['source']}] {src} | {r['content'][:70]}...")
