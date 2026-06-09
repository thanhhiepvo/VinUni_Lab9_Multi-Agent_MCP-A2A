"""Retrieval helpers filtered by document type for specialized workers."""

from __future__ import annotations

from ..task9_retrieval_pipeline import retrieve


def retrieve_by_type(
    query: str,
    doc_type: str,
    top_k: int = 5,
) -> list[dict]:
    """Run hybrid retrieval pipeline and keep chunks matching doc_type."""
    candidates = retrieve(query, top_k=top_k * 4)
    filtered = [
        item
        for item in candidates
        if item.get("metadata", {}).get("type") == doc_type
    ]
    return filtered[:top_k]


def format_chunks_for_prompt(chunks: list[dict]) -> str:
    """Format retrieved chunks as context for worker LLM prompts."""
    if not chunks:
        return "(Không tìm thấy tài liệu liên quan.)"

    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", f"source_{i}").replace(".md", "")
        parts.append(
            f"[{i}] Nguồn: {source} | score={chunk.get('score', 0):.3f}\n"
            f"{chunk['content'][:1200]}"
        )
    return "\n\n".join(parts)
