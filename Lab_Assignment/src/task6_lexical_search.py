"""
Task 6 — Lexical Search Module (BM25).

Sử dụng BM25 (Best Match 25) — thuật toán tìm kiếm từ khóa phổ biến nhất hiện nay.
Được dùng trong Elasticsearch, Lucene, và nhiều search engine khác.

Cách hoạt động của BM25:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn từ phổ biến
    - Document length normalization: tránh thiên vị document dài
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)

Ưu điểm so với vector search:
    - Tìm chính xác từ khóa, tên riêng (tên người, điều luật, ...)
    - Không cần GPU hay model lớn
    - Kết quả giải thích được (keyword match)

Kết hợp với Semantic Search (Task 5) → Hybrid Search (Task 9).
"""

import json
from pathlib import Path

# Đường dẫn tới metadata (đã được tạo bởi Task 4)
FAISS_INDEX_DIR = Path(__file__).parent.parent / "data" / "faiss_index"

# Cache BM25 index và corpus để tránh khởi tạo lại nhiều lần
_bm25 = None
_corpus: list[dict] = []


def _load_corpus() -> list[dict]:
    """
    Load corpus từ FAISS metadata.json (được tạo bởi Task 4).
    Tái sử dụng corpus đã có — không đọc lại file .md từ đầu.
    """
    meta_path = FAISS_INDEX_DIR / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(
            f"Metadata not found at {meta_path}. "
            "Please run task4_chunking_indexing.py first."
        )
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Tokenization: lowercase + split theo khoảng trắng (đơn giản, phù hợp tiếng Việt
    vì tiếng Việt đã cách từ bằng dấu cách như tiếng Anh).

    Args:
        corpus: List of {'content': str, 'metadata': dict}

    Returns:
        BM25Okapi object
    """
    from rank_bm25 import BM25Okapi

    # Tokenize — lowercase và split theo whitespace
    # Tiếng Việt tách từ tự nhiên bằng dấu cách → đơn giản hiệu quả
    tokenized_corpus = [doc["content"].lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25


def _get_bm25():
    """Lazy init: chỉ build BM25 index một lần khi cần."""
    global _bm25, _corpus
    if _bm25 is None:
        _corpus = _load_corpus()
        _bm25 = build_bm25_index(_corpus)
    return _bm25, _corpus


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Cách hoạt động:
        1. Tokenize query (lowercase + split)
        2. Tính BM25 score cho tất cả documents trong corpus
        3. Sort descending, lấy top_k
        4. Chỉ trả về documents có score > 0 (có ít nhất 1 từ khớp)

    Args:
        query: Câu truy vấn (từ khóa cần tìm)
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # BM25 score (>0 nghĩa là có từ khớp)
            'metadata': dict     # source, type, chunk_index
        }
        Sorted by score descending.
    """
    import numpy as np

    bm25, corpus = _get_bm25()

    # Tokenize query
    tokenized_query = query.lower().split()

    # Tính BM25 score cho toàn bộ corpus
    scores = bm25.get_scores(tokenized_query)

    # Lấy top_k indices, sorted descending
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:  # Chỉ lấy documents có ít nhất 1 từ khớp
            results.append({
                "content": corpus[idx]["content"],
                "score": float(scores[idx]),
                "metadata": corpus[idx]["metadata"]
            })

    return results  # Đã được sort descending bởi argsort


if __name__ == "__main__":
    print("=== BM25 Lexical Search Test ===\n")

    test_queries = [
        "Điều 248 tàng trữ trái phép chất ma tuý",
        "hình phạt tù chung thân ma túy",
        "Hữu Tín bị bắt cocaine",
        "cai nghiện bắt buộc tự nguyện",
        "nghệ sĩ An Tây",
    ]

    for query in test_queries:
        print(f"Query: \"{query}\"")
        results = lexical_search(query, top_k=3)
        if results:
            for i, r in enumerate(results, 1):
                src = r["metadata"].get("source", "?")
                print(f"  [{i}] score={r['score']:.3f} | {src} | {r['content'][:80]}...")
        else:
            print("  (Không tìm thấy kết quả)")
        print()
