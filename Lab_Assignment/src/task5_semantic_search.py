"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4

Lựa chọn:
    - Embedding model: sentence-transformers/all-MiniLM-L6-v2 (cùng model với Task 4)
    - Vector store: FAISS (tìm kiếm dense vector nhanh, local)
    - Similarity: Cosine similarity (chuyển đổi từ L2 distance)
"""

import json
from pathlib import Path

# Cấu hình — phải khớp với Task 4
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
FAISS_INDEX_DIR = Path(__file__).parent.parent / "data" / "faiss_index"

# Cache model để tránh load lại nhiều lần
_model = None
_index = None
_metadata = None


def _load_resources():
    """Load model, FAISS index và metadata một lần duy nhất."""
    global _model, _index, _metadata

    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)

    if _index is None:
        import faiss
        index_path = FAISS_INDEX_DIR / "index.faiss"
        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {index_path}. "
                "Please run task4_chunking_indexing.py first."
            )
        _index = faiss.read_index(str(index_path))

    if _metadata is None:
        meta_path = FAISS_INDEX_DIR / "metadata.json"
        if not meta_path.exists():
            raise FileNotFoundError(
                f"Metadata not found at {meta_path}. "
                "Please run task4_chunking_indexing.py first."
            )
        with open(meta_path, "r", encoding="utf-8") as f:
            _metadata = json.load(f)

    return _model, _index, _metadata


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity (FAISS).

    Cách hoạt động:
        1. Embed query bằng cùng model với Task 4 (all-MiniLM-L6-v2)
        2. Tìm kiếm top_k nearest neighbors trong FAISS index (L2 distance)
        3. Chuyển đổi L2 distance → similarity score (0-1)
        4. Trả về kết quả sorted descending theo score

    Args:
        query: Câu truy vấn (tiếng Việt hoặc tiếng Anh)
        top_k: Số lượng kết quả tối đa trả về

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Similarity score (0-1, càng cao càng liên quan)
            'metadata': dict     # source, type, chunk_index
        }
        Sorted by score descending.
    """
    import numpy as np

    model, index, metadata = _load_resources()

    # Embed query
    query_embedding = model.encode([query]).astype("float32")

    # Giới hạn top_k không vượt quá số chunks trong index
    actual_k = min(top_k, index.ntotal)
    if actual_k == 0:
        return []

    # Tìm kiếm FAISS (L2 distance)
    distances, indices = index.search(query_embedding, actual_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:  # FAISS trả về -1 nếu không đủ kết quả
            continue

        # Chuyển L2 distance → similarity score (0-1)
        # Công thức: score = 1 / (1 + distance)
        score = float(1.0 / (1.0 + dist))

        chunk = metadata[idx]
        results.append({
            "content": chunk["content"],
            "score": score,
            "metadata": chunk["metadata"]
        })

    # Sort descending by score (đã là thứ tự đúng từ FAISS, nhưng sort lại để chắc chắn)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


if __name__ == "__main__":
    # Test
    print("=== Semantic Search Test ===\n")
    test_queries = [
        "hình phạt cho tội tàng trữ ma tuý",
        "nghệ sĩ bị bắt vì sử dụng ma túy",
        "cai nghiện bắt buộc",
    ]
    for query in test_queries:
        print(f"Query: {query}")
        results = semantic_search(query, top_k=3)
        for i, r in enumerate(results, 1):
            src = r["metadata"].get("source", "?")
            print(f"  [{i}] score={r['score']:.3f} | {src} | {r['content'][:80]}...")
        print()
