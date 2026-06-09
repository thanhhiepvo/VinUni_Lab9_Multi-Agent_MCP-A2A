"""
Day08 RAG Chatbot — Supervisor-Workers pattern (Gradio UI).

Run from Lab_Assignment/:
    uv run python group_project/app.py
    # or: python group_project/app.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure src/ is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import gradio as gr  # noqa: E402

from group_project.workflow_viz import render_workflow  # noqa: E402
from src.agents.supervisor import SupervisorAgent  # noqa: E402

EXAMPLES = [
    "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo pháp luật Việt Nam?",
    "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma tuý?",
    "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma tuý 2021?",
    "So sánh hình phạt pháp luật và các vụ nghệ sĩ bị bắt vì ma tuý",
]

_supervisor = SupervisorAgent()


async def chat(message: str, history: list):
    """Stream chat + supervisor workflow animation."""
    message = (message or "").strip()
    history = history or []

    if not message:
        yield history, render_workflow("idle"), ""
        return

    history = history + [{"role": "user", "content": message}]
    yield history, render_workflow("routing"), ""

    try:
        final_state = None
        async for state in _supervisor.run_stream(message):
            final_state = state
            wf = render_workflow(state.step, state.workers_planned)
            if state.step in ("workers", "citation"):
                history = _append_assistant(history, f"⏳ {state.message}")
            yield history, wf, ""

        if final_state is None:
            raise RuntimeError("Pipeline did not return a final state.")

        worker_notes = "\n".join(
            f"**{r.worker_name}:** {r.summary[:300]}…"
            if len(r.summary) > 300
            else f"**{r.worker_name}:** {r.summary}"
            for r in final_state.worker_results
        )
        sources_note = (
            f"\n\n---\n📚 {len(final_state.sources)} nguồn "
            f"| Workers: {', '.join(final_state.workers_planned)}"
        )
        full_answer = (
            f"{final_state.final_answer}\n\n"
            f"<details><summary>Worker summaries</summary>\n\n{worker_notes}</details>"
            f"{sources_note}"
        )

        history = _append_assistant(history, full_answer)
        yield history, render_workflow("complete", final_state.workers_planned), ""

    except Exception as exc:
        history = _append_assistant(history, f"**Lỗi:** {exc}")
        yield history, render_workflow("error"), ""


def _append_assistant(history: list, content: str) -> list:
    history = list(history)
    if history and history[-1].get("role") == "assistant":
        history[-1] = {"role": "assistant", "content": content}
    else:
        history.append({"role": "assistant", "content": content})
    return history


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Day08 RAG — Supervisor Workers") as demo:
        gr.Markdown(
            """
# Day08 RAG Chatbot — Supervisor / Workers
**Supervisor** phân tích câu hỏi → dispatch **Legal Worker** + **News Worker** (song song)
→ **Citation Worker** tổng hợp câu trả lời có trích dẫn.

*Chủ đề: Pháp luật Việt Nam về ma tuý + tin tức nghệ sĩ*
"""
        )
        workflow = gr.HTML(value=render_workflow("idle"))
        chatbot = gr.Chatbot(height=400)
        with gr.Row():
            msg = gr.Textbox(label="Câu hỏi", placeholder="Hỏi về pháp luật ma tuý…", scale=5)
            send = gr.Button("Gửi", variant="primary", scale=1)
        gr.Examples(examples=EXAMPLES, inputs=msg)

        outputs = [chatbot, workflow, msg]
        send.click(chat, [msg, chatbot], outputs)
        msg.submit(chat, [msg, chatbot], outputs)

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="127.0.0.1", server_port=7861)
