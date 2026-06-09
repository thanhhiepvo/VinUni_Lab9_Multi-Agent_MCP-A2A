"""Supervisor agent — routes queries to specialized workers and aggregates results."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator

from .workers import (
    CITATION_WORKER,
    LEGAL_WORKER,
    NEWS_WORKER,
    WORKER_REGISTRY,
    WorkerResult,
)


LEGAL_KEYWORDS = [
    "luật", "điều", "hình phạt", "tội", "nghị định", "pháp luật",
    "cai nghiện", "xử phạt", "bộ luật", "quy định", "điều kiện",
    "tàng trữ", "buôn bán", "sử dụng trái phép",
]

NEWS_KEYWORDS = [
    "nghệ sĩ", "ca sĩ", "diễn viên", "rapper", "bắt", "tạm giữ",
    "tin tức", "bài báo", "vụ án", "scandal", "showbiz", "người nổi tiếng",
]


@dataclass
class PipelineState:
    """Tracks supervisor pipeline progress for UI animation."""

    step: str = "idle"
    message: str = "Sẵn sàng."
    workers_planned: list[str] = field(default_factory=list)
    worker_results: list[WorkerResult] = field(default_factory=list)
    final_answer: str = ""
    sources: list[dict] = field(default_factory=list)


class SupervisorAgent:
    """
    Supervisor-Workers pattern for Day08 RAG.

    Architecture:
        Supervisor → [Legal Worker | News Worker] (parallel) → Citation Worker
    """

    def plan_workers(self, query: str) -> list[str]:
        """Decide which workers to invoke based on query keywords."""
        q = query.lower()
        planned: list[str] = []

        if any(kw in q for kw in LEGAL_KEYWORDS):
            planned.append(LEGAL_WORKER.name)
        if any(kw in q for kw in NEWS_KEYWORDS):
            planned.append(NEWS_WORKER.name)

        # Default: use both workers for comprehensive coverage
        if not planned:
            planned = [LEGAL_WORKER.name, NEWS_WORKER.name]

        return planned

    async def _run_worker(self, name: str, query: str) -> WorkerResult:
        """Run a worker in a thread pool (retrieval + LLM are blocking)."""
        worker = WORKER_REGISTRY[name]
        return await asyncio.to_thread(worker.run, query)

    async def run_stream(self, query: str) -> AsyncIterator[PipelineState]:
        """Execute pipeline and yield state updates for UI animation."""
        state = PipelineState(step="routing", message="Supervisor đang phân tích câu hỏi…")
        state.workers_planned = self.plan_workers(query)
        yield state

        # ── Dispatch workers in parallel ──────────────────────────────────────
        state.step = "workers"
        names = ", ".join(state.workers_planned)
        state.message = f"Dispatch workers song song: {names}"
        yield state

        tasks = [self._run_worker(name, query) for name in state.workers_planned]
        state.worker_results = await asyncio.gather(*tasks)

        state.step = "workers_done"
        state.message = f"Hoàn thành {len(state.worker_results)} worker(s)"
        yield state

        # ── Citation worker synthesizes final answer ──────────────────────────
        state.step = "citation"
        state.message = "Citation Worker đang tổng hợp câu trả lời có trích dẫn…"
        yield state

        result = await asyncio.to_thread(
            CITATION_WORKER.run, query, state.worker_results
        )
        state.final_answer = result["answer"]
        state.sources = result.get("sources", [])
        state.step = "complete"
        state.message = "Hoàn tất."
        yield state

    async def run(self, query: str) -> dict:
        """Run full pipeline and return final result dict."""
        final_state = None
        async for state in self.run_stream(query):
            final_state = state

        assert final_state is not None
        return {
            "answer": final_state.final_answer,
            "sources": final_state.sources,
            "workers_used": final_state.workers_planned,
            "worker_summaries": {
                r.worker_name: r.summary for r in final_state.worker_results
            },
        }


def run_supervisor_pipeline(query: str) -> dict:
    """Synchronous entry point for scripts and tests."""
    return asyncio.run(SupervisorAgent().run(query))


if __name__ == "__main__":
    import json

    demo_q = "Hình phạt cho tội tàng trữ ma tuý và có nghệ sĩ nào bị bắt không?"
    print(f"Query: {demo_q}\n")
    out = run_supervisor_pipeline(demo_q)
    print(json.dumps({k: v for k, v in out.items() if k != "sources"}, ensure_ascii=False, indent=2))
    print(f"\nSources: {len(out['sources'])} chunks")
