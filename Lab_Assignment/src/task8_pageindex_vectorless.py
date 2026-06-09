"""
Task 8 — PageIndex Vectorless RAG.

PageIndex là hệ thống RAG không dùng vector embedding.
Thay vào đó, nó hiểu cấu trúc của document (headings, sections, tables)
và truy xuất theo ngữ nghĩa cấu trúc — "vectorless RAG".

Ưu điểm:
    - Không cần chunking thủ công
    - Không cần embedding model
    - Hiểu được cấu trúc phân cấp của văn bản pháp luật

Flow:
    1. submit_document(pdf_path) → doc_id
    2. is_retrieval_ready(doc_id) → True/False
    3. submit_query(doc_id, query) → retrieval_id
    4. get_retrieval(retrieval_id) → kết quả

Doc IDs đã upload (xem data/pageindex_doc_ids.json):
    - luat-phong-chong-ma-tuy-2021: pi-cmq4unjkw024p01qx344th3as
    - nghi-dinh-105-2021:           pi-cmq4unm2d024r01qx73z164mz
    - nghi-dinh-28-2026:            pi-cmq4uno2e024s01qxbhkxq2th
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
LANDING_LEGAL_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
DOC_IDS_FILE = Path(__file__).parent.parent / "data" / "pageindex_doc_ids.json"

# Doc IDs đã upload
_DOC_IDS = {
    "luat-phong-chong-ma-tuy-2021": "pi-cmq4unjkw024p01qx344th3as",
    "nghi-dinh-105-2021": "pi-cmq4unm2d024r01qx73z164mz",
    "nghi-dinh-28-2026": "pi-cmq4uno2e024s01qxbhkxq2th",
}

_client = None


def _get_client():
    """Khởi tạo PageIndexClient một lần duy nhất."""
    global _client
    if _client is None:
        from pageindex import PageIndexClient
        if not PAGEINDEX_API_KEY:
            raise ValueError("PAGEINDEX_API_KEY chưa được set trong .env")
        _client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    return _client


def upload_documents():
    """
    Upload toàn bộ PDF legal documents lên PageIndex.
    Chỉ cần chạy một lần — doc IDs được lưu vào data/pageindex_doc_ids.json.

    Lưu ý: PageIndex chỉ hỗ trợ PDF, không hỗ trợ .md files.
    """
    client = _get_client()
    doc_ids = {}

    for pdf in sorted(LANDING_LEGAL_DIR.glob("*.pdf")):
        print(f"  Uploading: {pdf.name} ...")
        result = client.submit_document(str(pdf))
        doc_id = result.get("doc_id", "")
        doc_ids[pdf.stem] = doc_id
        print(f"    → doc_id: {doc_id}")

    # Lưu doc IDs ra file
    DOC_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DOC_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(doc_ids, f, indent=2)

    print(f"\n✓ Uploaded {len(doc_ids)} documents. IDs saved to {DOC_IDS_FILE}")
    return doc_ids


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.

    PageIndex tìm kiếm dựa trên cấu trúc document thay vì embedding,
    phù hợp với văn bản pháp luật có cấu trúc phân cấp rõ ràng
    (Chương → Điều → Khoản → Điểm).

    Dùng làm fallback khi hybrid search (Task 9) không đủ kết quả.

    Cơ chế:
        1. Gửi query đến từng document đã upload
        2. Thu thập kết quả từ tất cả documents
        3. Sắp xếp theo độ liên quan và trả về top_k

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
        Sorted by score descending.
    """
    client = _get_client()

    all_results = []
    doc_ids = _DOC_IDS

    for doc_name, doc_id in doc_ids.items():
        try:
            # Kiểm tra document đã sẵn sàng chưa
            if not client.is_retrieval_ready(doc_id):
                print(f"  ⚠ {doc_name} chưa sẵn sàng, bỏ qua...")
                continue

            # Gửi query → nhận retrieval_id
            submit_result = client.submit_query(doc_id=doc_id, query=query)
            retrieval_id = submit_result.get("retrieval_id", "")

            if not retrieval_id:
                continue

            # Poll cho đến khi có kết quả (tối đa 30 giây)
            retrieval_result = None
            for _ in range(15):
                result = client.get_retrieval(retrieval_id)
                status = result.get("status", "")
                if status == "completed":
                    retrieval_result = result
                    break
                time.sleep(2)

            if not retrieval_result:
                continue

            # Cấu trúc thực tế: retrieved_nodes[].relevant_contents[][][].relevant_content
            retrieved_nodes = retrieval_result.get("retrieved_nodes", [])

            for node_idx, node in enumerate(retrieved_nodes[:top_k]):
                title = node.get("title", "")
                # relevant_contents là list of lists of dicts
                relevant_contents = node.get("relevant_contents", [])

                for content_group in relevant_contents:
                    for content_item in content_group:
                        text = content_item.get("relevant_content", "")
                        section = content_item.get("section_title", title)
                        if text:
                            all_results.append({
                                "content": f"[{section}]\n{text}",
                                "score": float(1.0 - node_idx * 0.05),  # score theo thứ tự node
                                "metadata": {
                                    "source": doc_name,
                                    "doc_id": doc_id,
                                    "type": "legal",
                                    "section": section,
                                },
                                "source": "pageindex",
                            })

        except Exception as e:
            print(f"  ⚠ Error querying {doc_name}: {e}")
            continue

    # Sort by score descending và trả về top_k
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:top_k]


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠  Hãy set PAGEINDEX_API_KEY trong file .env")
        print("   Đăng ký tại: https://pageindex.ai/")
    else:
        print("=== PageIndex Vectorless Search Test ===\n")
        test_queries = [
            "hình phạt tội tàng trữ ma tuý",
            "cai nghiện bắt buộc điều kiện",
        ]
        for query in test_queries:
            print(f"Query: \"{query}\"")
            results = pageindex_search(query, top_k=3)
            if results:
                for i, r in enumerate(results, 1):
                    src = r["metadata"].get("source", "?")
                    print(f"  [{i}] score={r['score']:.3f} | {src} | {r['content'][:80]}...")
            else:
                print("  (Không có kết quả)")
            print()
