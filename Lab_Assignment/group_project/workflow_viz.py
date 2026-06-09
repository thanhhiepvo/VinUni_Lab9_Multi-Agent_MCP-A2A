"""Animated Supervisor-Workers workflow diagram for Gradio UI."""

from __future__ import annotations

STEP_LABELS = {
    "idle": "Sẵn sàng — nhập câu hỏi để bắt đầu.",
    "routing": "Supervisor đang phân tích và chọn workers…",
    "workers": "Legal Worker + News Worker đang chạy song song…",
    "workers_done": "Workers hoàn thành — chuẩn bị tổng hợp.",
    "citation": "Citation Worker đang tạo câu trả lời có trích dẫn…",
    "complete": "Hoàn tất.",
    "error": "Lỗi — kiểm tra API key và FAISS index.",
}

_CSS = """
<style>
.sw-wrap{font-family:system-ui,sans-serif;padding:14px;border-radius:12px;
  background:linear-gradient(135deg,#0f172a,#1e293b);color:#e2e8f0}
.sw-status{text-align:center;font-size:.88rem;color:#94a3b8;margin-bottom:12px;min-height:1.3em}
.sw-row{display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap}
.sw-node{min-width:100px;padding:10px 8px;border-radius:10px;border:2px solid #334155;
  background:#1e293b;text-align:center;transition:all .35s}
.sw-node .t{font-size:.72rem;font-weight:700}.sw-node .s{font-size:.62rem;color:#64748b}
.sw-node.active{border-color:#38bdf8;background:#0c4a6e;box-shadow:0 0 16px rgba(56,189,248,.5);
  animation:sw-pulse 1.2s ease-in-out infinite}
.sw-node.done{border-color:#4ade80;background:#14532d}
.sw-arrow{color:#475569;font-size:1rem}.sw-arrow.active{color:#38bdf8}
@keyframes sw-pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.04)}}
</style>
"""

_ACTIVE = {
    "idle": set(),
    "routing": {"supervisor"},
    "workers": {"legal", "news"},
    "workers_done": set(),
    "citation": {"citation"},
    "complete": {"response"},
    "error": set(),
}

_DONE = {
    "idle": set(),
    "routing": set(),
    "workers": {"supervisor"},
    "workers_done": {"supervisor", "legal", "news"},
    "citation": {"supervisor", "legal", "news"},
    "complete": {"supervisor", "legal", "news", "citation", "response"},
    "error": set(),
}


def _cls(node: str, step: str) -> str:
    if node in _ACTIVE.get(step, set()):
        return "sw-node active"
    if node in _DONE.get(step, set()):
        return "sw-node done"
    return "sw-node"


def render_workflow(step: str, workers: list[str] | None = None) -> str:
    workers = workers or []
    extra = ""
    if workers:
        extra = f"<div style='text-align:center;font-size:.75rem;color:#64748b;margin-top:8px'>Workers: {', '.join(workers)}</div>"

    return f"""{_CSS}
<div class="sw-wrap">
  <div class="sw-status">{STEP_LABELS.get(step, step)}</div>
  <div class="sw-row">
    <div class="{_cls('user', step)}"><div class="t">User</div></div>
    <span class="sw-arrow">→</span>
    <div class="{_cls('supervisor', step)}"><div class="t">Supervisor</div><div class="s">Router</div></div>
    <span class="sw-arrow">→</span>
    <div class="{_cls('legal', step)}"><div class="t">Legal Worker</div><div class="s">luật / nghị định</div></div>
    <span class="sw-arrow">+</span>
    <div class="{_cls('news', step)}"><div class="t">News Worker</div><div class="s">tin tức / nghệ sĩ</div></div>
    <span class="sw-arrow">→</span>
    <div class="{_cls('citation', step)}"><div class="t">Citation Worker</div><div class="s">trích dẫn</div></div>
    <span class="sw-arrow">→</span>
    <div class="{_cls('response', step)}"><div class="t">Response</div></div>
  </div>
  {extra}
</div>"""
