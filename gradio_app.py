"""Gradio web UI for the Legal Multi-Agent System (Stage 5).

Requires backend services to be running:
    ./start_all.sh

Then launch this UI:
    uv run python gradio_app.py
"""

from __future__ import annotations

import asyncio

import gradio as gr

from common.customer_client import CUSTOMER_AGENT_URL, CustomerAgentError, ask_legal_question
from common.workflow_viz import WORKFLOW_STEPS, render_workflow

EXAMPLE_QUESTIONS = [
    "If a company breaks a contract and avoids taxes, what are the legal consequences?",
    "Công ty vi phạm hợp đồng lao động bằng cách sa thải nhân viên không có lý do chính đáng thì phải chịu trách nhiệm pháp lý gì?",
    "A tech company shared user data without consent (GDPR violation). What are the privacy consequences?",
]

STEP_INTERVAL_S = 2.0


def _with_assistant(history: list, content: str) -> list:
    """Append or replace the latest assistant message (Gradio 6 messages format)."""
    history = list(history)
    if history and history[-1].get("role") == "assistant":
        history[-1] = {"role": "assistant", "content": content}
    else:
        history.append({"role": "assistant", "content": content})
    return history


async def process_question(message: str, history: list):
    """Stream chat + workflow animation while agents process the question."""
    message = (message or "").strip()
    history = history or []

    if not message:
        yield history, render_workflow("idle"), ""
        return

    history = history + [{"role": "user", "content": message}]
    yield history, render_workflow("customer"), ""

    task = asyncio.create_task(ask_legal_question(message))

    for step in WORKFLOW_STEPS:
        if task.done():
            break
        yield _with_assistant(history, "⏳ Agents are working…"), render_workflow(step), ""
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=STEP_INTERVAL_S)
            break
        except asyncio.TimeoutError:
            continue

    while not task.done():
        yield _with_assistant(history, "⏳ Tax & Compliance agents running in parallel…"), render_workflow("parallel"), ""
        await asyncio.sleep(0.4)

    try:
        text, elapsed = task.result()
        reply = f"{text}\n\n---\n⏱️ Latency: {elapsed:.2f}s (Customer → Law → Tax/Compliance)"
        yield _with_assistant(history, reply), render_workflow("complete"), ""
    except CustomerAgentError as exc:
        yield _with_assistant(
            history,
            f"**Could not reach the agent system**\n\n{exc}\n\n"
            "Start backend services first: `./start_all.sh`",
        ), render_workflow("error"), ""
    except Exception as exc:
        yield _with_assistant(history, f"**Unexpected error:** {exc}"), render_workflow("error"), ""


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Legal Multi-Agent Assistant") as demo:
        gr.Markdown(
            f"""
# Legal Multi-Agent Assistant
Ask a legal question — watch the **agent workflow** animate as your request flows through the A2A pipeline.

**Backend:** `{CUSTOMER_AGENT_URL}` — run `./start_all.sh` before using this UI.

*Educational legal analysis only — not legal advice.*
"""
        )

        workflow_html = gr.HTML(value=render_workflow("idle"), label="Agent workflow")

        chatbot = gr.Chatbot(height=420)

        with gr.Row():
            msg = gr.Textbox(
                placeholder="Ask a legal question…",
                label="Your question",
                scale=5,
                lines=2,
            )
            send = gr.Button("Send", variant="primary", scale=1)

        gr.Examples(
            examples=EXAMPLE_QUESTIONS,
            inputs=msg,
            label="Example questions",
        )

        outputs = [chatbot, workflow_html, msg]
        send.click(process_question, [msg, chatbot], outputs)
        msg.submit(process_question, [msg, chatbot], outputs)

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        css=".gradio-container { max-width: 1100px !important; }",
    )
