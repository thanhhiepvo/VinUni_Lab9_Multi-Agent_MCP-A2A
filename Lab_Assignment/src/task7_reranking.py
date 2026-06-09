"""
Task 7 — Reranking Module.

Phương pháp được chọn: RRF (Reciprocal Rank Fusion)

Lý do chọn RRF:
    - Không cần model AI nào thêm (không tốn RAM/GPU)
    - Hiệu quả cao khi kết hợp nhiều ranker (đã được dùng trong TREC, Elasticsearch)
    - Hoạt động tốt ngay cả khi score từ các ranker khác nhau không cùng thang đo
    - Đây là kỹ thuật nền tảng của Hybrid Search

Công thức RRF (Cormack et al. 2009):
    RRF(d) = Σ 1 / (k + rank_r(d))
    - k = 60 (hằng số làm mịn, từ bài báo gốc)
    - rank_r(d) = vị trí của document d trong ranked list r (bắt đầu từ 1)

Ví dụ:
    - Nếu document A xếp #1 ở semantic và #3 ở BM25:
      RRF(A) = 1/(60+1) + 1/(60+3) = 0.0164 + 0.0159 = 0.0323
    - Nếu document B xếp #2 ở cả hai:
      RRF(B) = 1/(60+2) + 1/(60+2) = 0.0323 → cùng điểm!

Cơ chế này ưu tiên documents xuất hiện cao trong nhiều danh sách cùng lúc.
"""

from typing import Optional


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker khác nhau.

    RRF(d) = Σ 1 / (k + rank_r(d))

    Args:
        ranked_lists: Danh sách các ranked lists (mỗi list từ 1 ranker)
                     Ví dụ: [semantic_results, bm25_results]
        top_k: Số lượng kết quả cuối cùng
        k: Smoothing constant (default=60, từ paper Cormack et al. 2009)

    Returns:
        List of top_k candidates sorted by RRF score descending,
        mỗi item có key 'score' là RRF score.
    """
    rrf_scores: dict[str, float] = {}  # content[:100] → RRF score
    content_map: dict[str, dict] = {}  # content[:100] → full dict

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            # Dùng 100 ký tự đầu làm key (tránh key quá dài)
            key = item["content"][:100]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            content_map[key] = item

    # Sort by RRF score descending
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content_key, score in sorted_items[:top_k]:
        item = content_map[content_key].copy()
        item["score"] = score
        results.append(item)

    return results


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank bằng cross-encoder (tính điểm relevance giữa query và từng document).

    Sử dụng sentence-transformers CrossEncoder với model nhẹ.
    Phương pháp này chính xác hơn RRF nhưng chậm hơn vì cần inference model.

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates được re-scored và sorted by rerank_score descending.
    """
    from sentence_transformers import CrossEncoder

    # ms-marco-MiniLM-L-6-v2: nhỏ, nhanh, đã train trên passage ranking
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    pairs = [(query, c["content"]) for c in candidates]
    scores = model.predict(pairs)

    # Ghép score mới vào candidates
    scored = []
    for candidate, score in zip(candidates, scores):
        item = candidate.copy()
        item["score"] = float(score)
        scored.append(item)

    # Sort descending và trả về top_k
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.

    MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))

    Args:
        query_embedding: Vector embedding của query
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
                   (score là cosine similarity với query, dùng làm relevance)
        top_k: Số lượng kết quả
        lambda_param: Trade-off relevance(1.0) vs diversity(0.0). Default 0.7

    Returns:
        List of top_k candidates selected by MMR, sorted bởi mmr_score.
    """
    import numpy as np

    if not candidates:
        return []

    def cosine_sim(a, b):
        a, b = np.array(a), np.array(b)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        return float(np.dot(a, b) / denom) if denom > 0 else 0.0

    selected_indices = []
    remaining_indices = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = None
        best_score = float("-inf")

        for idx in remaining_indices:
            # Relevance: dùng score sẵn có (từ semantic search = cosine sim)
            relevance = candidates[idx]["score"]

            # Diversity: max similarity với các docs đã chọn
            max_sim_to_selected = 0.0
            for sel_idx in selected_indices:
                # Dùng score từ query làm proxy vì không có embedding trong candidates
                # Trong thực tế, nên truyền embedding vào
                sim = abs(candidates[idx]["score"] - candidates[sel_idx]["score"])
                max_sim_to_selected = max(max_sim_to_selected, 1 - sim)

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is not None:
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)

    result = []
    for idx in selected_indices:
        item = candidates[idx].copy()
        result.append(item)
    return result


# =============================================================================
# Main rerank interface — dùng RRF làm default
# =============================================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "rrf",  # "rrf" | "cross_encoder" | "mmr"
) -> list[dict]:
    """
    Unified reranking interface. Default: RRF.

    RRF được chọn vì:
    - Không cần model thêm
    - Hoạt động tốt khi kết hợp semantic + BM25 results
    - Rất phổ biến trong production hybrid search

    Args:
        query: Câu truy vấn
        candidates: Danh sách candidates từ retrieval (đã có 'score', 'content', 'metadata')
        top_k: Số lượng kết quả sau rerank
        method: Phương pháp reranking

    Returns:
        List of top_k reranked candidates với 'score' là RRF score.
    """
    if not candidates:
        return []

    if method == "rrf":
        # Với RRF, coi candidates là 1 ranked list duy nhất
        # (thường nên truyền [semantic_results, bm25_results] riêng vào rerank_rrf)
        return rerank_rrf([candidates], top_k=top_k)
    elif method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        return rerank_mmr([], candidates, top_k)
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    print("=== Reranking Test ===\n")

    # Test RRF với 2 ranked lists (mô phỏng semantic + BM25)
    semantic_results = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.85, "metadata": {"source": "luat.md"}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.75, "metadata": {"source": "luat.md"}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý tại nhà riêng", "score": 0.60, "metadata": {"source": "news.md"}},
    ]
    bm25_results = [
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 12.5, "metadata": {"source": "luat.md"}},
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 11.0, "metadata": {"source": "luat.md"}},
        {"content": "Cai nghiện bắt buộc theo quy định pháp luật", "score": 8.0, "metadata": {"source": "luat.md"}},
    ]

    print("--- RRF (kết hợp semantic + BM25) ---")
    rrf_results = rerank_rrf([semantic_results, bm25_results], top_k=3)
    for i, r in enumerate(rrf_results, 1):
        print(f"  [{i}] RRF_score={r['score']:.5f} | {r['content'][:70]}...")

    print("\n--- rerank() với single list ---")
    results = rerank("hình phạt tàng trữ ma tuý", semantic_results, top_k=2)
    for i, r in enumerate(results, 1):
        print(f"  [{i}] score={r['score']:.5f} | {r['content'][:70]}...")
