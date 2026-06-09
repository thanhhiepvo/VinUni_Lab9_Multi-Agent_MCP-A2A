"""Specialized worker agents for the Day08 Supervisor-Workers system."""

from __future__ import annotations

from dataclasses import dataclass, field

from .llm_client import chat_completion
from .retrieval_utils import format_chunks_for_prompt, retrieve_by_type


@dataclass
class WorkerResult:
    """Output from a single worker."""

    worker_name: str
    summary: str
    chunks: list[dict] = field(default_factory=list)
    doc_type: str = ""


class LegalWorker:
    """Worker 1 — retrieves and analyzes legal statutes / regulations."""

    name = "legal_worker"

    def run(self, query: str, top_k: int = 5) -> WorkerResult:
        chunks = retrieve_by_type(query, doc_type="legal", top_k=top_k)
        context = format_chunks_for_prompt(chunks)

        summary = chat_completion(
            system_prompt=(
                "Bạn là chuyên gia pháp luật Việt Nam về phòng chống ma tuý. "
                "Phân tích dựa CHỈ trên context được cung cấp. "
                "Trích dẫn điều khoản/nghị định khi có thể. Tối đa 200 từ."
            ),
            user_prompt=f"Câu hỏi: {query}\n\nContext pháp luật:\n{context}",
            max_tokens=500,
        )

        return WorkerResult(
            worker_name=self.name,
            summary=summary,
            chunks=chunks,
            doc_type="legal",
        )


class NewsWorker:
    """Worker 2 — retrieves and summarizes news about artists / drug cases."""

    name = "news_worker"

    def run(self, query: str, top_k: int = 5) -> WorkerResult:
        chunks = retrieve_by_type(query, doc_type="news", top_k=top_k)
        context = format_chunks_for_prompt(chunks)

        summary = chat_completion(
            system_prompt=(
                "Bạn là nhà phân tích tin tức về các vụ việc nghệ sĩ liên quan ma tuý. "
                "Tóm tắt dựa CHỈ trên context báo chí. Nêu tên, sự kiện, nguồn tin. "
                "Tối đa 200 từ."
            ),
            user_prompt=f"Câu hỏi: {query}\n\nContext tin tức:\n{context}",
            max_tokens=500,
        )

        return WorkerResult(
            worker_name=self.name,
            summary=summary,
            chunks=chunks,
            doc_type="news",
        )


class CitationWorker:
    """Worker 3 — synthesizes worker outputs into a final cited answer."""

    name = "citation_worker"

    def run(
        self,
        query: str,
        worker_results: list[WorkerResult],
    ) -> dict:
        all_chunks: list[dict] = []
        briefs: list[str] = []

        for result in worker_results:
            all_chunks.extend(result.chunks)
            briefs.append(f"## {result.worker_name}\n{result.summary}")

        if not all_chunks:
            return {
                "answer": "Tôi không thể xác minh thông tin này từ các nguồn hiện có.",
                "sources": [],
                "workers_used": [r.worker_name for r in worker_results],
            }

        # Deduplicate chunks by content prefix
        seen: set[str] = set()
        unique_chunks: list[dict] = []
        for chunk in all_chunks:
            key = chunk["content"][:200]
            if key not in seen:
                seen.add(key)
                unique_chunks.append(chunk)

        from ..task10_generation import format_context, reorder_for_llm

        reordered = reorder_for_llm(unique_chunks[:8])
        context = format_context(reordered)
        worker_brief = "\n\n".join(briefs)

        answer = chat_completion(
            system_prompt=(
                "Bạn là trợ lý RAG về pháp luật ma tuý Việt Nam. "
                "Tổng hợp phân tích từ các worker chuyên môn và context gốc. "
                "Mỗi sự kiện/pháp lý PHẢI có citation [Nguồn, Năm/Điều]. "
                "Nếu không đủ evidence → 'Tôi không thể xác minh thông tin này'. "
                "Trả lời tiếng Việt, có cấu trúc."
            ),
            user_prompt=(
                f"Câu hỏi: {query}\n\n"
                f"Phân tích từ workers:\n{worker_brief}\n\n"
                f"Context gốc:\n{context}"
            ),
            max_tokens=900,
        )

        return {
            "answer": answer,
            "sources": unique_chunks,
            "workers_used": [r.worker_name for r in worker_results],
        }


LEGAL_WORKER = LegalWorker()
NEWS_WORKER = NewsWorker()
CITATION_WORKER = CitationWorker()

WORKER_REGISTRY = {
    LEGAL_WORKER.name: LEGAL_WORKER,
    NEWS_WORKER.name: NEWS_WORKER,
}
